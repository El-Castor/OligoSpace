import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { loginAs } from "./helpers";

const before = process.env.UI_EVIDENCE_STAGE === "before";

test("real shell at all five widths with keyboard mobile navigation", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await loginAs(page);
  for (const width of [1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/");
    const root = process.env.UI_EVIDENCE_DIR;
    if (root) {
      await mkdir(`${root}/${before ? "before" : "after"}`, { recursive: true });
      await page.screenshot({ path: `${root}/${before ? "before" : "after"}/shell-${width}.png`, fullPage: true });
    }
    if (before) continue;
    if (width === 1440) {
      const pairs = await page.locator(".sidebar").evaluate((sidebar) => {
        const css = getComputedStyle(sidebar);
        return ["--rail", "--rail-deep"].flatMap((background) => ["--rail-text", "--rail-muted"].map((foreground) => {
          const swatch = document.createElement("span");
          swatch.style.color = css.getPropertyValue(foreground);
          swatch.style.backgroundColor = css.getPropertyValue(background);
          sidebar.append(swatch);
          const style = getComputedStyle(swatch);
          const pair = [style.color, style.backgroundColor];
          swatch.remove();
          return pair;
        }));
      });
      for (const [foreground, background] of pairs) {
        const luminance = (value: string) => {
          const [r, g, b] = value.match(/[\d.]+/g)!.slice(0, 3).map((part) => {
            const c = Number(part) / 255; return c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4;
          });
          return .2126 * r + .7152 * g + .0722 * b;
        };
        const a = luminance(foreground); const b = luminance(background);
        expect((Math.max(a, b) + .05) / (Math.min(a, b) + .05)).toBeGreaterThanOrEqual(4.5);
      }
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const nav = page.getByRole("navigation", { name: "Primary navigation" });
    if (width < 768) {
      await expect(nav).toBeHidden();
      const toggle = page.getByRole("button", { name: "Open navigation" });
      await toggle.focus();
      await page.keyboard.press("Enter");
      await expect(nav).toBeVisible();
      await expect(page.getByRole("button", { name: "Close navigation", exact: true })).toBeFocused();
      await expect(toggle).toHaveAttribute("aria-expanded", "true");
      await page.keyboard.press("Shift+Tab");
      await expect(nav.getByRole("link", { name: "Admin", exact: true })).toBeFocused();
      await page.keyboard.press("Tab");
      await expect(page.getByRole("button", { name: "Close navigation", exact: true })).toBeFocused();
      if (root) await page.screenshot({ path: `${root}/after/shell-${width}-open.png`, fullPage: false });
      await page.keyboard.press("Escape");
      await expect(toggle).toBeFocused();
      await expect(toggle).toHaveAttribute("aria-expanded", "false");
      await toggle.click();
      if (width === 390) {
        await page.setViewportSize({ width: 1024, height: 1000 });
        await expect(page.locator("#mobile-navigation")).not.toHaveAttribute("open");
        await page.setViewportSize({ width, height: 1000 });
        await expect(toggle).toHaveAttribute("aria-expanded", "false");
        await toggle.click();
      }
    }
    await nav.getByRole("link", { name: "Oligos", exact: true }).click();
    await expect(page).toHaveURL(/\/oligos$/);
    if (width < 768) await page.getByRole("button", { name: "Open navigation" }).click();
    await expect(nav.getByRole("link", { name: "Oligos", exact: true })).toHaveAttribute("aria-current", "page");
    await expect(nav.getByRole("link", { name: "Overview", exact: true })).not.toHaveAttribute("aria-current");
    if (width < 768) await page.keyboard.press("Escape");
  }
  expect(errors).toEqual([]);
});

for (const role of ["admin", "member", "viewer"] as const) {
  test(`shell preserves ${role} conditional links and user logout`, async ({ page }) => {
    test.skip(before, "Reference shell capture only");
    await loginAs(page, role);
    const nav = page.getByRole("navigation", { name: "Primary navigation" });
    await expect(nav.getByRole("link", { name: "Admin", exact: true })).toHaveCount(role === "admin" ? 1 : 0);
    await page.getByLabel("Current user").focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("link", { name: "Profile", exact: true })).toBeVisible();
    await page.getByLabel("Global search").focus();
    await expect(page.getByRole("link", { name: "Profile", exact: true })).toBeHidden();
    await page.getByLabel("Current user").focus();
    await page.keyboard.press("Enter");
    await page.keyboard.press("Escape");
    await expect(page.getByLabel("Current user")).toBeFocused();
    await page.keyboard.press("Enter");
    await page.getByRole("button", { name: "Logout", exact: true }).click();
    await expect(page).toHaveURL(/\/login/);
  });
}
