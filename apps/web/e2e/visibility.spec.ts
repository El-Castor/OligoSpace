import { expect, test } from "@playwright/test";

import { loginAs, uniqueDna } from "./helpers";

test("project membership limits search, details and assay choices across projects", async ({ page }) => {
  await loginAs(page);
  const run = Date.now();
  const suffix = `visibility-${run.toString(36)}`;
  const projects: string[] = [];
  for (const [index, label] of ["shared", "unrelated"].entries()) {
    await page.goto("/projects/new");
    await page.locator('input[name="name"]').fill(`${suffix}-${label}`);
    await page.locator('select[name="visibility"]').selectOption("private");
    await page.getByRole("button", { name: "Create project" }).click();
    await expect(page).toHaveURL(/\/projects\/PRJ-[0-9]+/);
    projects.push(new URL(page.url()).pathname.split("/").at(-1) ?? "");
    if (index === 0) {
      await page.locator('select[name="user_id"]').selectOption({
        label: "Local researcher · researcher@oligospace.local",
      });
      await page.locator('select[name="role"]').selectOption("member");
      await page.getByRole("button", { name: "Add or update" }).click();
      await expect(page.getByRole("status")).toContainText("Project membership");
    }
  }

  const records: { id: string; name: string; visible: boolean }[] = [];
  for (const [index, scope] of ["shared", "unrelated", "private", "organization"].entries()) {
    const name = `${suffix}-oligo-${scope}`;
    await page.goto("/oligos/new");
    await page.locator('input[name="name"]').fill(name);
    await page.locator('textarea[name="sequence"]').fill(uniqueDna(run + index, "CAT"));
    await page.locator('select[name="visibility"]').selectOption(index < 2 ? "project" : scope);
    if (index < 2) {
      await page.locator('select[name="owner_project_id"]').selectOption({
        label: `${projects[index]} · ${suffix}-${scope}`,
      });
    }
    await page.getByRole("button", { name: "Register oligo" }).click();
    await expect(page).toHaveURL(/\/oligos\/OLG-[0-9]+/);
    await expect(page.getByRole("heading", { level: 1, name })).toBeVisible();
    records.push({
      id: new URL(page.url()).pathname.split("/").at(-1) ?? "",
      name,
      visible: scope === "shared" || scope === "organization",
    });
  }

  await page.getByLabel("Current user").click();
  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login/);
  await loginAs(page, "member");
  await page.goto(`/search?q=${suffix}-oligo`);
  await expect(page.getByText("2 visible records across the implemented registry, evidence, and projects.")).toBeVisible();
  for (const record of records) {
    await expect(page.getByRole("link", { name: new RegExp(record.name) })).toHaveCount(record.visible ? 1 : 0);
  }
  await page.reload();
  await expect(page.getByText("2 visible records across the implemented registry, evidence, and projects.")).toBeVisible();

  await page.goto("/assays/new");
  const choices = page.locator('select[name="oligo_id"]').first().locator("option");
  for (const record of records) {
    await expect(choices.filter({ hasText: record.name })).toHaveCount(record.visible ? 1 : 0);
  }
  for (const record of records) {
    await page.goto(`/oligos/${record.id}`);
    if (record.visible) {
      await expect(page.getByRole("heading", { level: 1, name: record.name })).toBeVisible();
      await page.getByRole("link", { name: "Edit metadata" }).click();
      await page.locator('input[name="name"]').fill(`${record.name}-forbidden`);
      await page.getByRole("button", { name: "Save changes" }).click();
      await expect(page.getByRole("alert").filter({ hasText: "This role cannot edit this resource." })).toBeVisible();
      await page.goto(`/oligos/${record.id}`);
      await expect(page.getByRole("heading", { level: 1, name: record.name })).toBeVisible();
    } else {
      await expect(page.getByRole("heading", { name: "404", exact: true })).toBeVisible();
      await expect(page.getByRole("heading", { level: 1, name: record.name })).toHaveCount(0);
      await expect(page.getByText(record.id, { exact: true })).toHaveCount(0);
    }
  }
});
