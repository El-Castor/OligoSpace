import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { createOligo, loginAs, uniqueDna } from "./helpers";

test("real surfaces with empty, sparse and full dashboard data", async ({ page }) => {
  const before = process.env.UI_EVIDENCE_STAGE === "before";
  const root = process.env.UI_EVIDENCE_DIR;
  await page.setViewportSize({ width: 1440, height: 1000 });
  const capture = async (name: string) => {
    if (!root) return;
    const directory = `${root}/${before ? "before" : "after"}`;
    await mkdir(directory, { recursive: true });
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({ path: `${directory}/${name}.png`, fullPage: true });
  };
  await loginAs(page, "viewer");
  await expect(page.getByText("No recent resources", { exact: true })).toBeVisible();
  await expect(page.getByText("No recent activity", { exact: true })).toBeVisible();
  await capture("dashboard-empty");
  await page.getByLabel("Current user").click();
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page).toHaveURL(/\/login/);
  await loginAs(page);
  const id = await createOligo(page, "Surface specimen 01", uniqueDna(10_000_001, "CCC"), "organization");
  await page.goto("/");
  await expect(page.locator(".recent-list > a")).toHaveCount(1);
  await expect(page.locator(".activity-list > div")).toHaveCount(1);
  await capture("dashboard-sparse");
  for (let i = 2; i <= 11; i++) {
    await createOligo(page, `Surface specimen ${String(i).padStart(2, "0")}`, uniqueDna(10_000_000 + i, "CCC"), "organization");
  }
  await page.goto("/");
  await expect(page.locator(".recent-list > a")).toHaveCount(5);
  await expect(page.locator(".activity-list > div")).toHaveCount(8);
  await capture("dashboard-full");
  if (!before) {
    const sizes = await page.locator(".panel-grid > .panel").evaluateAll((panels) => panels.map((panel) => ({ height: panel.getBoundingClientRect().height, content: panel.lastElementChild!.getBoundingClientRect().bottom - panel.getBoundingClientRect().top })));
    for (const size of sizes) expect(size.height - size.content).toBeLessThan(4);
    expect(Math.abs(sizes[0].height - sizes[1].height)).toBeGreaterThan(30);
    const pairs = await page.evaluate(() => [".stat-detail", ".panel-copy", ".recent-list small", ".activity-list small"].map((selector) => {
      const element = document.querySelector(selector)!;
      const style = getComputedStyle(element);
      const background = getComputedStyle(element.closest(".stat, .panel")!).backgroundColor;
      return [style.color, background, style.fontSize];
    }));
    for (const [foreground, background, fontSize] of pairs) {
      const luminance = (color: string) => {
        const [r, g, b] = color.match(/[\d.]+/g)!.slice(0, 3).map((part) => {
          const c = Number(part) / 255; return c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4;
        });
        return .2126 * r + .7152 * g + .0722 * b;
      };
      const a = luminance(foreground); const b = luminance(background);
      expect((Math.max(a, b) + .05) / (Math.min(a, b) + .05)).toBeGreaterThanOrEqual(4.5);
      expect(parseFloat(fontSize)).toBeGreaterThanOrEqual(13);
    }
  }
  await page.goto(`/oligos/${id}`);
  await expect(page.getByRole("heading", { name: "Surface specimen 01", exact: true })).toBeVisible();
  await capture("record-details");
  await page.goto("/oligos/new");
  await capture("record-form");
  await page.locator('input[name="name"]').fill("Surface error probe");
  await page.locator('textarea[name="sequence"]').fill("INVALID!");
  await page.getByRole("button", { name: "Register oligo", exact: true }).click();
  await expect(page.locator('.notice[role="alert"]')).toBeVisible();
  await capture("record-error");
  for (const width of [320, 390, 768, 1024]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    if (width === 390) await capture("dashboard-mobile");
  }
});
