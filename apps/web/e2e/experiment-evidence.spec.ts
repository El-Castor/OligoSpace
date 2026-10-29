import { expect, test } from "@playwright/test";

import { createOligo, createTarget, loginAs, uniqueDna } from "./helpers";

test("experiment runs, contextual validation, quarantine, supersession, search, and reload persist", async ({ page }) => {
  await loginAs(page);
  const seed = Date.now();
  const suffix = seed.toString(36);
  const assayName = `E2E evidence assay ${suffix}`;
  const forwardName = `E2E evidence forward ${suffix}`;
  const reverseName = `E2E evidence reverse ${suffix}`;
  const targetName = `E2E evidence target ${suffix}`;
  const forwardId = await createOligo(page, forwardName, uniqueDna(seed, "AGC"));
  const reverseId = await createOligo(page, reverseName, uniqueDna(seed + 1, "CTA"));
  const targetId = await createTarget(page, targetName, `EVIDENCE-${suffix}`);

  await page.goto("/assays/new");
  await page.locator('input[name="name"]').fill(assayName);
  await page.locator('select[name="experiment_type_id"]').selectOption({ label: "PCR" });
  await page.locator('select[name="target_id"]').selectOption({ label: `${targetId} · ${targetName}` });
  await page.locator('select[name="oligo_id"]').nth(0).selectOption({ label: `${forwardId} · ${forwardName}` });
  await page.locator('select[name="role"]').nth(0).selectOption("forward_primer");
  await page.locator('select[name="oligo_id"]').nth(1).selectOption({ label: `${reverseId} · ${reverseName}` });
  await page.locator('select[name="role"]').nth(1).selectOption("reverse_primer");
  await page.getByRole("button", { name: "Register assay" }).click();
  await expect(page).toHaveURL(/\/assays\/ASY-[0-9]+/);
  const assayPublicId = new URL(page.url()).pathname.split("/").at(-1) ?? "";

  await page.getByRole("link", { name: "Record run" }).click();
  await page.locator('input[name="performed_at"]').fill("2026-09-02T09:30");
  await page.locator('input[name="protocol_name"]').fill(`Evidence protocol ${suffix}`);
  await page.locator('input[name="protocol_version"]').fill("2.1");
  await page.locator('textarea[name="conditions"]').fill('{"annealing_temperature_c":61.5}');
  await page.locator('textarea[name="input_metadata"]').fill('{"lot_reference":"user-provided-LOT-42"}');
  await page.getByRole("button", { name: "Record experiment run" }).click();
  await expect(page).toHaveURL(/\/experiments\/RUN-[0-9]+/);
  const firstRunUrl = page.url();
  const firstRunId = new URL(firstRunUrl).pathname.split("/").at(-1) ?? "";
  await expect(page.getByText("v1", { exact: true })).toBeVisible();

  await page.locator('input[name="file"]').setInputFiles({
    name: `run-evidence-${suffix}.csv`,
    mimeType: "text/csv",
    buffer: Buffer.from("lane,sample,result\n1,A,weak\n"),
  });
  await page.getByRole("button", { name: "Upload to quarantine" }).click();
  await expect(page.getByRole("status")).toHaveText("Evidence stored privately in quarantine.");
  await expect(page.getByText(`run-evidence-${suffix}.csv`)).toBeVisible();
  await expect(page.getByText("quarantined", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText(`run-evidence-${suffix}.csv`)).toBeVisible();

  await page.getByRole("link", { name: "Add validation" }).click();
  await expect(page.getByText(/Method guidance:.*gel_validation/)).toBeVisible();
  await page.locator('select[name="status"]').selectOption("inconclusive");
  await page.locator('input[name="validated_at"]').fill("2026-09-02T12:00");
  await page.locator('textarea[name="conclusion"]').fill(`Weak evidence ${suffix} requires repetition`);
  await page.locator('textarea[name="measurements"]').fill('{"efficiency":0.72}');
  await page.getByRole("button", { name: "Record validation evidence" }).click();
  await expect(page).toHaveURL(/\/validation\/VAL-[0-9]+/);
  const firstValidationUrl = page.url();
  const firstValidationId = new URL(firstValidationUrl).pathname.split("/").at(-1) ?? "";
  await expect(page.getByText("inconclusive", { exact: true })).toBeVisible();

  await page.getByRole("link", { name: "Supersede with new evidence" }).click();
  await expect(page.getByText(new RegExp(`supersede ${firstValidationId}`))).toBeVisible();
  await page.locator('select[name="status"]').selectOption("passed");
  await page.locator('input[name="validated_at"]').fill("2026-09-02T14:00");
  await page.locator('textarea[name="conclusion"]').fill(`Repeat evidence ${suffix} supports the run`);
  await page.locator('textarea[name="measurements"]').fill('{"efficiency":0.94}');
  await page.getByRole("button", { name: "Record validation evidence" }).click();
  await expect(page.getByText("passed", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { level: 1, name: `Repeat evidence ${suffix} supports the run` })).toBeVisible();

  await page.goto(firstValidationUrl);
  await expect(page.getByText("superseded", { exact: true })).toBeVisible();
  await page.goto(firstRunUrl);
  await expect(page.getByRole("link", { name: new RegExp(`Repeat evidence ${suffix}`) })).toBeVisible();

  await page.goto(`/experiments/new?assay=${assayPublicId}`);
  await page.locator('input[name="performed_at"]').fill("2026-09-02T16:00");
  await page.locator('input[name="protocol_name"]').fill(`Evidence protocol ${suffix}`);
  await page.getByRole("button", { name: "Record experiment run" }).click();
  await expect(page).toHaveURL(/\/experiments\/RUN-[0-9]+/);
  await page.goto(`/assays/${assayPublicId}`);
  await expect(page.getByRole("link", { name: new RegExp(firstRunId) })).toBeVisible();
  await expect(page.locator('a[href^="/experiments/RUN-"]')).toHaveCount(2);

  await page.locator('input[name="q"]').fill(suffix);
  await page.locator('input[name="q"]').press("Enter");
  await expect(page.getByRole("heading", { level: 1, name: `Results for “${suffix}”` })).toBeVisible();
  await expect(page.getByRole("link", { name: new RegExp(`Evidence protocol ${suffix}`) }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: new RegExp(`Repeat evidence ${suffix}`) })).toBeVisible();

  await page.goto("/");
  await expect(page.getByText("Awaiting validation", { exact: true })).toBeVisible();
});
