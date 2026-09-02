import { expect, test } from "@playwright/test";

import { createTarget, loginAs } from "./helpers";

test("target creation, detail, metadata edit, and reload persistence work", async ({ page }) => {
  await loginAs(page);
  const suffix = Date.now().toString(36);
  const name = `E2E target ${suffix}`;
  await createTarget(page, name, `GENE-${suffix}`);
  await page.getByRole("link", { name: "Edit target" }).click();
  await page.locator('textarea[name="description"]').fill(`Persisted target note ${suffix}`);
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByRole("status")).toHaveText("Target updated and audited.");
  await page.reload();
  await expect(page.getByText(`Persisted target note ${suffix}`)).toBeVisible();
});
