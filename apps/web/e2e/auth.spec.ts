import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

test("development login, profile, logout, and second identity work", async ({ page }) => {
  await loginAs(page);
  await page.getByLabel("Current user").click();
  await expect(page.getByText("admin@oligospace.local", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Profile" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Your profile" })).toBeVisible();

  const suffix = Date.now().toString(36);
  await page.locator('input[name="display_name"]').fill(`Local administrator ${suffix}`);
  await page.getByRole("button", { name: "Save profile" }).click();
  await expect(page.getByRole("status")).toHaveText("Profile updated and audited.");
  await page.reload();
  await expect(page.locator('input[name="display_name"]')).toHaveValue(`Local administrator ${suffix}`);

  await page.getByLabel("Current user").click();
  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login/);

  await loginAs(page, "member");
  await expect(page.getByLabel("Current user")).toHaveText("LR");
});
