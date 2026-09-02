import { expect, type Page } from "@playwright/test";

export async function loginAs(page: Page, identity: "admin" | "member" = "admin") {
  await page.goto("/login");
  await expect(page.getByRole("heading", { level: 1, name: "Welcome to OligoSpace." })).toBeVisible();
  const buttonName = identity === "admin"
    ? "Sign in as local administrator"
    : "Sign in as local researcher";
  await page.getByRole("button", { name: buttonName }).click();
  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { level: 1, name: /Welcome back/ })).toBeVisible();
}

export function uniqueDna(seed: number, prefix: string): string {
  const encoded = seed
    .toString(4)
    .padStart(24, "0")
    .replaceAll("0", "A")
    .replaceAll("1", "C")
    .replaceAll("2", "G")
    .replaceAll("3", "T");
  return `${prefix}${encoded}GCTA`;
}

export async function createOligo(page: Page, name: string, sequence: string): Promise<string> {
  await page.goto("/oligos/new");
  await page.locator('input[name="name"]').fill(name);
  await page.locator('textarea[name="sequence"]').fill(sequence);
  await page.getByRole("button", { name: "Register oligo" }).click();
  await expect(page).toHaveURL(/\/oligos\/OLG-[0-9]+/);
  await expect(page.getByRole("heading", { level: 1, name })).toBeVisible();
  return new URL(page.url()).pathname.split("/").at(-1) ?? "";
}

export async function createTarget(page: Page, name: string, geneIdentifier: string): Promise<string> {
  await page.goto("/targets/new");
  await page.locator('input[name="name"]').fill(name);
  await page.locator('input[name="gene_identifier"]').fill(geneIdentifier);
  await page.getByRole("button", { name: "Register target" }).click();
  await expect(page).toHaveURL(/\/targets\/TGT-[0-9]+/);
  await expect(page.getByRole("heading", { level: 1, name })).toBeVisible();
  return new URL(page.url()).pathname.split("/").at(-1) ?? "";
}
