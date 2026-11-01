import { expect, test } from "@playwright/test";

import { createOligo, createTarget, loginAs, uniqueDna } from "./helpers";

test("Primer3 Oligo QC and Assay pair results persist through Caddy reloads", async ({ page }) => {
  await loginAs(page);
  const run = Date.now();
  const suffix = run.toString(36);
  const forwardName = `Primer3 forward ${suffix}`;
  const reverseName = `Primer3 reverse ${suffix}`;
  const forwardId = await createOligo(page, forwardName, uniqueDna(run, "ACG"));

  await expect(page.getByText("Wallace screening Tm", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
  await expect(page).toHaveURL(new RegExp(`/oligos/${forwardId}\\?scientific_job=SJOB-`));
  const oligoJob = page.locator(".scientific-job").first();
  await expect(oligoJob.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible({ timeout: 90_000 });
  await expect(oligoJob.getByText("Primer3 nearest-neighbor Tm", { exact: true })).toBeVisible();
  await expect(oligoJob.getByText("Hairpin", { exact: true })).toBeVisible();
  await expect(oligoJob.getByText("Homodimer", { exact: true })).toBeVisible();
  await page.reload();
  await expect(oligoJob.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible();

  const reverseId = await createOligo(page, reverseName, uniqueDna(run + 1, "TGC"));
  const targetName = `Primer3 target ${suffix}`;
  const targetId = await createTarget(page, targetName, `P3-${suffix}`);
  await page.goto("/assays/new");
  await page.locator('input[name="name"]').fill(`Primer3 assay ${suffix}`);
  await page.locator('select[name="experiment_type_id"]').selectOption({ label: "PCR" });
  await page.locator('select[name="target_id"]').selectOption({ label: `${targetId} · ${targetName}` });
  await page.locator('select[name="oligo_id"]').nth(0).selectOption({ label: `${forwardId} · ${forwardName}` });
  await page.locator('select[name="role"]').nth(0).selectOption("forward_primer");
  await page.locator('select[name="oligo_id"]').nth(1).selectOption({ label: `${reverseId} · ${reverseName}` });
  await page.locator('select[name="role"]').nth(1).selectOption("reverse_primer");
  await page.getByRole("button", { name: "Register assay" }).click();
  await expect(page).toHaveURL(/\/assays\/ASY-[0-9]+/);
  await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
  await expect(page).toHaveURL(/\/assays\/ASY-[0-9]+\?scientific_job=SJOB-/);
  const pairJob = page.locator(".scientific-job").first();
  await expect(pairJob.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible({ timeout: 90_000 });
  await expect(pairJob.getByText("Absolute Tm delta", { exact: true })).toBeVisible();
  await expect(pairJob.getByText("Heterodimer", { exact: true })).toBeVisible();
  await expect(pairJob.getByText("3′ end complementarity", { exact: true })).toBeVisible();
  await page.reload();
  await expect(pairJob.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible();
});

test("viewer can read institute results but cannot submit or discover private jobs", async ({ page }) => {
  await loginAs(page);
  const run = Date.now();
  const sharedId = await createOligo(
    page,
    `Shared Primer3 ${run.toString(36)}`,
    uniqueDna(run, "GCA"),
    "organization",
  );
  await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
  const sharedJob = page.locator(".scientific-job").first();
  await expect(sharedJob.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible({ timeout: 90_000 });
  const sharedJobHref = await sharedJob.getByRole("link").getAttribute("href");

  const privateId = await createOligo(
    page,
    `Private Primer3 ${run.toString(36)}`,
    uniqueDna(run + 1, "CGT"),
  );
  await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
  const privateJob = page.locator(".scientific-job").first();
  await expect(privateJob.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible({ timeout: 90_000 });
  const privateJobHref = await privateJob.getByRole("link").getAttribute("href");

  await page.context().clearCookies();
  await loginAs(page, "viewer");
  await page.goto(`/oligos/${sharedId}`);
  await expect(page.locator(".scientific-job").first().getByRole("status", { name: "Execution state: succeeded" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Run Primer3 analysis" })).toHaveCount(0);
  await page.goto(sharedJobHref ?? "/");
  await expect(page.getByText("Persisted scientific request, execution state, result and reproducibility provenance.")).toBeVisible();

  const response = await page.goto(privateJobHref ?? `/oligos/${privateId}`);
  expect(response?.status()).toBe(404);
});

test("Primer3 rejects ambiguous DNA without creating a scientific result", async ({ page }) => {
  await loginAs(page);
  const run = Date.now();
  const ambiguousSequence = `${uniqueDna(run, "ATG").slice(0, -4)}NNNNGCTA`;
  const publicId = await createOligo(
    page,
    `Ambiguous Primer3 ${run.toString(36)}`,
    ambiguousSequence,
  );

  await page.getByRole("button", { name: "Run Primer3 analysis" }).click();
  await expect(page).toHaveURL(new RegExp(`/oligos/${publicId}\\?scientific_error=`));
  await expect(page.locator(".notice[role='alert']")).toContainText(
    "Primer3 analysis requires unambiguous DNA (A/C/G/T).",
  );
  await expect(page.locator(".scientific-job")).toHaveCount(0);
});
