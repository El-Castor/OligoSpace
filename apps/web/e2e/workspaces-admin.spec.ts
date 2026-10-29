import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

test("project workspace, membership, administration, and member denial work", async ({ page }) => {
  await loginAs(page);
  const suffix = Date.now().toString(36);
  const projectName = `E2E project ${suffix}`;

  await page.goto("/projects/new");
  await page.locator('input[name="name"]').fill(projectName);
  await page.locator('select[name="team_id"]').selectOption({ label: "Development laboratory" });
  await page.locator('select[name="visibility"]').selectOption("team");
  await page.locator('textarea[name="description"]').fill(`Persistent project ${suffix}`);
  await page.getByRole("button", { name: "Create project" }).click();
  await expect(page).toHaveURL(/\/projects\/PRJ-[0-9]+/);
  await expect(page.getByRole("status")).toHaveText("Project created in PostgreSQL.");
  const projectUrl = page.url();
  await page.reload();
  await expect(page.getByRole("heading", { level: 1, name: projectName })).toBeVisible();
  await expect(page.getByText(`Persistent project ${suffix}`)).toBeVisible();

  await page.locator('select[name="user_id"]').selectOption({
    label: "Local researcher · researcher@oligospace.local",
  });
  await page.locator('select[name="role"]').selectOption("member");
  await page.getByRole("button", { name: "Add or update" }).click();
  await expect(page.getByRole("status")).toContainText("Project membership");
  await expect(page.getByText("Local researcher", { exact: true })).toBeVisible();

  await page.goto("/team");
  await expect(page.getByRole("heading", { level: 1, name: "Teams" })).toBeVisible();
  await page.getByRole("link", { name: /Development laboratory/ }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Development laboratory" })).toBeVisible();
  await expect(page.getByRole("link", { name: new RegExp(projectName) })).toBeVisible();

  await page.goto("/admin");
  await expect(page.getByRole("heading", { level: 1, name: "Administration" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "Users" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Create projection" })).toBeVisible();

  await page.getByLabel("Current user").click();
  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login/);
  await loginAs(page, "member");
  await page.goto(projectUrl);
  await expect(page.getByRole("heading", { level: 1, name: projectName })).toBeVisible();
  await expect(page.getByRole("link", { name: "Edit project" })).toHaveCount(0);
  await page.goto("/admin");
  await expect(page.getByRole("heading", { level: 1, name: "Access denied" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Create projection" })).toHaveCount(0);
});
