// Explicit evidence runner (not a default *.spec.ts). Host controls only its
// isolated worker via marker files; no database state/result is fabricated.
import { expect, test } from "@playwright/test";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createOligo, loginAs, uniqueDna } from "./helpers";

test("same persisted workflow jobs before and after presentation", async ({ page }) => {
  test.setTimeout(300_000);
  const root = process.env.UI_EVIDENCE_DIR!;
  const after = process.env.UI_EVIDENCE_STAGE === "after";
  await mkdir(`${root}/control`, { recursive: true });
  const signal = async (name: string) => writeFile(`${root}/control/${name}`, "ready");
  const ack = async (name: string) => expect.poll(async () => readFile(`${root}/control/${name}`, "utf8").catch(() => ""), { timeout: 120_000 }).toBe("ready");
  const first = page.locator(".scientific-job").first();
  const stateLabel = (value: string) => after ? first.getByRole("status", { name: `Execution state: ${value}` }) : first.getByText(value, { exact: true });
  const state = async (value: string) => expect(async () => { await page.reload(); await expect(stateLabel(value)).toBeVisible(); }).toPass({ timeout: 90_000, intervals: [500, 1000] });
  const jobId = () => first.getByRole("link").first().innerText();
  let data: { forward: string; assay: string; success: string; pair: string; failed: string; queued: string; facts: string[] };
  await page.setViewportSize({ width: 1440, height: 1000 });
  await loginAs(page);
  if (!after) {
    const forward = await createOligo(page, "WorkflowSpec long QC", uniqueDna(40_000_001, "CGC") + "ACGT".repeat(7) + "A", "organization");
    await page.getByRole("button", { name: "Run Primer3 analysis", exact: true }).click();
    await state("queued");
    await signal("start-normal");
    await state("succeeded");
    const success = await jobId();
    const facts = await first.locator(".scientific-fact strong").allTextContents();
    const reverse = await createOligo(page, "WorkflowSpec reverse", uniqueDna(40_000_002, "TGC"), "organization");
    await page.goto("/assays/new");
    await page.locator('input[name="name"]').fill("WorkflowSpec pair");
    await page.locator('select[name="experiment_type_id"]').selectOption({ label: "PCR" });
    await page.locator('select[name="visibility"]').selectOption("organization");
    await page.locator('select[name="oligo_id"]').nth(0).selectOption({ label: `${forward} · WorkflowSpec long QC` });
    await page.locator('select[name="role"]').nth(0).selectOption("forward_primer");
    await page.locator('select[name="oligo_id"]').nth(1).selectOption({ label: `${reverse} · WorkflowSpec reverse` });
    await page.locator('select[name="role"]').nth(1).selectOption("reverse_primer");
    await page.getByRole("button", { name: "Register assay", exact: true }).click();
    await expect(page).toHaveURL(/\/assays\/ASY-/);
    const assay = new URL(page.url()).pathname.split("/").at(-1)!;
    await page.getByRole("button", { name: "Run Primer3 analysis", exact: true }).click();
    await state("succeeded");
    const pair = await jobId();
    await page.getByRole("link", { name: "Edit assay", exact: true }).click();
    await expect(page.locator('textarea[name="protocol_notes"]')).toBeVisible();
    await page.locator('textarea[name="protocol_notes"]').fill("User-provided protocol revision for stale-version display.");
    await page.getByRole("button", { name: "Save as new version", exact: true }).click();
    await expect(page.getByRole("status")).toContainText("version 2");
    await signal("start-timeout"); await ack("timeout-ready");
    await page.goto(`/oligos/${forward}`);
    await page.locator('input[name="mv_conc_mM"]').fill("51");
    await page.getByRole("button", { name: "Run Primer3 analysis", exact: true }).click();
    await state("failed");
    const failed = await jobId();
    await expect(first.locator('.notice[role="alert"]')).toContainText("tool_timeout");
    await signal("stop-worker"); await ack("worker-stopped");
    await page.locator('input[name="mv_conc_mM"]').fill("52");
    await page.getByRole("button", { name: "Run Primer3 analysis", exact: true }).click();
    await state("queued");
    data = { forward, assay, success, pair, failed, queued: await jobId(), facts };
    await writeFile(`${root}/manifest.json`, JSON.stringify(data, null, 2));
  } else data = JSON.parse(await readFile(`${root}/manifest.json`, "utf8"));
  await mkdir(`${root}/${after ? "after" : "before"}`, { recursive: true });
  const capture = async (name: string) => {
    await expect(page.getByText("Loading records", { exact: true })).toHaveCount(0);
    await page.evaluate(() => { (document.activeElement as HTMLElement)?.blur(); scrollTo(0, 0); });
    await page.screenshot({ path: `${root}/${after ? "after" : "before"}/${name}.png`, fullPage: true });
  };
  await page.goto(`/oligos/${data.forward}`); await expect(stateLabel("queued")).toBeVisible(); await capture("parameters-history");
  for (const [id, name, expected] of [[data.queued, "queued", "queued"], [data.success, "result-long-sequence", "succeeded"], [data.failed, "failed", "failed"], [data.pair, "pair-result", "succeeded"]]) {
    await page.goto(`/scientific-jobs/${id}`);
    await expect(stateLabel(expected)).toBeVisible();
    if (id === data.success) expect(await first.locator(".scientific-fact strong").allTextContents()).toEqual(data.facts);
    await capture(name);
  }
  await page.goto(`/assays/${data.assay}`); await expect(page.getByText(/This result belongs to Assay version 1/)).toBeVisible(); await capture("stale-version");
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto(`/scientific-jobs/${data.success}`);
    await expect(stateLabel("succeeded")).toBeVisible();
    if (after) expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    if ([390, 768].includes(width)) await capture(`result-${width}`);
  }
});
