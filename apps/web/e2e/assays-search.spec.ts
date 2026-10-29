import { expect, test } from "@playwright/test";

import { createOligo, createTarget, loginAs, uniqueDna } from "./helpers";

test("assay roles, versioned edit, global search, and reload persistence work", async ({ page }) => {
  await loginAs(page);
  const run = Date.now();
  const suffix = run.toString(36);
  const forwardName = `E2E forward ${suffix}`;
  const reverseName = `E2E reverse ${suffix}`;
  const targetName = `E2E assay target ${suffix}`;
  const assayName = `E2E assay ${suffix}`;
  const forwardId = await createOligo(page, forwardName, uniqueDna(run, "ACG"));
  const reverseId = await createOligo(page, reverseName, uniqueDna(run + 1, "TGC"));
  const targetId = await createTarget(page, targetName, `GENE-${suffix}`);

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
  await expect(page.getByRole("status")).toHaveText("Assay saved as version 2; the update was audited.");
  await page.reload();
  await expect(page.getByText(`Persisted protocol ${suffix}`)).toBeVisible();

  await page.locator('input[name="q"]').fill(suffix);
  await page.locator('input[name="q"]').press("Enter");
  await expect(page.getByRole("heading", { level: 1, name: `Results for “${suffix}”` })).toBeVisible();
  await expect(page.getByRole("link", { name: new RegExp(assayName) })).toBeVisible();
});
