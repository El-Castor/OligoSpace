import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

test("application root opens through Caddy and renders the personalized dashboard", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/OligoSpace/);
  await expect(page).toHaveURL(/\/login/);

  await loginAs(page);
  await expect(page.getByLabel("Current user")).toHaveText("LA");
  await expect(page.getByText("My oligos", { exact: true })).toBeVisible();
  await expect(page.getByText("My recent activity", { exact: true })).toBeVisible();
});
