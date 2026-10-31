import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { createOligo, createTarget, loginAs, uniqueDna } from "./helpers";

test("scientific tables retain real data, density, copy, search and pagination", async ({ page, context }) => {
  test.setTimeout(240_000);
  const before = process.env.UI_EVIDENCE_STAGE === "before";
  const root = process.env.UI_EVIDENCE_DIR;
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const capture = async (name: string) => {
    await expect(page.getByText("Loading records", { exact: true })).toHaveCount(0);
    if (!root) return;
    const directory = `${root}/${before ? "before" : "after"}`;
    await mkdir(directory, { recursive: true });
    await page.evaluate(() => { (document.activeElement as HTMLElement)?.blur(); document.querySelectorAll(".table-scroll").forEach((element) => { element.scrollLeft = 0; }); scrollTo(0, 0); });
    await page.screenshot({ path: `${directory}/${name}.png`, fullPage: true });
  };
  await page.setViewportSize({ width: 1440, height: 1000 });
  await loginAs(page);
  await page.goto("/oligos?q=TableSpec");
  await capture("oligos-empty");
  const sequence = uniqueDna(20_000_001, "CTC");
  const first = await createOligo(page, "TableSpec 01 — Brachypodium distachyon long resource name for complete scientific metadata", sequence);
  await page.goto("/oligos?q=TableSpec");
  await capture("oligos-one");
  for (let i = 2; i <= 55; i++) {
    await createOligo(page, `TableSpec ${String(i).padStart(2, "0")}`, uniqueDna(20_000_000 + i, "CTC"));
    if (i === 15) { await page.goto("/oligos?q=TableSpec"); await capture("oligos-fifteen"); }
  }
  await page.goto("/oligos?q=TableSpec");
  await expect(page.locator("tbody tr")).toHaveCount(50);
  await capture("oligos-many");
  if (!before) {
    const row = page.locator("tbody tr").first();
    await expect(row).toBeVisible();
    const comfortable = (await row.boundingBox())!.height;
    await page.getByRole("button", { name: "Compact", exact: true }).click();
    await expect(page.getByRole("button", { name: "Compact", exact: true })).toHaveAttribute("aria-pressed", "true");
    expect((await row.boundingBox())!.height).toBeLessThan(comfortable);
    await capture("oligos-compact");
    await page.getByRole("link", { name: "Next page" }).click();
    await expect(page.locator("tbody tr")).toHaveCount(5);
    await expect(page).toHaveURL(/q=TableSpec.*offset=50/);
    await page.getByRole("link", { name: "Previous page" }).click();
    await expect(page.locator("tbody tr")).toHaveCount(50);
    const idLink = page.locator("td.public-id a").first();
    expect(await idLink.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
    expect(await page.locator("td.numeric").first().evaluate((element) => getComputedStyle(element).textAlign)).toBe("right");
    const colors = await page.locator("th").first().evaluate((element) => { const style = getComputedStyle(element); return [style.color, style.backgroundColor]; });
    const luminance = (color: string) => {
      const [r, g, b] = color.match(/[\d.]+/g)!.slice(0, 3).map((n) => { const c = Number(n) / 255; return c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4; });
      return .2126 * r + .7152 * g + .0722 * b;
    };
    const [a, b] = colors.map(luminance);
    expect((Math.max(a, b) + .05) / (Math.min(a, b) + .05)).toBeGreaterThanOrEqual(4.5);
    await expect(page.getByRole("link", { name: "Export visible oligos (CSV)" })).toHaveAttribute("href", "/oligos/export?q=TableSpec");
    await page.goto("/oligos?q=TableSpec&offset=999");
    await expect(page.getByText("No records on this page", { exact: true })).toBeVisible();
    await page.getByRole("link", { name: "Return to first page", exact: true }).click();
    await expect(page.locator("tbody tr")).toHaveCount(50);
    await page.goto(`/oligos?q=${first}`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    // Existing HTTP test origin is insecure; browser permission override permits
    // deterministic clipboard tests without changing application/network config.
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    await page.getByRole("button", { name: `Copy ${first}`, exact: true }).click();
    await expect(page.getByRole("status")).toContainText("Copied");
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(first);
    await page.getByRole("button", { name: "Copy DNA sequence", exact: true }).click();
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(sequence);
    await page.evaluate(() => { Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: async () => { throw new Error("Permission denied"); } } }); });
    await page.getByRole("button", { name: "Copy DNA sequence", exact: true }).focus();
    await page.keyboard.press("Enter");
    await expect(page.getByText("Copy unavailable. Select and copy the value manually.", { exact: true })).toBeVisible();
    await page.getByText("Full value", { exact: true }).first().click();
    await expect(page.getByText("TableSpec 01 — Brachypodium distachyon long resource name for complete scientific metadata", { exact: true }).last()).toBeVisible();
    await capture("oligos-actions");
    await page.getByRole("link", { name: "Clear", exact: true }).click();
    await expect(page).toHaveURL(/\/oligos$/);
  }
  const target = await createTarget(page, "TableSpec target", "Bradi1g00010.very-long-identifier-for-full-value-inspection");
  await page.goto("/targets?q=TableSpec"); await capture("targets");
  await page.goto("/assays/new");
  await page.locator('input[name="name"]').fill("TableSpec assay");
  await page.locator('select[name="experiment_type_id"]').selectOption({ label: "PCR" });
  await page.locator('select[name="target_id"]').selectOption({ label: `${target} · TableSpec target` });
  await page.locator('select[name="oligo_id"]').nth(0).selectOption({ label: `${first} · TableSpec 01 — Brachypodium distachyon long resource name for complete scientific metadata` });
  await page.locator('select[name="role"]').nth(0).selectOption("forward_primer");
  await page.getByRole("button", { name: "Register assay" }).click();
  await expect(page).toHaveURL(/\/assays\/ASY-/);
  const assay = new URL(page.url()).pathname.split("/").at(-1)!;
  await page.goto("/assays?q=TableSpec"); await capture("assays");
  await page.goto(`/experiments/new?assay=${assay}`);
  await page.locator('input[name="performed_at"]').fill("2026-10-01T09:30");
  await page.locator('input[name="protocol_name"]').fill("TableSpec protocol");
  await page.getByRole("button", { name: "Record experiment run" }).click();
  await expect(page).toHaveURL(/\/experiments\/RUN-/);
  await page.goto("/experiments?q=TableSpec"); await capture("experiments");
  await page.goto("/projects"); await capture("projects");
  await page.goto("/admin"); await capture("admin-actions");
  await page.goto("/oligos?q=TableSpec");
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/oligos?q=TableSpec");
    await expect(page.getByText("Loading records", { exact: true })).toHaveCount(0);
    if ([390, 768].includes(width)) await capture(`oligos-${width}`);
    if (!before) {
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      const scroll = page.getByRole("region", { name: "Oligos data" });
      await scroll.focus(); await expect(scroll).toBeFocused();
      await page.keyboard.press("ArrowRight");
    }
  }
  await page.getByLabel("Current user").click();
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page).toHaveURL(/\/login/);
  await loginAs(page, "viewer");
  await page.goto("/oligos?q=TableSpec");
  await expect(page.locator("tbody tr")).toHaveCount(0);
  if (!before) await expect(page.getByText("No matching records", { exact: true })).toBeVisible();
  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: "Access denied", exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});

test("membership removal requires confirmation and preserves data when cancelled", async ({ page }) => {
  test.skip(process.env.UI_EVIDENCE_STAGE === "before", "New confirmation follows baseline");
  await loginAs(page);
  await page.goto("/projects/new");
  await page.locator('input[name="name"]').fill("UI04 confirmation project");
  await page.getByRole("button", { name: "Create project", exact: true }).click();
  await expect(page).toHaveURL(/\/projects\/PRJ-/);
  await page.locator('select[name="user_id"]').selectOption({ label: "Local researcher · researcher@oligospace.local" });
  await page.getByRole("button", { name: "Add or update", exact: true }).click();
  const member = page.locator(".member-row").filter({ hasText: "Local researcher" });
  await expect(member).toBeVisible();
  page.once("dialog", async (dialog) => { expect(dialog.message()).toContain("Remove this membership"); await dialog.dismiss(); });
  await member.getByRole("button", { name: "Remove", exact: true }).click();
  await page.reload(); await expect(member).toBeVisible();
  page.once("dialog", async (dialog) => { await dialog.accept(); });
  await member.getByRole("button", { name: "Remove", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("membership");
  await page.reload(); await expect(member).toHaveCount(0);
  await createTarget(page, "W".repeat(24), "UI04-wide-value");
  await page.goto("/targets?q=UI04-wide-value");
  const wide = page.locator("td .value-complete").filter({ hasText: "W".repeat(24) });
  await expect(wide).toBeVisible();
  expect(await wide.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
});
