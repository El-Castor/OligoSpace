import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";

import { createOligo, loginAs, uniqueDna } from "./helpers";

test("authenticated CSV download preserves the search and excludes private records", async ({ page }) => {
  await loginAs(page);
  const marker = `CSV-${Date.now()}`;
  const visibleName = `${marker} échantillon, "Bd21"`;
  const visible = await createOligo(page, visibleName, uniqueDna(Date.now(), "ACG"), "organization");
  const hidden = await createOligo(page, `${marker} private`, uniqueDna(Date.now() + 1, "TGC"));
  await page.goto("/api/auth/signout");
  await page.getByRole("button", { name: "Sign out" }).click();
  await loginAs(page, "viewer");
  await page.goto(`/oligos?q=${encodeURIComponent(marker)}`);
  await expect(page.getByRole("link", { name: visible, exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: hidden, exact: true })).toHaveCount(0);
  const pending = page.waitForEvent("download");
  await page.getByRole("link", { name: "Export visible oligos (CSV)" }).click();
  const download = await pending;
  expect(download.suggestedFilename()).toBe("oligos.csv");
  expect(await download.failure()).toBeNull();
  const path = await download.path();
  expect(path).not.toBeNull();
  const content = await readFile(path!, "utf8");
  expect(content.charCodeAt(0)).toBe(0xfeff);
  expect(content).toContain(visible);
  expect(content).toContain('échantillon, ""Bd21""');
  expect(content).not.toContain(hidden);
  expect(content).not.toContain(`${marker} private`);
});
