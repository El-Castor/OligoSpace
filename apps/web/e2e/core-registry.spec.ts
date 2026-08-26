import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ mode: "serial" });

function uniqueDna(seed: number, prefix: string): string {
  const encoded = seed
    .toString(4)
    .padStart(24, "0")
    .replaceAll("0", "A")
    .replaceAll("1", "C")
    .replaceAll("2", "G")
    .replaceAll("3", "T");
  return `${prefix}${encoded}GCTA`;
}

async function createOligo(page: Page, name: string, sequence: string): Promise<string> {
  await page.goto("/oligos/new");
  await page.locator('input[name="name"]').fill(name);
  await page.locator('textarea[name="sequence"]').fill(sequence);
  await page.getByRole("button", { name: "Register oligo" }).click();
  await expect(page).toHaveURL(/\/oligos\/OLG-[0-9]+/);
  await expect(page.getByRole("heading", { level: 1, name })).toBeVisible();
  return new URL(page.url()).pathname.split("/").at(-1) ?? "";
}

test("core registry works through Caddy and persists after reload", async ({ page }) => {
  const run = Date.now();
  const suffix = run.toString(36);
  const forwardName = `E2E forward ${suffix}`;
  const reverseName = `E2E reverse ${suffix}`;
  const targetName = `E2E target ${suffix}`;
  const assayName = `E2E assay ${suffix}`;

  await page.goto("/");
  await expect(page).toHaveTitle(/OligoSpace/);
  await expect(page.getByRole("heading", { level: 1, name: /Good science starts/ })).toBeVisible();
  await expect(page.getByLabel("Current user")).toHaveText("LA");

  await page.goto("/oligos");
  await expect(page.getByRole("heading", { level: 1, name: "Oligos" })).toBeVisible();

  const forwardId = await createOligo(page, forwardName, uniqueDna(run, "ACG"));
  await expect(page.getByText("Calculation provenance")).toBeVisible();
  await page.getByRole("link", { name: "Edit metadata" }).click();
  await page.locator('textarea[name="notes"]').fill(`Persisted note ${suffix}`);
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByText("Oligo metadata updated and audited.")).toBeVisible();
  await page.reload();
  await expect(page.getByText(`Persisted note ${suffix}`)).toBeVisible();

  const reverseId = await createOligo(page, reverseName, uniqueDna(run + 1, "TGC"));

  await page.goto("/targets/new");
  await page.locator('input[name="name"]').fill(targetName);
  await page.locator('input[name="gene_identifier"]').fill(`GENE-${suffix}`);
  await page.getByRole("button", { name: "Register target" }).click();
  await expect(page).toHaveURL(/\/targets\/TGT-[0-9]+/);
  await expect(page.getByRole("heading", { level: 1, name: targetName })).toBeVisible();
  const targetId = new URL(page.url()).pathname.split("/").at(-1) ?? "";
  await page.getByRole("link", { name: "Edit target" }).click();
  await page.locator('textarea[name="description"]').fill(`Persisted target ${suffix}`);
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByText("Target updated and audited.")).toBeVisible();
  await page.reload();
  await expect(page.getByText(`Persisted target ${suffix}`)).toBeVisible();

  await page.goto("/assays/new");
  await page.locator('input[name="name"]').fill(assayName);
  await page.locator('select[name="experiment_type_id"]').selectOption({ label: "PCR" });
  await page.locator('select[name="target_id"]').selectOption({ label: `${targetId} · ${targetName}` });
  await page.locator('input[name="expected_amplicon_length"]').fill("186");
  await page.locator('select[name="oligo_id"]').nth(0).selectOption({ label: `${forwardId} · ${forwardName}` });
  await page.locator('select[name="role"]').nth(0).selectOption("forward_primer");
  await page.locator('select[name="oligo_id"]').nth(1).selectOption({ label: `${reverseId} · ${reverseName}` });
  await page.locator('select[name="role"]').nth(1).selectOption("reverse_primer");
  await page.getByRole("button", { name: "Register assay" }).click();
  await expect(page).toHaveURL(/\/assays\/ASY-[0-9]+/);
  await expect(page.getByRole("heading", { level: 1, name: assayName })).toBeVisible();
  await expect(page.getByText("forward primer", { exact: true })).toBeVisible();
  await expect(page.getByText("reverse primer", { exact: true })).toBeVisible();
  await expect(page.getByText("186 bp", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Edit assay" }).click();
  await page.locator('textarea[name="protocol_notes"]').fill(`Persisted protocol ${suffix}`);
  await page.getByRole("button", { name: "Save as new version" }).click();
  await expect(page.getByText("Assay saved as version 2; the update was audited.")).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { level: 1, name: assayName })).toBeVisible();
  await expect(page.getByText(`Persisted protocol ${suffix}`)).toBeVisible();

  await page.locator('input[name="q"]').fill(suffix);
  await page.locator('input[name="q"]').press("Enter");
  await expect(page.getByRole("heading", { level: 1, name: `Results for “${suffix}”` })).toBeVisible();
  await expect(page.getByRole("link", { name: new RegExp(assayName) })).toBeVisible();
});
