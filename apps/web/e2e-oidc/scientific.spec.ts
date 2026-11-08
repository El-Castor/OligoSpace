import { readFileSync } from "node:fs";
import { devices, expect, test, type Browser, type Page } from "@playwright/test";

import {
  api,
  controlWorker,
  openSession,
  origin,
  recordEvidence,
  uniqueDna,
  userLabel,
  type Persona,
  type Session,
} from "./support";

// MVP-02 scientific acceptance. Every journey is driven through the real UI/API of the
// disposable stack; setup that is not the subject of a test uses the same server API.
const run = Date.now();
const suffix = run.toString(36);

const PRIMER3_SOURCE_SHA256 = "805cef7ef39607cd40f0f5bb8b32e35e20007153a0a55131dd430ce644c8fb9e";
const GOLDEN = {
  forward: "ATGCGTACGTTAGCGTACGA",
  reverse: "TCGTACGCTAACGTACGCAT",
  // docs/PRIMER3_QUALIFICATION.md (Primer3 2.6.1; 50 mM, 1.5 mM, 0.6 mM, 50 nM, loop 30).
  facts: {
    forward_nearest_neighbor_tm: 59.62663,
    forward_hairpin: 69.836183,
    forward_homodimer: 46.16876,
    reverse_nearest_neighbor_tm: 59.62663,
    reverse_hairpin: 69.091431,
    reverse_homodimer: 34.346077,
    tm_delta: 0.0,
    heterodimer: 59.555182,
    end_complementarity: 59.555182,
  },
} as const;
const TOLERANCE_C = 1e-6;
const DEFAULT_PARAMETERS = {
  mv_conc_mM: 50,
  dv_conc_mM: 1.5,
  dntp_conc_mM: 0.6,
  dna_conc_nM: 50,
  max_loop: 30,
  max_nn_length: 60,
  tm_method: "santalucia_1998",
  salt_correction_method: "santalucia_1998",
};

interface Fact { state: string; value: number; units: string }
interface Job {
  id: string;
  public_id: string;
  state: string;
  requester_id: string;
  attempt_count: number;
  assay_version: number | null;
  effective_parameters: Record<string, number | string>;
  input_snapshot: Record<string, unknown>;
  attempts: Array<{ state: string }>;
  result: {
    tool_version: string;
    tool_source_sha256: string;
    algorithm: string;
    warnings: unknown[];
    payload: Record<string, unknown>;
  } | null;
}
interface OligoRecord {
  id: string;
  public_id: string;
  name: string;
  normalized_sequence: string;
  reverse_complement: string;
  sequence_length: number;
  gc_percent: number | null;
  melting_temperature_c: number | null;
  molecular_weight_g_mol: number | null;
  status: string;
  created_at: string;
  calculation_provenance: Record<string, string | null>;
}

interface Workspace {
  teamName: string;
  teamId: string;
  projectName: string;
  projectId: string;
  projectUuid: string;
}
let workspace: Workspace;
let denials = 0;

function projectOption() {
  return `${workspace.projectId} · ${workspace.projectName}`;
}

async function withSession<T>(
  browser: Browser,
  persona: Persona,
  work: (session: Session) => Promise<T>,
  options: Parameters<typeof openSession>[2] = {},
): Promise<T> {
  const session = await openSession(browser, persona, options);
  try {
    return await work(session);
  } finally {
    await session.context.close();
  }
}

async function json<T>(response: Awaited<ReturnType<typeof api>>, status = 200): Promise<T> {
  expect(response.status()).toBe(status);
  return (await response.json()) as T;
}

function denied(status: number, expected: number[]) {
  expect(expected).toContain(status);
  denials += 1;
}

const record = (page: Page, label: string) =>
  page
    .locator(".record-field")
    .filter({ has: page.locator("dt").filter({ hasText: new RegExp(`^${label}$`) }) })
    .locator("dd");

async function addMember(page: Page, persona: Persona, role: string, kind: "Team" | "Project") {
  await page.locator('select[name="user_id"]').selectOption({ label: userLabel(persona) });
  await page.locator('select[name="role"]').selectOption(role);
  await page.getByRole("button", { name: "Add or update" }).click();
  await expect(page.getByRole("status")).toContainText(`${kind} membership`);
}

async function registerOligo(
  page: Page,
  options: { name: string; sequence: string; visibility?: "project" | "private" | "organization" },
): Promise<string> {
  const visibility = options.visibility ?? "project";
  await page.goto("/oligos/new");
  await page.locator('input[name="name"]').fill(options.name);
  await page.locator('textarea[name="sequence"]').fill(options.sequence);
  await page.locator('select[name="visibility"]').selectOption(visibility);
  if (visibility === "project") {
    await page.locator('select[name="owner_project_id"]').selectOption({ label: projectOption() });
  }
  await page.getByRole("button", { name: "Register oligo" }).click();
  await expect(page).toHaveURL(/\/oligos\/OLG-[0-9]+/);
  await expect(page.getByRole("heading", { level: 1, name: options.name })).toBeVisible();
  return new URL(page.url()).pathname.split("/").at(-1) ?? "";
}

async function registerAssay(
  page: Page,
  options: { name: string; associations: Array<{ oligo: string; role: string }>; target?: string },
): Promise<string> {
  await page.goto("/assays/new");
  await page.locator('input[name="name"]').fill(options.name);
  await page.locator('select[name="experiment_type_id"]').selectOption({ label: "PCR" });
  if (options.target) await page.locator('select[name="target_id"]').selectOption({ label: options.target });
  for (const [index, association] of options.associations.entries()) {
    await page.locator('select[name="oligo_id"]').nth(index).selectOption({ label: association.oligo });
    await page.locator('select[name="role"]').nth(index).selectOption(association.role);
  }
  await page.locator('select[name="visibility"]').selectOption("project");
  await page.locator('select[name="owner_project_id"]').selectOption({ label: projectOption() });
  await page.getByRole("button", { name: "Register assay" }).click();
  await expect(page).toHaveURL(/\/assays\/ASY-[0-9]+/);
  await expect(page.getByRole("heading", { level: 1, name: options.name })).toBeVisible();
  return new URL(page.url()).pathname.split("/").at(-1) ?? "";
}

async function apiOligo(
  session: Session,
  name: string,
  sequence: string,
  visibility: "project" | "private" | "organization" = "project",
): Promise<OligoRecord> {
  const body: Record<string, unknown> = { name, sequence, visibility };
  if (visibility === "project") body.owner_project_id = workspace.projectUuid;
  const created = await json<{ oligo: OligoRecord }>(await api(session, "/registry/oligos", "POST", body), 201);
  return created.oligo;
}

async function waitForJob(session: Session, publicId: string): Promise<Job> {
  let job: Job | undefined;
  await expect
    .poll(
      async () => {
        job = await json<Job>(await api(session, `/scientific-jobs/${publicId}`));
        return job.state;
      },
      { timeout: 120_000, intervals: [500, 1000, 2000] },
    )
    .toMatch(/^(succeeded|failed)$/);
  return job!;
}

function jobFact(job: Job, ...path: string[]): Fact {
  let cursor: unknown = job.result!.payload;
  for (const key of path) cursor = (cursor as Record<string, unknown>)[key];
  return cursor as Fact;
}

function independentMetrics(sequence: string) {
  const count = (bases: string) => [...sequence].filter((base) => bases.includes(base)).length;
  const mass: Record<string, number> = { A: 313.21, C: 289.18, G: 329.21, T: 304.2 };
  const weight = [...sequence].reduce((sum, base) => sum + mass[base], 0) - 61.96;
  return {
    length: sequence.length,
    gc: (100 * count("GC")) / sequence.length,
    wallaceTm: 2 * count("AT") + 4 * count("GC"),
    weight,
    reverseComplement: [...sequence]
      .reverse()
      .map((base) => ({ A: "T", C: "G", G: "C", T: "A" })[base])
      .join(""),
  };
}

function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let quoted = false;
  for (let index = 0; index < text.length; index++) {
    const character = text[index];
    if (quoted) {
      if (character === '"') {
        if (text[index + 1] === '"') {
          cell += '"';
          index++;
        } else quoted = false;
      } else cell += character;
    } else if (character === '"') quoted = true;
    else if (character === ",") {
      row.push(cell);
      cell = "";
    } else if (character === "\n") {
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
    } else if (character !== "\r") cell += character;
  }
  return rows;
}

const CSV_COLUMNS = [
  "public_id", "name", "normalized_sequence", "oligo_type", "status", "sequence_length", "gc_percent",
  "melting_temperature_c", "molecular_weight_g_mol", "normalization", "gc_method", "tm_method",
  "molecular_weight_method", "calculated_at", "created_at", "updated_at",
];

async function csvRows(session: Session, query: string): Promise<string[][]> {
  const response = await session.context.request.get(`${origin}/oligos/export?q=${encodeURIComponent(query)}`);
  expect(response.status()).toBe(200);
  const text = (await response.body()).toString("utf8");
  expect(text.charCodeAt(0)).toBe(0xfeff);
  const rows = parseCsv(text.slice(1));
  expect(rows[0]).toEqual(CSV_COLUMNS);
  return rows.slice(1);
}

test.beforeAll(async ({ browser, request }) => {
  test.setTimeout(240_000);
  await expect.poll(async () => {
    try {
      const health = await request.get(`${origin}/api/v1/health/live`);
      const discovery = await request.get(`${origin}/realms/qualification/.well-known/openid-configuration`);
      const login = await request.get(`${origin}/login`);
      return health.status() === 200 && discovery.status() === 200 && login.status() === 200;
    } catch { return false; }
  }, { timeout: 180_000, intervals: [1000, 2000, 5000] }).toBe(true);
  workspace = await withSession(browser, "labadmin", async (admin) => {
    const { page } = admin;
    const teamName = `MVP02 team ${suffix}`;
    const projectName = `MVP02 project ${suffix}`;
    await page.goto("/admin");
    const teamForm = page.locator("#teams form.inline-admin-form");
    await teamForm.locator('input[name="name"]').fill(teamName);
    await teamForm.getByRole("button", { name: "Create team" }).click();
    await expect(page).toHaveURL(/\/team\/[0-9a-f-]{36}\?created=1/);
    const teamId = new URL(page.url()).pathname.split("/").at(-1) ?? "";
    for (const [persona, role] of [["scientist", "member"], ["reader", "viewer"], ["trainee", "member"]] as const) {
      await addMember(page, persona, role, "Team");
    }
    const projectId = await withSession(browser, "scientist", async ({ page: creator }) => {
      await creator.goto("/projects/new");
      await creator.locator('input[name="name"]').fill(projectName);
      await creator.locator('select[name="team_id"]').selectOption({ label: teamName });
      await creator.locator('select[name="visibility"]').selectOption("project");
      await creator.locator('textarea[name="description"]').fill("Synthetic MVP-02 scientific acceptance project.");
      await creator.getByRole("button", { name: "Create project" }).click();
      await expect(creator).toHaveURL(/\/projects\/PRJ-[0-9]+/);
      return new URL(creator.url()).pathname.split("/").at(-1) ?? "";
    });
    await page.goto(`/projects/${projectId}`);
    for (const [persona, role] of [["scientist", "member"], ["reader", "viewer"], ["trainee", "member"]] as const) {
      await addMember(page, persona, role, "Project");
    }
    const detail = await json<{ id: string }>(await api(admin, `/workspace/projects/${projectId}`));
    return { teamName, teamId, projectName, projectId, projectUuid: detail.id };
  });
});

test("scientist registers targets, oligos and assays in an authorized project, then searches, filters and reuses them", async ({ browser }) => {
  test.setTimeout(300_000);
  await withSession(browser, "scientist", async (session) => {
    const { page } = session;

    // Authorized organization, team and project.
    const me = await json<{ role: string; organization_name: string; development_identity: boolean }>(await api(session, "/me"));
    expect(me.role).toBe("member");
    expect(me.development_identity).toBe(false);
    await page.goto("/team");
    await expect(page.getByRole("heading", { level: 1, name: "Teams" })).toBeVisible();
    await page.getByRole("link", { name: new RegExp(workspace.teamName) }).click();
    await expect(page.getByRole("heading", { level: 1, name: workspace.teamName })).toBeVisible();
    await page.getByRole("link", { name: new RegExp(workspace.projectName) }).click();
    await expect(page).toHaveURL(new RegExp(`/projects/${workspace.projectId}$`));
    await expect(page.getByRole("heading", { level: 1, name: workspace.projectName })).toBeVisible();

    // Target creation and modification keep the stable public ID.
    const targetName = `MVP02 target ${suffix}`;
    const gene = `MVP02-${suffix}`;
    await page.goto("/targets/new");
    await page.locator('input[name="name"]').fill(targetName);
    await page.locator('input[name="gene_identifier"]').fill(gene);
    await page.locator('input[name="transcript_identifier"]').fill(`${gene}.1`);
    await page.locator('select[name="visibility"]').selectOption("project");
    await page.locator('select[name="owner_project_id"]').selectOption({ label: projectOption() });
    await page.getByRole("button", { name: "Register target" }).click();
    await expect(page).toHaveURL(/\/targets\/TGT-[0-9]+/);
    const targetId = new URL(page.url()).pathname.split("/").at(-1) ?? "";
    await expect(page.getByRole("heading", { level: 1, name: targetName })).toBeVisible();
    await expect(page.locator("body")).toContainText(gene);
    const revisedTarget = `${targetName} revised`;
    await page.getByRole("link", { name: "Edit target" }).click();
    await page.locator('input[name="name"]').fill(revisedTarget);
    await page.locator('textarea[name="description"]').fill(`Persisted target note ${suffix}`);
    await page.getByRole("button", { name: "Save changes" }).click();
    await expect(page.getByRole("status")).toHaveText("Target updated and audited.");
    await page.reload();
    await expect(page).toHaveURL(new RegExp(`/targets/${targetId}`));
    await expect(page.getByRole("heading", { level: 1, name: revisedTarget })).toBeVisible();
    await expect(page.getByText(`Persisted target note ${suffix}`)).toBeVisible();
    await page.goto(`/targets?q=${encodeURIComponent(gene)}`);
    await expect(page.getByRole("link", { name: revisedTarget })).toBeVisible();
    await page.goto(`/targets?q=${encodeURIComponent(`absent-${suffix}`)}`);
    await expect(page.getByRole("link", { name: revisedTarget })).toHaveCount(0);

    // Oligo registration: identity, computed facts, provenance and normalization.
    const sequenceA = uniqueDna(run, "ACG");
    const nameA = `MVP02 oligo A ${suffix}`;
    const oligoA = await registerOligo(page, { name: nameA, sequence: sequenceA });
    const apiA = await json<OligoRecord>(await api(session, `/registry/oligos/${oligoA}`));
    const expected = independentMetrics(sequenceA);
    expect(apiA.normalized_sequence).toBe(sequenceA);
    expect(apiA.sequence_length).toBe(expected.length);
    expect(Math.abs(apiA.gc_percent! - expected.gc)).toBeLessThan(0.006);
    expect(apiA.melting_temperature_c).toBe(expected.wallaceTm);
    expect(Math.abs(apiA.molecular_weight_g_mol! - expected.weight)).toBeLessThan(0.006);
    expect(apiA.reverse_complement).toBe(expected.reverseComplement);
    expect(apiA.calculation_provenance.tm_method).toBe("wallace-2at-4gc/v1");
    await expect(record(page, "Public ID")).toHaveText(oligoA);
    await expect(record(page, "Length")).toHaveText(`${expected.length} nt`);
    await expect(record(page, "GC")).toHaveText(`${apiA.gc_percent}%`);
    await expect(record(page, "Wallace screening Tm")).toHaveText(`${apiA.melting_temperature_c} °C`);
    await expect(record(page, "Molecular weight")).toHaveText(`${apiA.molecular_weight_g_mol} g/mol`);
    await expect(record(page, "Status")).toHaveText("active");
    await expect(record(page, "Visibility")).toHaveText("project");
    await expect(record(page, "Sequence 5′→3′")).toHaveText(sequenceA);
    await expect(record(page, "Reverse complement")).toHaveText(expected.reverseComplement);
    await expect(page.locator(".provenance-card pre").first()).toContainText("wallace-2at-4gc/v1");

    // Lower-case, spaced input is normalized to one canonical sequence.
    const sequenceB = uniqueDna(run + 1, "TGC");
    const spaced = sequenceB.toLowerCase().replace(/(.{8})/g, "$1 ");
    const oligoB = await registerOligo(page, { name: `MVP02 oligo B ${suffix}`, sequence: spaced });
    await expect(record(page, "Sequence 5′→3′")).toHaveText(sequenceB);
    expect(oligoB).not.toBe(oligoA);

    // Exact duplicates are refused and point to the reusable record; invalid input is explained.
    await page.goto("/oligos/new");
    await page.locator('input[name="name"]').fill(`MVP02 duplicate ${suffix}`);
    await page.locator('textarea[name="sequence"]').fill(sequenceA);
    await page.locator('select[name="visibility"]').selectOption("private");
    await page.getByRole("button", { name: "Register oligo" }).click();
    await expect(page.getByRole("alert").filter({ hasText: "already exists" })).toBeVisible();
    const duplicate = await api(session, "/registry/oligos", "POST", { name: "dup", sequence: sequenceA, visibility: "private" });
    expect(duplicate.status()).toBe(409);
    expect((await duplicate.json()).detail.existing_public_id).toBe(oligoA);
    await page.goto("/oligos/new");
    await page.locator('input[name="name"]').fill(`MVP02 invalid ${suffix}`);
    await page.locator('textarea[name="sequence"]').fill("INVALID!");
    await page.locator('select[name="visibility"]').selectOption("private");
    await page.getByRole("button", { name: "Register oligo" }).click();
    await expect(page.locator('.notice[role="alert"], .form-error[role="alert"]').first()).toBeVisible();
    await expect(page).toHaveURL(/\/oligos\/new/);

    // The reverse complement of an existing visible oligo is registered with a warning.
    const oligoC = await registerOligo(page, { name: `MVP02 oligo C ${suffix}`, sequence: expected.reverseComplement });
    await page.goto("/oligos/new");
    await page.locator('input[name="name"]').fill(`MVP02 oligo D ${suffix}`);
    await page.locator('textarea[name="sequence"]').fill(independentMetrics(sequenceB).reverseComplement);
    await page.locator('select[name="visibility"]').selectOption("private");
    await page.getByRole("button", { name: "Register oligo" }).click();
    await expect(page).toHaveURL(/\/oligos\/OLG-[0-9]+\?warning=reverse-complement/);
    await expect(page.getByText("A reverse-complement match already exists. Review both records before reuse.")).toBeVisible();

    // Sequence is immutable; metadata edits persist.
    await page.goto(`/oligos/${oligoA}`);
    await page.getByRole("link", { name: "Edit metadata" }).click();
    await expect(page.locator('textarea[name="sequence"]')).toHaveAttribute("readonly", "");
    await page.locator('textarea[name="notes"]').fill(`Persisted oligo note ${suffix}`);
    await page.getByRole("button", { name: "Save changes" }).click();
    await expect(page.getByRole("status")).toHaveText("Oligo metadata updated and audited.");
    await page.reload();
    await expect(page.getByText(`Persisted oligo note ${suffix}`)).toBeVisible();
    denied((await api(session, `/registry/oligos/${oligoA}`, "PATCH", { sequence: "AAAAAAAAAA" })).status(), [400, 422]);

    // Assay association rules.
    const forwardOption = `${oligoA} · ${nameA}`;
    const reverseOption = `${oligoC} · MVP02 oligo C ${suffix}`;
    await page.goto("/assays/new");
    await page.locator('input[name="name"]').fill(`MVP02 rejected role ${suffix}`);
    await page.locator('select[name="experiment_type_id"]').selectOption({ label: "PCR" });
    await page.locator('select[name="oligo_id"]').nth(0).selectOption({ label: forwardOption });
    await page.locator('select[name="role"]').nth(0).selectOption("probe");
    await page.getByRole("button", { name: "Register assay" }).click();
    await expect(page.locator('.form-error[role="alert"]')).toBeVisible();
    await expect(page).toHaveURL(/\/assays\/new/);
    await page.locator('select[name="role"]').nth(0).selectOption("forward_primer");
    await page.locator('select[name="oligo_id"]').nth(1).selectOption({ label: forwardOption });
    await page.locator('select[name="role"]').nth(1).selectOption("forward_primer");
    await page.getByRole("button", { name: "Register assay" }).click();
    await expect(page.locator('.form-error[role="alert"]')).toBeVisible();
    await expect(page).toHaveURL(/\/assays\/new/);

    const assayName = `MVP02 assay ${suffix}`;
    const assayId = await registerAssay(page, {
      name: assayName,
      target: `${targetId} · ${revisedTarget}`,
      associations: [
        { oligo: forwardOption, role: "forward_primer" },
        { oligo: reverseOption, role: "reverse_primer" },
      ],
    });
    await expect(page.getByText("forward primer", { exact: true })).toBeVisible();
    await expect(page.getByText("reverse primer", { exact: true })).toBeVisible();
    await page.getByRole("link", { name: "Edit assay" }).click();
    await page.locator('input[name="expected_amplicon_length"]').fill("186");
    await page.locator('textarea[name="protocol_notes"]').fill(`Persisted protocol ${suffix}`);
    await page.getByRole("button", { name: "Save as new version" }).click();
    await expect(page.getByRole("status")).toHaveText("Assay saved as version 2; the update was audited.");
    await page.reload();
    await expect(page.getByText("186 bp", { exact: true })).toBeVisible();
    await expect(page.getByText(`Persisted protocol ${suffix}`)).toBeVisible();

    // Reuse: the same registered oligos serve a second assay without a duplicate record.
    const reuseId = await registerAssay(page, {
      name: `MVP02 reuse assay ${suffix}`,
      associations: [
        { oligo: forwardOption, role: "forward_primer" },
        { oligo: reverseOption, role: "reverse_primer" },
      ],
    });
    expect(reuseId).not.toBe(assayId);
    const reused = await json<{ items: Array<{ public_id: string }>; total: number }>(
      await api(session, `/registry/oligos?q=${sequenceA}`),
    );
    expect(reused.items.map((item) => item.public_id)).toEqual([oligoA]);

    // Search, filter and consult.
    await page.goto(`/oligos?q=${sequenceA}`);
    await expect(page.getByRole("link", { name: oligoA, exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: oligoB, exact: true })).toHaveCount(0);
    await page.goto(`/oligos?q=${encodeURIComponent(nameA)}`);
    await expect(page.getByRole("link", { name: oligoA, exact: true })).toBeVisible();
    await page.goto(`/assays?q=${encodeURIComponent(`MVP02 reuse assay ${suffix}`)}`);
    await expect(page.getByRole("link", { name: new RegExp(`MVP02 reuse assay ${suffix}`) }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: assayName, exact: true })).toHaveCount(0);
    await page.goto(`/search?q=${suffix}`);
    for (const name of [revisedTarget, nameA, assayName]) {
      await expect(page.getByRole("link", { name: new RegExp(name) }).first()).toBeVisible();
    }
    await page.goto(`/projects/${workspace.projectId}`);
    await expect(page.getByRole("link", { name: new RegExp(nameA) })).toBeVisible();
    await expect(page.getByRole("link", { name: new RegExp(assayName) })).toBeVisible();

    // History: the dashboard lists the scientist's audited work.
    await page.goto("/");
    await expect(page.getByText("create · oligo", { exact: false }).first()).toBeVisible();
    await expect(page.getByText("My recent activity")).toBeVisible();
  });
});

test("validated Primer3 reference values are reproduced, persisted with provenance and reloaded", async ({ browser }) => {
  test.setTimeout(360_000);
  const forwardName = `MVP02 reference forward ${suffix}`;
  const reverseName = `MVP02 reference reverse ${suffix}`;
  const observed: Record<string, number> = {};
  let pairJobId = "";
  let oligoJobId = "";
  let forwardId = "";
  await withSession(browser, "scientist", async (session) => {
    const { page } = session;
    forwardId = await registerOligo(page, { name: forwardName, sequence: GOLDEN.forward });
    const reverseId = await registerOligo(page, { name: reverseName, sequence: GOLDEN.reverse });
    await expect(page).toHaveURL(/warning=reverse-complement/);
    const assayId = await registerAssay(page, {
      name: `MVP02 reference assay ${suffix}`,
      associations: [
        { oligo: `${forwardId} · ${forwardName}`, role: "forward_primer" },
        { oligo: `${reverseId} · ${reverseName}`, role: "reverse_primer" },
      ],
    });
    const me = await json<{ id: string }>(await api(session, "/me"));

    // Single-oligo QC through the real worker.
    await page.goto(`/oligos/${forwardId}`);
    await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
    await expect(page).toHaveURL(new RegExp(`/oligos/${forwardId}\\?scientific_job=SJOB-`));
    oligoJobId = new URL(page.url()).searchParams.get("scientific_job")!;
    const oligoCard = page.locator(".scientific-job").first();
    await expect(oligoCard.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible({ timeout: 120_000 });
    const oligoJob = await waitForJob(session, oligoJobId);
    expect(oligoJob.state).toBe("succeeded");
    expect(oligoJob.requester_id).toBe(me.id);
    expect(oligoJob.effective_parameters).toEqual(DEFAULT_PARAMETERS);
    expect(oligoJob.result!.tool_version).toBe("2.6.1");
    expect(oligoJob.result!.tool_source_sha256).toBe(PRIMER3_SOURCE_SHA256);
    expect(oligoJob.result!.warnings).toEqual([]);
    expect((oligoJob.input_snapshot.sequence as { normalized: string }).normalized).toBe(GOLDEN.forward);
    expect(oligoJob.attempts.map((attempt) => attempt.state)).toEqual(["succeeded"]);
    expect(Math.abs(jobFact(oligoJob, "nearest_neighbor_tm").value - GOLDEN.facts.forward_nearest_neighbor_tm)).toBeLessThanOrEqual(TOLERANCE_C);
    expect(Math.abs(jobFact(oligoJob, "hairpin").value - GOLDEN.facts.forward_hairpin)).toBeLessThanOrEqual(TOLERANCE_C);
    expect(Math.abs(jobFact(oligoJob, "homodimer").value - GOLDEN.facts.forward_homodimer)).toBeLessThanOrEqual(TOLERANCE_C);
    await expect(oligoCard.locator(".scientific-fact").filter({ hasText: "Primer3 nearest-neighbor Tm" }).locator("strong")).toHaveText(
      `${GOLDEN.facts.forward_nearest_neighbor_tm.toFixed(2)} °C`,
    );

    // Pair analysis on the assay: forward, reverse and pair facts match the validated fixture.
    await page.goto(`/assays/${assayId}`);
    await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
    await expect(page).toHaveURL(new RegExp(`/assays/${assayId}\\?scientific_job=SJOB-`));
    pairJobId = new URL(page.url()).searchParams.get("scientific_job")!;
    const pairCard = page.locator(".scientific-job").first();
    await expect(pairCard.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible({ timeout: 120_000 });
    const pair = await waitForJob(session, pairJobId);
    expect(pair.state).toBe("succeeded");
    expect(pair.assay_version).toBe(1);
    expect(pair.effective_parameters).toEqual(DEFAULT_PARAMETERS);
    expect(pair.result!.tool_version).toBe("2.6.1");
    expect(pair.result!.tool_source_sha256).toBe(PRIMER3_SOURCE_SHA256);
    const facts: Array<[keyof typeof GOLDEN.facts, string[]]> = [
      ["forward_nearest_neighbor_tm", ["forward", "nearest_neighbor_tm"]],
      ["forward_hairpin", ["forward", "hairpin"]],
      ["forward_homodimer", ["forward", "homodimer"]],
      ["reverse_nearest_neighbor_tm", ["reverse", "nearest_neighbor_tm"]],
      ["reverse_hairpin", ["reverse", "hairpin"]],
      ["reverse_homodimer", ["reverse", "homodimer"]],
      ["tm_delta", ["tm_delta"]],
      ["heterodimer", ["heterodimer"]],
      ["end_complementarity", ["end_complementarity"]],
    ];
    for (const [name, path] of facts) {
      const fact = jobFact(pair, ...path);
      expect(fact.state).toBe("available");
      expect(fact.units).toBe("degC");
      observed[name] = fact.value;
      expect(Math.abs(fact.value - GOLDEN.facts[name])).toBeLessThanOrEqual(TOLERANCE_C);
    }
    const sections = pairCard.locator(".scientific-results");
    await expect(sections.nth(0).locator(".scientific-fact").filter({ hasText: "Hairpin" }).locator("strong")).toHaveText(
      `${GOLDEN.facts.forward_hairpin.toFixed(2)} °C`,
    );
    await expect(sections.nth(1).locator(".scientific-fact").filter({ hasText: "Hairpin" }).locator("strong")).toHaveText(
      `${GOLDEN.facts.reverse_hairpin.toFixed(2)} °C`,
    );
    await expect(sections.nth(2).locator(".scientific-fact").filter({ hasText: "Heterodimer" }).locator("strong")).toHaveText(
      `${GOLDEN.facts.heterodimer.toFixed(2)} °C`,
    );

    // Controlled parameters are recorded with the result and change the calculation; an
    // inconsistent set is refused without a job.
    await page.goto(`/oligos/${forwardId}`);
    await page.locator('input[name="mv_conc_mM"]').fill("75");
    await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
    await expect(page).toHaveURL(/scientific_job=SJOB-/);
    const salted = await waitForJob(session, new URL(page.url()).searchParams.get("scientific_job")!);
    expect(salted.effective_parameters.mv_conc_mM).toBe(75);
    expect(salted.state).toBe("succeeded");
    expect(jobFact(salted, "nearest_neighbor_tm").value).not.toBe(GOLDEN.facts.forward_nearest_neighbor_tm);
    await expect(page.getByText('"mv_conc_mM": 75', { exact: false }).first()).toBeAttached();
    const oligoUuid = (await json<OligoRecord>(await api(session, `/registry/oligos/${forwardId}`))).id;
    const jobsBefore = await json<{ total: number }>(await api(session, `/scientific-jobs?oligo_id=${oligoUuid}`));
    await page.locator('input[name="dv_conc_mM"]').fill("0.5");
    await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
    await expect(page.locator('.notice[role="alert"]')).toBeVisible();
    const jobsAfter = await json<{ total: number }>(await api(session, `/scientific-jobs?oligo_id=${oligoUuid}`));
    expect(jobsAfter.total).toBe(jobsBefore.total);
  });

  // A fresh login (new browser context) reads the same persisted results and provenance.
  await withSession(browser, "scientist", async (session) => {
    const { page } = session;
    await page.goto(`/scientific-jobs/${pairJobId}`);
    await expect(page.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible();
    await expect(page.getByText("Absolute Tm delta", { exact: true })).toBeVisible();
    await page.getByText("Parameters and provenance", { exact: true }).click();
    const provenance = JSON.parse(await page.locator("details").filter({ has: page.getByText("Parameters and provenance", { exact: true }) }).locator("pre").innerText());
    expect(provenance.parameters).toEqual(DEFAULT_PARAMETERS);
    expect(provenance.input_snapshot.forward.normalized_sequence).toBe(GOLDEN.forward);
    expect(provenance.input_snapshot.reverse.normalized_sequence).toBe(GOLDEN.reverse);
    expect(provenance.result.tool_version).toBe("2.6.1");
    expect(provenance.result.tool_source_sha256).toBe(PRIMER3_SOURCE_SHA256);
    expect(provenance.attempts).toHaveLength(1);
    await page.reload();
    await expect(page.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible();
    const again = await json<Job>(await api(session, `/scientific-jobs/${oligoJobId}`));
    expect(again.state).toBe("succeeded");
    expect(Math.abs(jobFact(again, "homodimer").value - GOLDEN.facts.forward_homodimer)).toBeLessThanOrEqual(TOLERANCE_C);
  });

  const deltas = Object.entries(GOLDEN.facts).map(([name, expectedValue]) => ({
    fact: name,
    expected: expectedValue,
    observed: observed[name],
    abs_delta: Math.abs(observed[name] - expectedValue),
  }));
  recordEvidence("reference", {
    tool_version: "2.6.1",
    tool_source_sha256_match: true,
    facts: deltas,
    max_abs_delta: Math.max(...deltas.map((item) => item.abs_delta)),
  });
});

test("asynchronous jobs survive a stopped worker and repeated submissions create one job", async ({ browser }) => {
  test.setTimeout(420_000);
  let requests = 0;
  let serverErrors = 0;
  let queuedWhileStopped = false;
  const distinct = new Set<string>();
  await withSession(browser, "scientist", async (session) => {
    const { page } = session;
    const sequence = uniqueDna(run + 7, "CTA");
    const oligoId = await registerOligo(page, { name: `MVP02 async oligo ${suffix}`, sequence });
    const oligoUuid = (await json<OligoRecord>(await api(session, `/registry/oligos/${oligoId}`))).id;
    try {
      await controlWorker("stop");
      await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
      await expect(page).toHaveURL(/scientific_job=SJOB-/);
      const jobId = new URL(page.url()).searchParams.get("scientific_job")!;
      requests += 1;
      distinct.add(jobId);
      await expect(page.locator(".scientific-job").first().getByRole("status", { name: "Execution state: queued" })).toBeVisible();
      await expect(page.getByText("Queued by the server. No result is confirmed yet.")).toBeVisible();
      await page.reload();
      await expect(page.locator(".scientific-job").first().getByRole("status", { name: "Execution state: queued" })).toBeVisible();
      queuedWhileStopped = true;

      // The web form sends a new idempotency key per click: sequential and concurrent repeats
      // of the same request must be recognised as the one active job, never a server error.
      const submit = (key: string) => api(session, "/scientific-jobs/oligo-primer3-qc", "POST", { oligo_public_id: oligoId }, { "Idempotency-Key": key });
      const sequential = [await submit(`repeat-${suffix}-1`), await submit(`repeat-${suffix}-2`)];
      const concurrent = await Promise.all([submit(`repeat-${suffix}-3`), submit(`repeat-${suffix}-4`), submit(`repeat-${suffix}-5`)]);
      for (const response of [...sequential, ...concurrent]) {
        requests += 1;
        if (response.status() >= 500) serverErrors += 1;
        expect(response.status()).toBe(200);
        distinct.add(((await response.json()) as Job).public_id);
      }
      expect(serverErrors).toBe(0);
      expect(distinct).toEqual(new Set([jobId]));
      const queued = await json<{ total: number; items: Job[] }>(await api(session, `/scientific-jobs?oligo_id=${oligoUuid}`));
      expect(queued.total).toBe(1);
      expect(queued.items[0].state).toBe("queued");
      expect(queued.items[0].attempt_count).toBe(0);

      // Restart the worker: the already persisted job completes once, without a second job.
      await controlWorker("start");
      await expect(async () => {
        await page.reload();
        await expect(page.locator(".scientific-job").first().getByRole("status", { name: "Execution state: succeeded" })).toBeVisible();
      }).toPass({ timeout: 150_000, intervals: [1000, 2000, 3000] });
      const finished = await json<{ total: number; items: Job[] }>(await api(session, `/scientific-jobs?oligo_id=${oligoUuid}`));
      expect(finished.total).toBe(1);
      expect(finished.items[0].attempts).toHaveLength(1);
      expect(finished.items[0].attempts[0].state).toBe("succeeded");
    } finally {
      await controlWorker("start");
    }
  });
  recordEvidence("repeated_submissions", {
    requests,
    distinct_jobs: distinct.size,
    server_errors: serverErrors,
    queued_while_worker_stopped: queuedWhileStopped,
    completed_after_restart: true,
  });
});

test("administrator, scientist, reader and another organization keep consistent rights through permission removal", async ({ browser }) => {
  test.setTimeout(420_000);
  let revokedEffective = false;
  let demotionEffective = false;
  let crossOrganizationChecks = 0;
  const projectOligoName = `MVP02 rights project ${suffix}`;
  const privateName = `MVP02 rights private ${suffix}`;
  let projectOligo!: OligoRecord;
  let privateOligo!: OligoRecord;
  let jobId = "";
  await withSession(browser, "scientist", async (scientist) => {
    projectOligo = await apiOligo(scientist, projectOligoName, uniqueDna(run + 11, "GAT"));
    privateOligo = await apiOligo(scientist, privateName, uniqueDna(run + 12, "GAT"), "private");
    const submitted = await json<Job>(
      await api(scientist, "/scientific-jobs/oligo-primer3-qc", "POST", { oligo_public_id: projectOligo.public_id }),
      202,
    );
    jobId = submitted.public_id;
    expect((await waitForJob(scientist, jobId)).state).toBe("succeeded");
  });

  await withSession(browser, "reader", async (reader) => {
    const { page } = reader;
    await page.goto(`/oligos/${projectOligo.public_id}`);
    await expect(page.getByRole("heading", { level: 1, name: projectOligoName })).toBeVisible();
    await expect(page.locator(".scientific-job").first().getByRole("status", { name: "Execution state: succeeded" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Run Primer3 analysis" })).toHaveCount(0);
    await page.goto("/oligos/new");
    await expect(page.getByText("Read-only access", { exact: true })).toBeVisible();
    await expect(page.locator('.record-form button[type="submit"]')).toHaveCount(0);
    const hidden = await page.goto(`/oligos/${privateOligo.public_id}`);
    expect(hidden?.status()).toBe(404);
    await page.goto(`/search?q=${suffix}`);
    await expect(page.getByRole("link", { name: new RegExp(projectOligoName) }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: new RegExp(privateName) })).toHaveCount(0);
    // Direct API: reads succeed; every write and job submission is refused server-side.
    expect((await api(reader, `/registry/oligos/${projectOligo.public_id}`)).status()).toBe(200);
    expect((await api(reader, `/scientific-jobs/${jobId}`)).status()).toBe(200);
    denied((await api(reader, "/registry/oligos", "POST", { name: "reader write", sequence: uniqueDna(run + 13, "ACA"), visibility: "private" })).status(), [403]);
    denied((await api(reader, `/registry/oligos/${projectOligo.public_id}`, "PATCH", { name: "reader edit" })).status(), [403]);
    denied((await api(reader, "/scientific-jobs/oligo-primer3-qc", "POST", { oligo_public_id: projectOligo.public_id })).status(), [403]);
    denied((await api(reader, `/scientific-jobs/${jobId}/retry`, "POST")).status(), [403]);
    denied((await api(reader, `/registry/oligos/${privateOligo.public_id}`)).status(), [404]);
  });

  {
    await withSession(browser, "rival", async (rival) => {
      const { page } = rival;
      for (const path of [`/oligos/${projectOligo.public_id}`, `/oligos/${privateOligo.public_id}`, `/scientific-jobs/${jobId}`]) {
        expect((await page.goto(path))?.status()).toBe(404);
        crossOrganizationChecks += 1;
      }
      await page.goto(`/search?q=${suffix}`);
      await expect(page.getByRole("link", { name: new RegExp(`MVP02 .* ${suffix}`) })).toHaveCount(0);
      for (const path of [`/registry/oligos/${projectOligo.public_id}`, `/scientific-jobs/${jobId}`]) {
        denied((await api(rival, path)).status(), [404]);
        crossOrganizationChecks += 1;
      }
      const listed = await json<{ total: number }>(await api(rival, `/registry/oligos?q=${suffix}`));
      expect(listed.total).toBe(0);
      const jobs = await json<{ items: unknown[] }>(await api(rival, "/scientific-jobs"));
      expect(jobs.items).toEqual([]);
      crossOrganizationChecks += 2;
      denied((await api(rival, "/scientific-jobs/oligo-primer3-qc", "POST", { oligo_public_id: projectOligo.public_id })).status(), [404]);
      crossOrganizationChecks += 1;
      // Duplicate detection is scoped to the institute: the same sequence is allowed in another one.
      const own = await api(rival, "/registry/oligos", "POST", { name: `Rival copy ${suffix}`, sequence: projectOligo.normalized_sequence, visibility: "private" });
      expect(own.status()).toBe(201);
      crossOrganizationChecks += 1;
    });
  }

  // Administrator removes the reader from the project through the UI; the same session loses access.
  await withSession(browser, "labadmin", async (admin) => {
    const adminJob = await api(admin, `/scientific-jobs/${jobId}`);
    expect(adminJob.status()).toBe(200);
    await withSession(browser, "reader", async (reader) => {
      const row = () => admin.page.locator(".member-row").filter({ hasText: userLabel("reader").split(" · ")[1] });
      await admin.page.goto(`/projects/${workspace.projectId}`);
      admin.page.once("dialog", (dialog) => dialog.accept());
      await row().getByRole("button", { name: "Remove" }).click();
      await expect(row()).toHaveCount(0);
      denied((await api(reader, `/registry/oligos/${projectOligo.public_id}`)).status(), [404]);
      denied((await api(reader, `/scientific-jobs/${jobId}`)).status(), [404]);
      const search = await json<{ total: number }>(await api(reader, `/registry/oligos?q=${suffix}`));
      expect(search.total).toBe(0);
      expect((await reader.page.goto(`/oligos/${projectOligo.public_id}`))?.status()).toBe(404);
      expect((await csvRows(reader, suffix)).length).toBe(0);
      revokedEffective = true;
      // Granting the role again restores read access to the same token.
      await admin.page.goto(`/projects/${workspace.projectId}`);
      await addMember(admin.page, "reader", "viewer", "Project");
      expect((await api(reader, `/registry/oligos/${projectOligo.public_id}`)).status()).toBe(200);
    });

    {
      await withSession(browser, "trainee", async (trainee) => {
        const first = await api(trainee, "/registry/oligos", "POST", { name: `Trainee write ${suffix}`, sequence: uniqueDna(run + 14, "TAC"), visibility: "private" });
        expect(first.status()).toBe(201);
        const users = await json<Array<{ id: string; email: string }>>(await api(admin, "/workspace/admin/users"));
        const target = users.find((user) => user.email === "trainee@qualification.invalid");
        expect(target).toBeDefined();
        await json(await api(admin, `/workspace/admin/users/${target!.id}`, "PATCH", { global_role: "viewer" }));
        denied((await api(trainee, "/registry/oligos", "POST", { name: `Trainee blocked ${suffix}`, sequence: uniqueDna(run + 15, "TAC"), visibility: "private" })).status(), [403]);
        denied((await api(trainee, "/scientific-jobs/oligo-primer3-qc", "POST", { oligo_public_id: projectOligo.public_id })).status(), [403]);
        demotionEffective = true;
      });
    }
  });

  recordEvidence("permissions", {
    denials_verified: denials,
    cross_organization_checks: crossOrganizationChecks,
    revoked_access_effective: revokedEffective,
    demotion_effective: demotionEffective,
  });
});

test("failure states explain what happened and create no scientific result", async ({ browser }) => {
  test.setTimeout(300_000);
  await withSession(browser, "scientist", async (session) => {
    const { page } = session;
    const jobCount = async (oligoId: string) => {
      const uuid = (await json<OligoRecord>(await api(session, `/registry/oligos/${oligoId}`))).id;
      return (await json<{ total: number }>(await api(session, `/scientific-jobs?oligo_id=${uuid}`))).total;
    };

    // Ambiguous bases are accepted as identity but calculated values are unavailable, not invented.
    const ambiguousId = await registerOligo(page, { name: `MVP02 ambiguous ${suffix}`, sequence: "ACGTNACGTNACGTNACGTACGTACGTAAA" });
    await expect(record(page, "GC")).toHaveText("—");
    await expect(record(page, "Wallace screening Tm")).toHaveText("—");
    await expect(record(page, "Molecular weight")).toHaveText("—");
    await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
    await expect(page).toHaveURL(new RegExp(`/oligos/${ambiguousId}\\?scientific_error=`));
    await expect(page.locator('.notice[role="alert"]')).toContainText("Primer3 analysis requires unambiguous DNA (A/C/G/T).");
    await expect(page.locator(".scientific-job")).toHaveCount(0);
    expect(await jobCount(ambiguousId)).toBe(0);
    await page.reload();
    await expect(page.locator(".scientific-job")).toHaveCount(0);

    // A sequence longer than the qualified nearest-neighbor limit is refused with the limit.
    const longId = await registerOligo(page, { name: `MVP02 long ${suffix}`, sequence: uniqueDna(run + 21, "GGT") + "ACGT".repeat(8) });
    await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
    await expect(page.locator('.notice[role="alert"]')).toContainText("Nearest-neighbor analysis is qualified for at most 60 nt.");
    expect(await jobCount(longId)).toBe(0);

    // Inconsistent parameters never reach the worker.
    const validId = await registerOligo(page, { name: `MVP02 parameters ${suffix}`, sequence: uniqueDna(run + 22, "AGC") });
    await page.locator('input[name="dv_conc_mM"]').fill("0.5");
    await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
    await expect(page.locator('.notice[role="alert"]')).toBeVisible();
    expect(await jobCount(validId)).toBe(0);

    // A pair analysis needs both roles; an assay without a reverse primer cannot be submitted.
    const forwardOnly = await registerAssay(page, {
      name: `MVP02 forward only ${suffix}`,
      associations: [{ oligo: `${validId} · MVP02 parameters ${suffix}`, role: "forward_primer" }],
    });
    expect(await page.locator('select[name="reverse_oligo_id"]').evaluate((element: HTMLSelectElement) => element.validity.valueMissing)).toBe(true);
    const refused = await api(session, "/scientific-jobs/assay-primer3-pair", "POST", { assay_public_id: forwardOnly });
    expect(refused.status()).toBe(422);
    expect((await refused.json()).detail.code).toBe("ambiguous_reverse_role");

    // Inject a failing executable in the disposable worker, with parameters unchanged.
    // A real claimed job must fail, explain the error and persist no result.
    try {
      await controlWorker("fault");
      await page.goto(`/oligos/${validId}`);
      await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
      await expect(page).toHaveURL(/scientific_job=SJOB-/);
      const failedId = new URL(page.url()).searchParams.get("scientific_job")!;
      const failed = await waitForJob(session, failedId);
      expect(failed.state).toBe("failed");
      expect(failed.result).toBeNull();
      expect(failed.attempts.map((attempt) => attempt.state)).toEqual(["failed"]);
      await page.goto(`/scientific-jobs/${failedId}`);
      await expect(page.getByRole("status", { name: "Execution state: failed" })).toBeVisible();
      await expect(page.getByText("Primer3 rejected the qualified input.", { exact: false }).first()).toBeVisible();
      await page.reload();
      await expect(page.getByRole("status", { name: "Execution state: failed" })).toBeVisible();
      expect((await json<Job>(await api(session, `/scientific-jobs/${failedId}`))).result).toBeNull();
      recordEvidence("worker_failure", { terminal_state: "failed", result_absent: true, persisted_after_reload: true });
    } finally {
      await controlWorker("repair");
    }

    // Unknown or unreachable records are a clear 404, not a partial page.
    expect((await page.goto("/oligos/OLG-999999"))?.status()).toBe(404);
    expect((await page.goto("/scientific-jobs/SJOB-999999"))?.status()).toBe(404);
    expect((await api(session, "/scientific-jobs/SJOB-999999")).status()).toBe(404);
  });
});

test("CSV export is faithful, formula-safe and limited to the permitted records", async ({ browser }) => {
  test.setTimeout(300_000);
  const marker = `CSV${suffix}`;
  const names = {
    accent: `${marker} Échantillon, "Bd21" é`,
    formula: `=${marker} formula`,
    privateName: `${marker} private`,
  };
  let rowsChecked = 0;
  let mismatches = 0;
  let outsiderRows = 0;
  let leaked = 0;
  const created: OligoRecord[] = [];
  await withSession(browser, "scientist", async (session) => {
    const { page } = session;
    created.push(await apiOligo(session, names.accent, uniqueDna(run + 31, "ACG")));
    created.push(await apiOligo(session, names.formula, uniqueDna(run + 32, "TGC")));
    created.push(await apiOligo(session, names.privateName, uniqueDna(run + 33, "CAT"), "private"));

    // The visible download is the file under test.
    await page.goto(`/oligos?q=${encodeURIComponent(marker)}`);
    const pending = page.waitForEvent("download");
    await page.getByRole("link", { name: "Export visible oligos (CSV)" }).click();
    const download = await pending;
    expect(download.suggestedFilename()).toBe("oligos.csv");
    expect(await download.failure()).toBeNull();
    const text = readFileSync((await download.path())!, "utf8");
    expect(text.charCodeAt(0)).toBe(0xfeff);
    const rows = parseCsv(text.slice(1));
    expect(rows[0]).toEqual(CSV_COLUMNS);
    const body = rows.slice(1);
    expect(body).toHaveLength(3);

    for (const row of body) {
      const cells = Object.fromEntries(CSV_COLUMNS.map((column, index) => [column, row[index]]));
      const source = created.find((item) => item.public_id === cells.public_id);
      expect(source).toBeDefined();
      const truth = await json<OligoRecord>(await api(session, `/registry/oligos/${source!.public_id}`));
      const expectedName = truth.name.startsWith("=") ? `'${truth.name}` : truth.name;
      const comparisons: Array<[string, string, string | number | null]> = [
        ["name", cells.name, expectedName],
        ["normalized_sequence", cells.normalized_sequence, truth.normalized_sequence],
        ["sequence_length", cells.sequence_length, truth.sequence_length],
        ["gc_percent", cells.gc_percent, truth.gc_percent],
        ["melting_temperature_c", cells.melting_temperature_c, truth.melting_temperature_c],
        ["molecular_weight_g_mol", cells.molecular_weight_g_mol, truth.molecular_weight_g_mol],
        ["status", cells.status, truth.status],
        ["tm_method", cells.tm_method, truth.calculation_provenance.tm_method],
      ];
      for (const [, actual, wanted] of comparisons) {
        const matches = typeof wanted === "number" ? Number(actual) === wanted : actual === wanted;
        if (!matches) mismatches += 1;
      }
      expect(Date.parse(cells.created_at)).toBe(Date.parse(truth.created_at));
      rowsChecked += 1;
    }
    expect(mismatches).toBe(0);
    const formulaRow = body.find((row) => row[1].includes("formula"))!;
    expect(formulaRow[1].startsWith("'=")).toBe(true);
    // Search narrows the export; an empty search result is a header-only file, not an error.
    expect(await csvRows(session, `${marker} Échantillon`)).toHaveLength(1);
    expect(await csvRows(session, `absent-${suffix}`)).toHaveLength(0);
    // The audited export shows in the actor's own activity.
    await page.goto("/");
    await expect(page.getByText("export · oligo export", { exact: false }).first()).toBeVisible();
  });

  await withSession(browser, "reader", async (reader) => {
    const rows = await csvRows(reader, marker);
    expect(rows.map((row) => row[1]).sort()).toEqual([names.accent, `'${names.formula}`].sort());
    leaked += rows.filter((row) => row[1].includes("private")).length;
    expect(leaked).toBe(0);
  });

  {
    await withSession(browser, "rival", async (rival) => {
      outsiderRows = (await csvRows(rival, marker)).length;
      expect(outsiderRows).toBe(0);
    });
  }

  recordEvidence("csv", {
    rows_checked: rowsChecked,
    mismatched_fields: mismatches,
    formula_cells_neutralized: true,
    excluded_records_present: leaked,
    outsider_rows: outsiderRows,
  });
});

test("desktop and mobile layouts keep the scientific workflow usable", async ({ browser }) => {
  test.setTimeout(420_000);
  let overflowPages = 0;
  let mobilePages = 0;
  let desktopPages = 0;
  let oligoId = "";
  let jobId = "";
  let assayId = "";
  await withSession(browser, "scientist", async (session) => {
    const { page } = session;
    oligoId = await registerOligo(page, { name: `MVP02 layout oligo ${suffix}`, sequence: uniqueDna(run + 41, "CCA") });
    const partner = await apiOligo(session, `MVP02 layout partner ${suffix}`, uniqueDna(run + 42, "GGA"));
    assayId = await registerAssay(page, {
      name: `MVP02 layout assay ${suffix}`,
      associations: [
        { oligo: `${oligoId} · MVP02 layout oligo ${suffix}`, role: "forward_primer" },
        { oligo: `${partner.public_id} · ${partner.name}`, role: "reverse_primer" },
      ],
    });
    const submitted = await json<Job>(await api(session, "/scientific-jobs/oligo-primer3-qc", "POST", { oligo_public_id: oligoId }), 202);
    jobId = submitted.public_id;
    expect((await waitForJob(session, jobId)).state).toBe("succeeded");
  });

  const pages = () => ["/", "/oligos", "/oligos/new", `/oligos/${oligoId}`, `/assays/${assayId}`, `/scientific-jobs/${jobId}`, `/search?q=${suffix}`];
  const noOverflow = async (page: Page) => {
    const fits = await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
    if (!fits) overflowPages += 1;
    return fits;
  };

  // Mobile: touch device emulation, collapsed navigation, forms, errors and results.
  await withSession(browser, "scientist", async (mobile) => {
    const { page } = mobile;
    for (const path of pages()) {
      await page.goto(path);
      await expect(page.locator("main, [role='main']").first()).toBeVisible();
      expect(await noOverflow(page)).toBe(true);
      mobilePages += 1;
    }
    await page.goto("/");
    const nav = page.getByRole("navigation", { name: "Primary navigation" });
    await expect(nav).toBeHidden();
    await page.getByRole("button", { name: "Open navigation" }).click();
    await expect(nav).toBeVisible();
    await nav.getByRole("link", { name: "Oligos", exact: true }).click();
    await expect(page).toHaveURL(/\/oligos$/);
    await page.goto("/oligos/new");
    await page.getByRole("button", { name: "Register oligo" }).click();
    await expect(page.locator('input[name="name"]')).toBeFocused();
    expect(await page.locator('input[name="name"]').evaluate((element: HTMLInputElement) => element.validity.valueMissing)).toBe(true);
    await page.locator('input[name="name"]').fill(`MVP02 layout invalid ${suffix}`);
    await page.locator('textarea[name="sequence"]').fill("NOT DNA!");
    await page.getByRole("button", { name: "Register oligo" }).click();
    await expect(page.locator('.notice[role="alert"], .form-error[role="alert"]').first()).toBeVisible();
    expect(await noOverflow(page)).toBe(true);
    await page.goto(`/scientific-jobs/${jobId}`);
    await expect(page.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible();
    await expect(page.locator(".scientific-fact").first()).toBeVisible();
    await expect(page.locator(".job-sequence").first()).toBeVisible();
    await page.screenshot({ path: `${process.env.EVIDENCE_DIR ?? "/evidence"}/synthetic-scientific-mobile.png`, fullPage: true });
  }, { ...devices["Pixel 7"] });

  // Desktop widths: no horizontal overflow and a readable result page.
  await withSession(browser, "scientist", async (desktop) => {
    const { page } = desktop;
    for (const width of [1440, 1024, 768]) {
      await page.setViewportSize({ width, height: 1000 });
      for (const path of pages()) {
        await page.goto(path);
        expect(await noOverflow(page)).toBe(true);
        desktopPages += 1;
      }
    }
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(`/scientific-jobs/${jobId}`);
    await expect(page.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible();
    await page.screenshot({ path: `${process.env.EVIDENCE_DIR ?? "/evidence"}/synthetic-scientific-desktop.png`, fullPage: true });
  });

  recordEvidence("viewport", {
    mobile_pages_checked: mobilePages,
    desktop_pages_checked: desktopPages,
    horizontal_overflow_pages: overflowPages,
  });
});
