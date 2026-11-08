import { existsSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { expect, type APIResponse, type Browser, type BrowserContext, type Page } from "@playwright/test";

// MVP-02 acceptance always uses the disposable real Keycloak; no development bypass.
export const origin = process.env.PLAYWRIGHT_BASE_URL!;
export const evidenceDir = process.env.EVIDENCE_DIR ?? "/evidence";
export type Persona = "labadmin" | "scientist" | "reader" | "trainee" | "rival";
export function userLabel(persona: Persona): string {
  const name = persona.charAt(0).toUpperCase() + persona.slice(1);
  return `Synthetic ${name} · ${persona}@qualification.invalid`;
}

export interface Session {
  persona: Persona;
  context: BrowserContext;
  page: Page;
}

async function oidcLogin(page: Page, persona: Persona) {
  await page.goto("/login");
  await page.getByRole("button", { name: "Continue with institutional identity" }).click();
  await page.locator("#username").waitFor();
  await page.locator("#username").fill(`synthetic-${persona}`);
  await page.locator("#password").fill(process.env.QUALIFICATION_PASSWORD!);
  await page.locator("#kc-login").click();
  await page.waitForURL((url) => url.origin === origin && !url.pathname.startsWith("/realms/"));
}

export async function openSession(
  browser: Browser,
  persona: Persona,
  options: Parameters<Browser["newContext"]>[0] = {},
): Promise<Session> {
  // browser.newContext does not inherit the configured `use` options.
  const context = await browser.newContext({ baseURL: origin, ignoreHTTPSErrors: true, ...options });
  const page = await context.newPage();
  await oidcLogin(page, persona);
  await expect(page.getByLabel("Current user")).toBeVisible();
  return { persona, context, page };
}

async function authHeaders(session: Session): Promise<Record<string, string>> {
  // A fresh read refreshes the 90 s test access token server-side when needed.
  const response = await session.context.request.get(`${origin}/api/auth/session`);
  const value = (await response.json()) as { accessToken?: string };
  expect(Boolean(value.accessToken)).toBe(true);
  return { Authorization: `Bearer ${value.accessToken}` };
}

// Statuses and bodies only: never hand a token-bearing request object to expect().
export async function api(
  session: Session,
  path: string,
  method = "GET",
  body?: object,
  headers: Record<string, string> = {},
): Promise<APIResponse> {
  return session.context.request.fetch(`${origin}/api/v1${path}`, {
    method,
    headers: { ...(await authHeaders(session)), ...headers },
    data: body,
  });
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

export function recordEvidence(section: string, value: unknown) {
  const path = `${evidenceDir}/scientific-evidence.json`;
  const current: Record<string, unknown> = existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : {};
  current[section] = value;
  writeFileSync(path, JSON.stringify(current, null, 2));
}

// The browser container cannot control Docker. It asks the harness, through two empty
// files, to stop or start only the disposable scientific worker, then waits for the answer.
export async function controlWorker(action: "stop" | "start" | "fault" | "repair") {
  const request = `${evidenceDir}/worker-${action}-request`;
  const acknowledgement = `${evidenceDir}/worker-${action}-ack`;
  rmSync(acknowledgement, { force: true });
  writeFileSync(request, "");
  await expect
    .poll(() => (existsSync(acknowledgement) ? readFileSync(acknowledgement, "utf8") : ""), {
      timeout: 120_000,
      intervals: [500, 1000],
    })
    .toBe("ok");
  rmSync(request, { force: true });
  rmSync(acknowledgement, { force: true });
}
