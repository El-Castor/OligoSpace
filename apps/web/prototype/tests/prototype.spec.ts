import { expect, test, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

async function capture(page: Page, name: string) {
  const folder = process.env.PROTOTYPE_SCREENSHOT_DIR;
  if (!folder) return;
  mkdirSync(folder, { recursive: true });
  await page.screenshot({ path: join(folder, name), fullPage: true });
}

test("desktop local interactions, component states, clipboard and reset", async ({ page }) => {
  const errors: string[] = [];
  const mutations: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
  page.on("request", (request) => {
    if (["POST", "PATCH", "PUT", "DELETE"].includes(request.method()) || request.url().includes("/api/")) mutations.push(`${request.method()} ${request.url()}`);
  });
  await page.goto("/");
  await expect(page).toHaveTitle("Scientific Soft UI · OligoSpace prototype");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Un espace clair pour la science.");
  await expect(page.getByText("Prototype · Données fictives · Aucune sauvegarde")).toBeVisible();
  await expect(page.getByRole("table").locator("tbody tr")).toHaveCount(6);
  await expect(page.locator(".su-sequence").first()).toHaveCSS("font-family", /monospace/);
  await page.getByLabel("Rechercher un oligo fictif").fill("Brachypodium distachyon");
  await expect(page.getByRole("table").locator("tbody tr")).toHaveCount(4);
  await page.getByLabel("Rechercher un oligo fictif").clear();
  await capture(page, "01-desktop.png");

  const row = page.getByRole("table").locator("tbody tr").first();
  const comfortable = await row.boundingBox();
  await page.getByRole("button", { name: "Compact", exact: true }).click();
  await expect(page.getByRole("button", { name: "Compact", exact: true })).toHaveAttribute("aria-pressed", "true");
  const compact = await row.boundingBox();
  expect(compact!.height).toBeLessThan(comfortable!.height * .85);
  await expect(page.getByRole("button", { name: "Compact", exact: true })).toHaveAttribute("aria-pressed", "true");
  await capture(page, "02-compact.png");
  await page.getByRole("button", { name: "Copier la séquence DEMO-OLG-001" }).click();
  const firstSequence = await row.locator(".su-sequence").textContent();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(firstSequence);
  await expect(page.getByRole("status").filter({ hasText: "Séquence DEMO-OLG-001 copiée." })).toBeVisible();
  await page.getByLabel("Rechercher un oligo fictif").fill("NO-MATCH");
  await expect(page.getByText("Aucun oligo ne correspond", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Réinitialiser les filtres" }).click();
  await page.getByLabel("Statut", { exact: true }).selectOption("Archivé");
  await expect(page.getByRole("table").locator("tbody tr")).toHaveCount(1);
  await page.getByLabel("Statut", { exact: true }).selectOption("Tous les statuts");

  const form = page.getByRole("region", { name: "Nouvel oligo", exact: true });
  await form.getByRole("textbox", { name: "Nom de l’oligo" }).fill("Exemple local");
  await form.getByRole("textbox", { name: "Séquence" }).fill("INVALID");
  await form.getByRole("button", { name: "Simuler la création" }).click();
  await expect(form.getByRole("alert")).toContainText("Pour cette simulation");
  await form.getByRole("textbox", { name: "Séquence" }).fill("ACGT ACGT");
  await form.getByRole("button", { name: "Simuler la création" }).click();
  await expect(form.getByRole("status")).toContainText("Ajout fictif en mémoire uniquement");
  await expect(page.getByRole("table").locator("tbody tr")).toHaveCount(7);
  await capture(page, "03-local-addition.png");

  const states = page.getByRole("region", { name: "États des composants" });
  await states.getByRole("button", { name: "Chargement", exact: true }).click();
  await expect(states.getByRole("status")).toContainText("Chargement de démonstration");
  await capture(page, "04-loading.png");
  await states.getByRole("button", { name: "Erreur", exact: true }).click();
  await expect(states.getByRole("alert")).toContainText("État simulé");
  await capture(page, "05-error.png");
  await states.getByRole("button", { name: "Vide", exact: true }).click();
  await expect(states.getByText("Aucun résultat dans cet exemple")).toBeVisible();
  await capture(page, "06-empty.png");
  await states.getByRole("button", { name: "Revenir aux composants" }).click();
  await expect(states.getByRole("button", { name: "Indisponible" })).toBeDisabled();
  await page.getByRole("button", { name: "Mettre en pause la simulation" }).click();
  await expect(page.getByText("Simulation en pause", { exact: true })).toHaveCount(2);
  await page.reload();
  await expect(page.getByRole("table").locator("tbody tr")).toHaveCount(6);
  expect(mutations).toEqual([]);
  expect(errors).toEqual([]);
});

test("mobile, keyboard focus, reduced motion and no document overflow", async ({ page }) => {
  for (const width of [320, 768, 1024]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Aller au contenu" })).toBeFocused();
  const outline = await page.getByRole("link", { name: "Aller au contenu" }).evaluate((element) => getComputedStyle(element).outlineWidth);
  expect(parseFloat(outline)).toBeGreaterThanOrEqual(3);
  await page.keyboard.press("Enter");
  await expect(page.locator("#prototype-main")).toBeFocused();
  await page.getByRole("button", { name: "Navigation", exact: true }).click();
  await expect(page.getByRole("navigation")).toBeVisible();
  await page.getByRole("link", { name: "Oligos", exact: true }).click();
  await expect(page.getByRole("button", { name: "Navigation", exact: true })).toHaveAttribute("aria-expanded", "false");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  const scrollRegion = page.getByRole("region", { name: "Tableau des oligos fictifs, défilement horizontal" });
  expect(await scrollRegion.evaluate((element) => element.scrollWidth > element.clientWidth)).toBe(true);
  await page.getByRole("button", { name: "Erreur", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("alert").filter({ hasText: "État simulé" })).toBeVisible();
  await page.getByRole("button", { name: "Chargement", exact: true }).click();
  expect(await page.locator(".su-skeleton").evaluate((element) => getComputedStyle(element).animationName)).toBe("none");
  await page.getByRole("button", { name: "Normal", exact: true }).click();
  await page.evaluate(() => window.scrollTo(0, 0));
  await capture(page, "07-mobile.png");
});

function luminance(color: string) {
  const rgb = color.match(/[\d.]+/g)!.slice(0, 3).map((value) => {
    const channel = Number(value) / 255;
    return channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4;
  });
  return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2];
}

test("key text, semantic badges and interactive boundaries meet AA contrast", async ({ page }) => {
  await page.goto("/");
  const pairs = await page.evaluate(() => {
    const colors = (selector: string, backgroundSelector = selector) => {
      const fg = getComputedStyle(document.querySelector(selector)!);
      const bg = getComputedStyle(document.querySelector(backgroundSelector)!);
      return { foreground: fg.color, background: bg.backgroundColor };
    };
    return [colors(".su-primary"), colors(".su-help", ".su-panel"), colors(".su-prototype-notice"), colors(".su-badge[data-status='Actif']"), colors(".su-badge[data-status='À revoir']"), colors(".su-badge[data-status='Archivé']"), ... ["--su-rail", "--su-rail-deep"].map((token) => { const sidebar = document.querySelector(".su-sidebar")!; const swatch = document.createElement("span"); swatch.style.backgroundColor = getComputedStyle(sidebar).getPropertyValue(token); sidebar.append(swatch); const pair = { foreground: getComputedStyle(sidebar.querySelector("nav a")!).color, background: getComputedStyle(swatch).backgroundColor }; swatch.remove(); return pair; })];
  });
  for (const pair of pairs) {
    const a = luminance(pair.foreground); const b = luminance(pair.background);
    expect((Math.max(a, b) + .05) / (Math.min(a, b) + .05)).toBeGreaterThanOrEqual(4.5);
  }
  const edge = await page.locator("input").first().evaluate((element) => {
    const style = getComputedStyle(element); return [style.borderTopColor, style.backgroundColor];
  });
  const a = luminance(edge[0]); const b = luminance(edge[1]);
  expect((Math.max(a, b) + .05) / (Math.min(a, b) + .05)).toBeGreaterThanOrEqual(3);
});
