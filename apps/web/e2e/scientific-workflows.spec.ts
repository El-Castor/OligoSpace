import { expect, test } from "@playwright/test";
import { createOligo, loginAs, uniqueDna } from "./helpers";

test("scientific workflow facts, exact copies, attempts and responsive provenance", async ({ page, context }) => {
  await loginAs(page);
  const sequence = uniqueDna(50_000_001, "GCG") + "ACGT".repeat(7) + "A";
  const id = await createOligo(page, "UI06 actual long QC", sequence, "organization");
  await page.getByRole("button", { name: "Run Primer3 analysis", exact: true }).click();
  await expect(page).toHaveURL(/scientific_job=SJOB-/);
  const job = page.locator(".scientific-job").first();
  await expect(job.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible({ timeout: 90_000 });
  const href = await job.getByRole("link").getAttribute("href");
  const publicId = await job.getByRole("link").innerText();
  await page.goto(href!);
  await expect(job.locator(".job-sequence")).toHaveText(sequence);
  await expect(job.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible();
  await expect(page.getByRole("progressbar")).toHaveCount(0);
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await job.getByRole("button", { name: `Copy ${publicId}`, exact: true }).click();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(publicId);
  await job.getByRole("button", { name: `Copy ${id} input sequence`, exact: true }).click();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(sequence);
  const raw = job.locator("details").filter({ has: page.getByText("Stored result JSON", { exact: true }) });
  await raw.locator("summary").click();
  const payload = await raw.locator("pre").innerText();
  await job.getByRole("button", { name: "Copy Primer3 result JSON", exact: true }).click();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(payload);
  const attempts = job.locator(".job-attempts summary");
  await attempts.focus(); await page.keyboard.press("Enter");
  const region = job.getByRole("region", { name: `${publicId} execution attempts` });
  await expect(region).toBeVisible();
  await page.keyboard.press("Tab"); await expect(region).toBeFocused();
  await job.getByText("Parameters and provenance", { exact: true }).click();
  const provenance = JSON.parse(await job.locator("details").filter({ has: page.getByText("Parameters and provenance", { exact: true }) }).locator("pre").innerText());
  expect(provenance.parameters.mv_conc_mM).toBe(50);
  expect(provenance.input_snapshot.sequence.normalized).toBe(sequence);
  expect(provenance.result.tool_version).toBe("2.6.1");
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
  await page.reload();
  await expect(job.getByRole("status", { name: "Execution state: succeeded" })).toBeVisible();
  await expect(job.locator(".job-sequence")).toHaveText(sequence);
  await page.getByRole("link", { name: "Open current source", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/oligos/${id}$`));
});
