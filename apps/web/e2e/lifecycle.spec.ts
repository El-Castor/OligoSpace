import { expect, test } from "@playwright/test";

import { createOligo, createTarget, loginAs, uniqueDna } from "./helpers";

for (const entity of ["oligo", "target", "assay", "project"] as const) {
  test(`${entity} deprecation and archive preserve identity, search and reload`, async ({ page }) => {
    await loginAs(page);
    const run = Date.now();
    const name = `Lifecycle ${entity} ${run.toString(36)}`;
    let id: string;
    let root: string;
    let edit: string;
    let save: string;
    if (entity === "oligo") {
      id = await createOligo(page, name, uniqueDna(run, "GAT"));
      root = "/oligos"; edit = "Edit metadata"; save = "Save changes";
    } else if (entity === "target") {
      id = await createTarget(page, name, `GENE-${run}`);
      root = "/targets"; edit = "Edit target"; save = "Save changes";
    } else if (entity === "project") {
      await page.goto("/projects/new");
      await page.locator('input[name="name"]').fill(name);
      await page.getByRole("button", { name: "Create project" }).click();
      await expect(page).toHaveURL(/\/projects\/PRJ-[0-9]+/);
      id = new URL(page.url()).pathname.split("/").at(-1) ?? "";
      root = "/projects"; edit = "Edit project"; save = "Save project";
    } else {
      const primerName = `${name} primer`;
      const primerId = await createOligo(page, primerName, uniqueDna(run, "TCA"));
      await page.goto("/assays/new");
      await page.locator('input[name="name"]').fill(name);
      await page.locator('select[name="experiment_type_id"]').selectOption({ label: "PCR" });
      await page.locator('select[name="oligo_id"]').first().selectOption({ label: `${primerId} · ${primerName}` });
      await page.locator('select[name="role"]').first().selectOption("forward_primer");
      await page.getByRole("button", { name: "Register assay" }).click();
      await expect(page).toHaveURL(/\/assays\/ASY-[0-9]+/);
      id = new URL(page.url()).pathname.split("/").at(-1) ?? "";
      root = "/assays"; edit = "Edit assay"; save = "Save as new version";
    }
    expect(id).toMatch(/^[A-Z]{3}-[0-9]+$/);
    const path = `${root}/${id}`;
    for (const [index, status] of ["deprecated", "archived"].entries()) {
      await page.getByRole("link", { name: edit, exact: true }).click();
      await expect(page.locator('input[name="public_id"]')).toHaveCount(0);
      await page.locator('select[name="status"]').selectOption(status);
      await page.getByRole("button", { name: save, exact: true }).click();
      await expect(page).toHaveURL(new RegExp(`${path}\\?updated=1$`));
      await page.reload();
      await expect(page.getByRole("heading", { level: 1, name, exact: true })).toBeVisible();
      await expect(page.locator(".record-field").filter({ has: page.locator("dt").filter({ hasText: /^Status$/ }) }).locator("dd")).toHaveText(status);
      await expect(page.getByText(id, { exact: true })).toBeVisible();
      if (entity === "assay") {
        await expect(page.getByText("forward primer", { exact: true })).toBeVisible();
        await expect(page.getByRole("status")).toContainText(`version ${index + 2}`);
      }
      await page.goto(`/search?q=${id}`);
      await expect(page.getByRole("link", { name: new RegExp(`${id}.*${name}`) })).toBeVisible();
      await page.goto(path);
    }
  });
}
