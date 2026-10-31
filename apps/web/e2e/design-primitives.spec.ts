import { expect, test, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";

import { loginAs } from "./helpers";

const stage = process.env.UI_EVIDENCE_STAGE ?? "after";
async function capture(page: Page, name: string) {
  const root = process.env.UI_EVIDENCE_DIR;
  if (!root) return;
  await mkdir(`${root}/${stage}`, { recursive: true });
  await page.screenshot({ path: `${root}/${stage}/${name}.png`, fullPage: true });
}

test("production surfaces retain navigation, forms and responsive layout", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await loginAs(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await capture(page, "dashboard-desktop");
  await page.goto("/oligos");
  await expect(page.getByRole("link", { name: "Export visible oligos (CSV)" })).toBeVisible();
  await capture(page, "registry-desktop");
  await page.getByRole("link", { name: "New oligo", exact: true }).click();
  await expect(page.locator('textarea[name="sequence"]')).toBeVisible();
  await capture(page, "form-desktop");
  await page.locator('input[name="name"]').fill("UI validation probe");
  await page.locator('textarea[name="sequence"]').fill("INVALID!");
  await page.getByRole("button", { name: "Register oligo", exact: true }).click();
  const errorNotice = page.locator('.notice[role="alert"]');
  await expect(errorNotice).toBeVisible();
  if (stage !== "before") {
    const [foreground, background] = await errorNotice.evaluate((element) => {
      const style = getComputedStyle(element); return [style.color, style.backgroundColor];
    });
    const a = luminance(foreground); const b = luminance(background);
    expect((Math.max(a, b) + .05) / (Math.min(a, b) + .05)).toBeGreaterThanOrEqual(4.5);
  }
  await capture(page, "form-error");
  await page.goto("/oligos/new");
  for (const width of [320, 390, 768]) {
    await page.setViewportSize({ width, height: 844 });
    if (stage !== "before") {
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
    if (width === 390) await capture(page, "form-mobile");
  }
  expect(errors).toEqual([]);
});

function luminance(color: string) {
  const channels = color.match(/[\d.]+/g)!.slice(0, 3).map((value) => {
    const channel = Number(value) / 255;
    return channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4;
  });
  return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2];
}

test("shared primitives preserve visible keyboard focus and readable contrast", async ({ page }) => {
  test.skip(stage === "before", "Reference capture precedes new token adoption");
  await loginAs(page);
  await page.goto("/oligos/new");
  const field = page.locator('input[name="name"]');
  await field.focus();
  await page.keyboard.press("Tab");
  const focused = page.locator(":focus");
  expect(await focused.evaluate((element) => parseFloat(getComputedStyle(element).outlineWidth))).toBeGreaterThanOrEqual(3);
  await page.emulateMedia({ reducedMotion: "reduce" });
  const transition = await page.locator(".primary-button").last().evaluate((element) => getComputedStyle(element).transitionDuration);
  expect(transition).toBe("0s");
  const pairs = await page.evaluate(() => {
    const pair = (selector: string, property = "color", background = selector) => {
      const style = getComputedStyle(document.querySelector(selector)!);
      return [style.getPropertyValue(property), getComputedStyle(document.querySelector(background)!).backgroundColor];
    };
    return [pair(".primary-button"), pair(".secondary-button"), pair(".field small", "color", ".record-form"), pair(".field input", "border-top-color")];
  });
  pairs.forEach(([foreground, background], index) => {
    const a = luminance(foreground); const b = luminance(background);
    expect((Math.max(a, b) + .05) / (Math.min(a, b) + .05)).toBeGreaterThanOrEqual(index === 3 ? 3 : 4.5);
  });
  // Visual state probe on the real native control, not a mocked scientific workflow.
  const submit = page.getByRole("button", { name: "Register oligo", exact: true });
  await submit.evaluate((element: HTMLButtonElement) => { element.disabled = true; });
  await expect(submit).toBeDisabled();
  expect(await submit.evaluate((element) => getComputedStyle(element).boxShadow)).toBe("none");
  await capture(page, "form-disabled-focus");
});
