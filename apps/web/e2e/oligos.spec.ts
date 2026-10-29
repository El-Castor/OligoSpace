import { expect, test } from "@playwright/test";

import { createOligo, loginAs, uniqueDna } from "./helpers";

test("oligo list, creation, detail, metadata edit, and reload persistence work", async ({ page }) => {
  await loginAs(page);
  await page.goto("/oligos");
  await expect(page.getByRole("heading", { level: 1, name: "Oligos" })).toBeVisible();

  const run = Date.now();
  const suffix = run.toString(36);
  const name = `E2E oligo ${suffix}`;
  await createOligo(page, name, uniqueDna(run, "ACG"));
  await expect(page.getByText("Wallace screening provenance")).toBeVisible();
  await page.getByRole("link", { name: "Edit metadata" }).click();
  await page.locator('textarea[name="notes"]').fill(`Persisted oligo note ${suffix}`);
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByRole("status")).toHaveText("Oligo metadata updated and audited.");
  await page.reload();
  await expect(page.getByText(`Persisted oligo note ${suffix}`)).toBeVisible();
});
