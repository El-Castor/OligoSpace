import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { createOligo, loginAs, uniqueDna } from "./helpers";

test("scientific forms preserve inputs, units, errors, save and cancel", async ({ page }) => {
  test.setTimeout(120_000);
  const before = process.env.UI_EVIDENCE_STAGE === "before";
  const root = process.env.UI_EVIDENCE_DIR;
  const capture = async (name: string) => {
    await expect(page.getByText("Loading records", { exact: true })).toHaveCount(0);
    if (!root) return;
    await mkdir(`${root}/${before ? "before" : "after"}`, { recursive: true });
    await page.evaluate(() => { (document.activeElement as HTMLElement)?.blur(); scrollTo(0, 0); });
    await page.screenshot({ path: `${root}/${before ? "before" : "after"}/${name}.png`, fullPage: true });
  };
  await page.setViewportSize({ width: 1440, height: 1000 });
  await loginAs(page);
  await page.goto("/oligos/new");
  await expect(page.locator('input[name="name"]')).toBeVisible();
  await capture("oligo-new");
  await page.getByRole("button", { name: "Register oligo", exact: true }).click();
  await expect(page.locator('input[name="name"]')).toBeFocused();
  expect(await page.locator('input[name="name"]').evaluate((element: HTMLInputElement) => element.validity.valueMissing)).toBe(true);
  const long = "FormSpec Brachypodium distachyon — user-provided annotation. ".repeat(12);
  await page.locator('input[name="name"]').fill("FormSpec error probe");
  await page.locator('textarea[name="sequence"]').fill("INVALID!");
  await page.locator('textarea[name="description"]').fill(long);
  await page.getByRole("button", { name: "Register oligo", exact: true }).click();
  await expect(page.locator('.notice[role="alert"]')).toBeVisible();
  if (!before) {
    await expect(page.locator('input[name="name"]')).toHaveValue("FormSpec error probe");
    await expect(page.locator('textarea[name="sequence"]')).toHaveValue("INVALID!");
    await expect(page.locator('textarea[name="description"]')).toHaveValue(long);
  } else {
    // Baseline redirects discard inputs. Re-enter the identical original input
    // for comparable error screenshots; after must restore it automatically.
    await page.locator('input[name="name"]').fill("FormSpec error probe");
    await page.locator('textarea[name="sequence"]').fill("INVALID!");
    await page.locator('textarea[name="description"]').fill(long);
  }
  await capture("oligo-error-long");
  if (!before) {
    await page.reload();
    await expect(page.locator('input[name="name"]')).toHaveValue("");
    await expect(page.locator('textarea[name="sequence"]')).toHaveValue("");
  }
  await page.getByRole("link", { name: "Cancel", exact: true }).click();
  await expect(page).toHaveURL(/\/oligos$/);
  await page.goto("/oligos/new");
  await expect(page.locator('input[name="name"]')).toHaveValue("");
  const sequence = uniqueDna(30_000_001, "GTC");
  const id = await createOligo(page, "FormSpec persisted oligo", sequence);
  await page.goto(`/oligos/${id}/edit`);
  await expect(page.locator('textarea[name="sequence"]')).toHaveAttribute("readonly", "");
  await capture("oligo-edit-readonly");
  await page.locator('textarea[name="description"]').fill(long);
  await page.getByRole("button", { name: "Save changes", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/oligos/${id}\\?updated=1`));
  await page.reload(); await expect(page.getByText(long, { exact: true })).toBeVisible();
  for (const [route, name] of [["/targets/new", "target"], ["/assays/new", "assay-numeric"], ["/experiments/new", "experiment"], ["/validation/new", "validation"], ["/projects/new", "project"]]) {
    await page.goto(route);
    await expect(page.locator(".record-form")).toBeVisible();
    if (route === "/assays/new") {
      await page.locator('input[name="expected_amplicon_length"]').fill("186");
      await page.locator('input[name="recommended_annealing_temperature_c"]').fill("61.3");
      await expect(page.locator('input[name="expected_amplicon_length"]')).toHaveAttribute("min", "1");
      await expect(page.locator('input[name="recommended_annealing_temperature_c"]')).toHaveAttribute("step", "0.1");
    }
    await capture(name);
  }
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/assays/new");
    await expect(page.locator('input[name="name"]')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    if ([390, 768].includes(width)) await capture(`assay-${width}`);
    await page.locator('input[name="name"]').focus();
    await page.keyboard.press("Tab");
    await expect(page.locator('select[name="experiment_type_id"]')).toBeFocused();
  }
});

test("submission waits for the real server and viewer forms are read-only", async ({ page }) => {
  test.skip(process.env.UI_EVIDENCE_STAGE === "before", "New submission and read-only presentation");
  await loginAs(page);
  await page.goto("/oligos/new");
  await page.locator('input[name="name"]').fill("FormSpec pending single submission");
  await page.locator('textarea[name="sequence"]').fill(uniqueDna(30_000_002, "GTC"));
  let release!: () => void;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  let posts = 0;
  await page.route("**/oligos/new", async (route) => {
    if (route.request().method() === "POST") { posts++; await gate; }
    await route.continue();
  });
  const button = page.getByRole("button", { name: "Register oligo", exact: true });
  const click = button.click();
  try {
    await expect(button).toBeDisabled();
    await expect(button).toHaveAttribute("aria-busy", "true");
    await expect(page.getByRole("status")).toContainText("Waiting for the server");
  } finally { release(); }
  await click;
  await expect(page).toHaveURL(/\/oligos\/OLG-/);
  expect(posts).toBe(1);
  const detail = page.url();
  await page.reload();
  await expect(page.getByRole("heading", { name: "FormSpec pending single submission", exact: true })).toBeVisible();
  await page.getByLabel("Current user").click();
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page).toHaveURL(/\/login/);
  await loginAs(page, "viewer");
  for (const route of ["/oligos/new", "/targets/new", "/assays/new", "/experiments/new", "/validation/new", "/projects/new"]) {
    await page.goto(route);
    await expect(page.getByText("Read-only access", { exact: true })).toBeVisible();
    await expect(page.locator('.record-form button[type="submit"]')).toHaveCount(0);
  }
  await page.goto(detail);
  await expect(page.getByRole("heading", { name: "404", exact: true })).toBeVisible();
});

test("assay errors preserve repeated associations and numeric inputs before real persistence", async ({ page }) => {
  test.skip(process.env.UI_EVIDENCE_STAGE === "before", "New draft restoration");
  await loginAs(page);
  const forward = await createOligo(page, "FormSpec association forward", uniqueDna(30_000_003, "GTC"));
  const reverse = await createOligo(page, "FormSpec association reverse", uniqueDna(30_000_004, "GTC"));
  await page.goto("/assays/new");
  await page.locator('input[name="name"]').fill("FormSpec persisted numeric assay");
  await page.locator('select[name="experiment_type_id"]').selectOption({ label: "PCR" });
  const forwardValue = await page.locator('select[name="oligo_id"] option').filter({ hasText: `${forward} · FormSpec association forward` }).first().getAttribute("value");
  const reverseValue = await page.locator('select[name="oligo_id"] option').filter({ hasText: `${reverse} · FormSpec association reverse` }).first().getAttribute("value");
  await page.locator('select[name="oligo_id"]').nth(0).selectOption(forwardValue!);
  await page.locator('select[name="oligo_id"]').nth(1).selectOption(forwardValue!);
  await page.locator('select[name="role"]').nth(0).selectOption("forward_primer");
  await page.locator('select[name="role"]').nth(1).selectOption("forward_primer");
  await page.locator('input[name="expected_amplicon_length"]').fill("186");
  await page.locator('input[name="recommended_annealing_temperature_c"]').fill("61.3");
  for (let attempt = 0; attempt < 2; attempt++) {
    await page.getByRole("button", { name: "Register assay", exact: true }).click();
    await expect(page.getByRole("button", { name: "Register assay", exact: true })).toBeEnabled();
    await expect(page.locator(".form-pending")).toHaveCount(0);
    await expect(page.locator('.form-error[role="alert"]')).toBeVisible();
    await expect(page.locator('select[name="oligo_id"]').nth(1)).toHaveValue(forwardValue!);
    await expect(page.locator('input[name="expected_amplicon_length"]')).toHaveValue("186");
    await expect(page.locator('input[name="recommended_annealing_temperature_c"]')).toHaveValue("61.3");
  }
  await page.locator('select[name="oligo_id"]').nth(1).selectOption(reverseValue!);
  await page.locator('select[name="role"]').nth(1).selectOption("reverse_primer");
  await page.getByRole("button", { name: "Register assay", exact: true }).click();
  await expect(page).toHaveURL(/\/assays\/ASY-/);
  await page.getByRole("link", { name: "Edit assay", exact: true }).click();
  await expect(page).toHaveURL(/\/assays\/ASY-[0-9]+\/edit$/);
  await expect(page.locator('input[name="expected_amplicon_length"]')).toBeVisible();
  await page.reload();
  await expect(page.locator('input[name="expected_amplicon_length"]')).toHaveValue("186");
  await expect(page.locator('input[name="recommended_annealing_temperature_c"]')).toHaveValue("61.3");
  // Associations are a set of (Oligo, role), not an API-ordered list. Verify the
  // persisted scientific pairing even when PostgreSQL returns the rows reversed.
  for (const [role, oligoId] of [["forward_primer", forwardValue!], ["reverse_primer", reverseValue!]]) {
    const row = page.locator(".association-row").filter({
      has: page.locator(`select[name="role"] option[value="${role}"]:checked`),
    });
    await expect(row).toHaveCount(1);
    await expect(row.locator('select[name="oligo_id"]')).toHaveValue(oligoId);
  }
});
