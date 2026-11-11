import { createHmac } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const origin = process.env.PLAYWRIGHT_BASE_URL!;
const issuer = `${origin}/realms/qualification`;
const identities: Record<string, string> = JSON.parse(process.env.QUALIFICATION_IDENTITIES!);

async function beginLogin(page: Page) {
  await page.goto("/login");
  await page.getByRole("button", { name: "Continue with institutional identity" }).click();
  await page.locator("#username").waitFor();
}

async function credentials(page: Page, identity: string) {
  await page.locator("#username").fill(`synthetic-${identity}`);
  await page.locator("#password").fill(process.env.QUALIFICATION_PASSWORD!);
  await page.locator("#kc-login").click();
}

async function login(page: Page, identity: string) {
  await beginLogin(page);
  await credentials(page, identity);
  await page.waitForURL((url) => url.origin === origin && !url.pathname.startsWith("/realms/"));
}

async function session(page: Page): Promise<{ accessToken?: string; error?: string }> {
  return page.evaluate(async () => (await fetch("/api/auth/session")).json());
}

async function expectSessionEnded(page: Page) {
  // The recovery path already sits on /login, so the URL cannot prove logout completion.
  await expect.poll(async () => {
    try { return Boolean((await session(page)).accessToken); }
    catch { return true; } // Navigation in progress: keep waiting, never treat as ended.
  }, { timeout: 20_000, intervals: [500, 1000] }).toBe(false);
}

async function api(page: Page, path: string, token?: string, method = "GET", body?: object) {
  // Return statuses only; never pass token-bearing request objects to expect().
  const response = await page.request.fetch(`/api/v1${path}`, {
    method,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    data: body,
  });
  return response;
}

async function keycloakAdmin(page: Page, path: string, method: string, body?: object) {
  const admin = await page.request.post("http://keycloak:8080/realms/master/protocol/openid-connect/token", {
    form: { grant_type: "password", client_id: "admin-cli", username: "synthetic-bootstrap", password: process.env.QUALIFICATION_ADMIN_PASSWORD! },
  });
  expect(admin.status()).toBe(200);
  const { access_token: token } = await admin.json();
  return page.request.fetch(`http://keycloak:8080/admin/realms/qualification${path}`, {
    method, data: body, headers: { Authorization: `Bearer ${token}` },
  });
}

test.beforeAll(async ({ request }) => {
  await expect.poll(async () => {
    try {
      const discovery = await request.get(`${issuer}/.well-known/openid-configuration`);
      const health = await request.get(`${origin}/api/v1/health/live`);
      const loginPage = await request.get(`${origin}/login`);
      return discovery.status() === 200 && health.status() === 200 && loginPage.status() === 200;
    } catch { return false; }
  }, { timeout: 180_000, intervals: [1000, 2000, 5000] }).toBe(true);
});

test("real login enforces PKCE, state, nonce and secure session cookies", async ({ page }) => {
  await page.goto("/login");
  await page.screenshot({ path: "/evidence/synthetic-login.png", fullPage: true });
  await beginLogin(page);
  const authorize = new URL(page.url());
  expect(authorize.searchParams.get("code_challenge_method")).toBe("S256");
  expect(Boolean(authorize.searchParams.get("code_challenge"))).toBe(true);
  expect(Boolean(authorize.searchParams.get("state"))).toBe(true);
  expect(Boolean(authorize.searchParams.get("nonce"))).toBe(true);
  const transient = await page.context().cookies(origin);
  for (const name of ["state", "pkce.code_verifier", "nonce"]) {
    const cookie = transient.find((candidate) => candidate.name.endsWith(name));
    expect(Boolean(cookie?.secure && cookie?.httpOnly && cookie?.sameSite === "Lax")).toBe(true);
  }
  await credentials(page, "admin");
  await expect.poll(async () => {
    try { return Boolean((await session(page)).accessToken); }
    catch { return false; }
  }).toBe(true);
  const value = await session(page);
  expect(Boolean(value.accessToken)).toBe(true);
  let claims: Record<string, unknown> = {};
  try {
    const decoded: unknown = JSON.parse(Buffer.from(value.accessToken!.split(".")[1], "base64url").toString("utf8"));
    if (decoded && typeof decoded === "object" && !Array.isArray(decoded)) claims = decoded as Record<string, unknown>;
  }
  catch { /* Only structural booleans are retained, including malformed payloads. */ }
  const me = await api(page, "/me", value.accessToken);
  const mePayload = await me.json().catch(() => null);
  const knownRules = ["invalid_token", "account_not_provisioned", "identity_provider_mismatch", "account_disabled"];
  const candidateRule = mePayload?.detail?.code;
  const realmAccess = claims.realm_access as { roles?: unknown } | undefined;
  writeFileSync("/evidence/oidc-structure.json", JSON.stringify({
    has_sub: typeof claims.sub === "string" && claims.sub.length > 0,
    issuer_expected: claims.iss === issuer,
    audience_expected: claims.aud === "oligospace-api" || (Array.isArray(claims.aud) && claims.aud.includes("oligospace-api")),
    realm_roles_present: Array.isArray(realmAccess?.roles) && realmAccess.roles.length > 0,
    me_status: me.status(),
    me_rule: typeof candidateRule === "string" && knownRules.includes(candidateRule) ? candidateRule : "other",
  }, null, 2));
  await expect(page.getByLabel("Current user")).toBeVisible();
  expect(me.status()).toBe(200);
  const identity = mePayload;
  expect(identity.role).toBe("admin");
  expect(identity.development_identity).toBe(false);
  const cookies = await page.context().cookies(origin);
  expect(cookies.some((cookie) => cookie.name.startsWith("__Secure-next-auth.session-token") && cookie.secure && cookie.httpOnly && cookie.sameSite === "Lax")).toBe(true);
  await page.reload();
  await expect(page.getByLabel("Current user")).toBeVisible();
  await page.screenshot({ path: "/evidence/synthetic-dashboard.png", fullPage: true });
});

test("a callback with forged state cannot establish a session", async ({ page }) => {
  await beginLogin(page);
  let interceptionSeen = false;
  await page.route((url) => url.pathname === "/realms/qualification/login-actions/authenticate", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    // Intercept the original form response: browser routing does not reliably
    // intercept a subsequent request within an HTTP redirect chain.
    const response = await route.fetch({ maxRedirects: 0 });
    const headers = response.headers();
    const location = headers.location;
    if (location) {
      const callback = new URL(location, origin);
      if (callback.origin === origin && callback.pathname === "/api/auth/callback/keycloak") {
        callback.searchParams.set("state", "synthetic-invalid-state");
        await route.fulfill({ response, headers: { ...headers, location: callback.toString() } });
        interceptionSeen = true; // The changed redirect was actually fulfilled.
        return;
      }
    }
    await route.fulfill({ response });
  });
  try {
    await credentials(page, "member");
    await expect(page).toHaveURL(/\/login/);
    expect(interceptionSeen).toBe(true);
    expect(Boolean((await session(page)).accessToken)).toBe(false);
  } finally {
    const path = new URL(page.url()).pathname;
    const pathClass = path.startsWith("/login") ? "login" : path.startsWith("/api/auth/") ? "auth" : path.startsWith("/realms/") ? "realms" : "other";
    let sessionPresent = true; // Fail closed if session inspection itself fails.
    try { sessionPresent = Boolean((await session(page)).accessToken); }
    catch { /* No session response or error text is retained. */ }
    writeFileSync("/evidence/state-probe.json", JSON.stringify({
      interception_seen: interceptionSeen,
      session_present: sessionPresent,
      path_class: pathClass,
    }, null, 2));
  }
});

test("administrator provisions a synthetic identity through the real UI", async ({ page }) => {
  await login(page, "pending");
  expect((await api(page, "/me", (await session(page)).accessToken)).status()).toBe(403);
  await expect(page.getByRole("heading", { name: "Account access unavailable" })).toBeVisible();
  await page.getByRole("link", { name: "Manage session" }).click();
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expectSessionEnded(page);
  await expect(page).toHaveURL(/\/login/);
  await login(page, "admin"); // Also proves the provider SSO session of the pending identity ended.
  await page.goto("/admin");
  await expect(page.getByRole("heading", { level: 1, name: "Administration" })).toBeVisible();
  const form = page.locator("form").filter({ has: page.getByRole("button", { name: "Create projection" }) });
  await form.getByLabel("External identity ID").fill(identities.pending);
  await form.getByLabel("Email", { exact: true }).fill("pending@qualification.invalid");
  await form.getByLabel("Display name").fill("Synthetic Pending");
  await form.getByRole("button", { name: "Create projection" }).click();
  await expect(page.getByRole("status")).toContainText("persisted and audited");
  await page.reload();
  await expect(page.locator(".admin-row").filter({ hasText: "pending@qualification.invalid" })).toBeVisible();
  await page.screenshot({ path: "/evidence/synthetic-administration.png", fullPage: true });
  await page.getByLabel("Current user").click();
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page).toHaveURL(/\/login/);
  await login(page, "pending");
  expect((await api(page, "/me", (await session(page)).accessToken)).status()).toBe(200);
});

for (const role of ["member", "viewer"]) {
  test(`${role} permissions remain server enforced`, async ({ page }) => {
    await login(page, role);
    const token = (await session(page)).accessToken;
    const me = await api(page, "/me", token);
    expect(me.status()).toBe(200);
    expect((await me.json()).role).toBe(role);
    expect((await api(page, "/workspace/admin/users", token)).status()).toBe(403);
    expect((await api(page, "/workspace/admin/users", token, "POST", { external_identity_id: "forbidden", email: "forbidden@qualification.invalid", display_name: "Forbidden", global_role: "admin" })).status()).toBe(403);
    if (role === "viewer") {
      expect((await api(page, "/workspace/projects", token, "POST", { name: "Forbidden", visibility: "private" })).status()).toBe(403);
    }
    await page.goto("/admin");
    await expect(page.getByRole("heading", { level: 1, name: "Access denied" })).toBeVisible();
  });
}

test("anonymous, malformed and development-header API requests are refused", async ({ page }) => {
  expect((await api(page, "/me")).status()).toBe(401);
  expect((await api(page, "/me", "synthetic-invalid-token")).status()).toBe(401);
  const response = await page.request.get("/api/v1/me", { headers: { "X-OligoSpace-Development-User": identities.admin, "X-OligoSpace-Development-Auth": "synthetic-forged" } });
  expect(response.status()).toBe(401);
});

test("invalid password does not establish an application session", async ({ page }) => {
  await beginLogin(page);
  await page.locator("#username").fill("synthetic-member");
  await page.locator("#password").fill("synthetic-wrong-password");
  await page.locator("#kc-login").click();
  await expect(page.locator("#password")).toBeVisible();
  expect(Boolean((await session(page)).accessToken)).toBe(false);
});

test("project membership grant and revocation apply to the same issued token", async ({ page, browser }) => {
  await login(page, "admin");
  const adminToken = (await session(page)).accessToken;
  const memberContext = await browser.newContext({ baseURL: origin, ignoreHTTPSErrors: process.env.PILOT_STRICT_TLS !== "1" });
  try {
    const member = await memberContext.newPage();
    await login(member, "member");
    const memberToken = (await session(member)).accessToken;
    const memberIdentity = await (await api(member, "/me", memberToken)).json();
    const created = await api(page, "/workspace/projects", adminToken, "POST", { name: "Synthetic private membership qualification", visibility: "private" });
    expect(created.status()).toBe(201);
    const project = await created.json();
    const detail = `/workspace/projects/${project.public_id}`;
    const membership = `/workspace/projects/${project.public_id}/members/${memberIdentity.id}`;
    expect((await api(member, detail, memberToken)).status()).toBe(404);
    expect((await api(page, membership, adminToken, "PUT", { role: "member" })).status()).toBe(200);
    const permitted = await api(member, detail, memberToken);
    expect(permitted.status()).toBe(200);
    expect((await permitted.json()).name).toBe("Synthetic private membership qualification");
    await member.goto(`/projects/${project.public_id}`);
    await expect(member.getByRole("heading", { level: 1 })).toContainText("Synthetic private membership qualification");
    await member.reload();
    await expect(member.getByRole("heading", { level: 1 })).toContainText("Synthetic private membership qualification");
    expect((await api(page, membership, adminToken, "DELETE")).status()).toBe(204);
    expect((await api(member, detail, memberToken)).status()).toBe(404);
    expect((await api(member, "/me", memberToken)).status()).toBe(200);
  } finally { await memberContext.close(); }
});

test("local account deactivation rejects a still-valid provider token", async ({ page, browser }) => {
  await login(page, "admin");
  const adminToken = (await session(page)).accessToken;
  const memberContext = await browser.newContext({ baseURL: origin, ignoreHTTPSErrors: process.env.PILOT_STRICT_TLS !== "1" });
  let userId: string | undefined;
  try {
    const member = await memberContext.newPage();
    await login(member, "member");
    const token = (await session(member)).accessToken;
    userId = (await (await api(member, "/me", token)).json()).id;
    expect((await api(page, `/workspace/admin/users/${userId}`, adminToken, "PATCH", { active: false })).status()).toBe(200);
    expect((await api(member, "/me", token)).status()).toBe(403);
    await member.goto("/");
    await expect(member.getByRole("heading", { name: "Account access unavailable" })).toBeVisible();
    await member.getByRole("link", { name: "Manage session" }).click();
    await member.getByRole("button", { name: "Logout", exact: true }).click();
    await expectSessionEnded(member);
    await expect(member).toHaveURL(/\/login/);
    await beginLogin(member); // Provider SSO must also have been ended.
    await expect(member.locator("#password")).toBeVisible();
  } finally {
    if (userId) expect((await api(page, `/workspace/admin/users/${userId}`, adminToken, "PATCH", { active: true })).status()).toBe(200);
    await memberContext.close();
  }
});

test("provider logout failure preserves the session and a confirmed retry revokes it", async ({ page }) => {
  await login(page, "member");
  const issued = (await session(page)).accessToken;
  expect(Boolean(issued)).toBe(true);
  await page.route("**/api/auth/provider-logout", async (route) => {
    await route.fulfill({ status: 503, contentType: "application/json", body: '{"code":"provider_logout_not_confirmed"}' });
  });
  await page.getByLabel("Current user").click();
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page.locator(".user-popover").getByRole("alert")).toHaveText("Logout could not be completed. Please retry.");
  await expect(page.getByRole("button", { name: "Logout", exact: true })).toBeEnabled();
  expect(Boolean((await session(page)).accessToken)).toBe(true);
  expect((await api(page, "/me", issued)).status()).toBe(200);
  const cookies = await page.context().cookies(origin);
  expect(cookies.some((cookie) => cookie.name.startsWith("__Secure-next-auth.session-token"))).toBe(true);
  await page.unroute("**/api/auth/provider-logout");
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page).toHaveURL(/\/login/);
  expect(Boolean((await session(page)).accessToken)).toBe(false);
  await expect.poll(async () => (await api(page, "/me", issued)).status(), { timeout: 15_000 }).toBe(401);
  await beginLogin(page);
  await expect(page.locator("#password")).toBeVisible();
});

test("expired access tokens refresh and logout revokes the provider session", async ({ page }) => {
  await login(page, "member");
  const original = (await session(page)).accessToken;
  expect(Boolean(original)).toBe(true);
  await expect.poll(async () => {
    const current = await session(page);
    return Boolean(current.accessToken && current.accessToken !== original && !current.error);
  }, { timeout: 110_000, intervals: [5000] }).toBe(true);
  expect((await api(page, "/me", (await session(page)).accessToken)).status()).toBe(200);
  await page.getByLabel("Current user").click();
  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login/);
  expect(Boolean((await session(page)).accessToken)).toBe(false);
  await beginLogin(page); // Provider SSO must also have been ended.
  await expect(page.locator("#password")).toBeVisible();
});

test("Keycloak account disable rejects an already issued token and failed refresh", async ({ page }) => {
  await login(page, "disabled");
  const token = (await session(page)).accessToken;
  expect((await api(page, "/me", token)).status()).toBe(200);
  expect((await keycloakAdmin(page, `/users/${identities.disabled}`, "PUT", { enabled: false })).status()).toBe(204);
  await expect.poll(async () => (await api(page, "/me", token)).status(), { timeout: 15_000 }).toBe(401);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Session required" })).toBeVisible();
  await expect.poll(async () => {
    const current = await session(page);
    return !current.accessToken && current.error === "RefreshAccessTokenError";
  }, { timeout: 110_000, intervals: [5000] }).toBe(true);
});

function totp(secret: string): string {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
  const bits = [...secret.replace(/\s/g, "").toUpperCase()].map((letter) => alphabet.indexOf(letter).toString(2).padStart(5, "0")).join("");
  const key = Buffer.from(bits.match(/.{8}/g)!.map((byte) => parseInt(byte, 2)));
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 30_000)));
  const digest = createHmac("sha1", key).update(counter).digest();
  return ((digest.readUInt32BE(digest[19] & 15) & 0x7fffffff) % 1_000_000).toString().padStart(6, "0");
}

test("provider TOTP enrollment and next-login MFA challenge are enforced", async ({ page }) => {
  await beginLogin(page);
  await credentials(page, "mfa");
  await expect(page.locator("#totp")).toBeVisible();
  await page.locator("#mode-manual").click();
  const secret = (await page.locator("#kc-totp-secret-key").innerText()).replace(/\s/g, "");
  const enrollmentCode = totp(secret);
  await page.locator("#totp").fill(enrollmentCode);
  await page.locator("#userLabel").fill("Synthetic qualification authenticator");
  await page.locator("#saveTOTPBtn").click();
  await page.waitForURL((url) => url.origin === origin && !url.pathname.startsWith("/realms/"));
  await page.context().clearCookies();
  await beginLogin(page);
  await credentials(page, "mfa");
  await expect(page.locator("#otp")).toBeVisible();
  expect(Boolean((await session(page)).accessToken)).toBe(false);
  await page.locator("#otp").fill("invalid");
  await page.locator("#kc-login").click();
  await expect(page.locator("#otp")).toBeVisible();
  await expect.poll(() => totp(secret) !== enrollmentCode, { timeout: 35_000, intervals: [1000] }).toBe(true);
  await page.locator("#otp").fill(totp(secret));
  await page.locator("#kc-login").click();
  await page.waitForURL((url) => url.origin === origin && !url.pathname.startsWith("/realms/"));
  expect(Boolean((await session(page)).accessToken)).toBe(true);
});

test("identities from different organizations cannot read or modify each other's data", async ({ page, browser }) => {
  const suffix = `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
  const markerA = `xorga${suffix}`;
  const markerB = `xorgb${suffix}`;
  const sequence = Array.from({ length: 24 }, () => "ACGT"[Math.floor(Math.random() * 4)]).join("");
  await login(page, "admin");
  const tokenA = (await session(page)).accessToken;
  const otherContext = await browser.newContext({ baseURL: origin, ignoreHTTPSErrors: process.env.PILOT_STRICT_TLS !== "1" });
  try {
    const other = await otherContext.newPage();
    await login(other, "foreign");
    const tokenB = (await session(other)).accessToken;
    const meA = await (await api(page, "/me", tokenA)).json();
    const meB = await (await api(other, "/me", tokenB)).json();
    // Two real Keycloak identities, both administrators, in distinct organizations.
    expect(meA.role).toBe("admin");
    expect(meB.role).toBe("admin");
    expect(meA.organization_id).not.toBe(meB.organization_id);

    const team = await (await api(page, "/workspace/teams", tokenA, "POST", { name: `team-${markerA}` })).json();
    const projectResponse = await api(page, "/workspace/projects", tokenA, "POST", { name: `project-${markerA}`, visibility: "organization", team_id: team.id });
    expect(projectResponse.status()).toBe(201);
    const project = await projectResponse.json();
    const oligoResponse = await api(page, "/registry/oligos", tokenA, "POST", { name: `oligo-${markerA}`, sequence, visibility: "organization", owner_project_id: project.id });
    expect(oligoResponse.status()).toBe(201);
    const oligo = (await oligoResponse.json()).oligo;

    // Organization B: direct API reads of every foreign record are not found.
    for (const path of [`/registry/oligos/${oligo.public_id}`, `/workspace/projects/${project.public_id}`, `/workspace/teams/${team.id}`]) {
      expect((await api(other, path, tokenB)).status()).toBe(404);
    }
    // Lists, search, CSV export and the user directory disclose nothing foreign.
    for (const path of [`/registry/oligos?q=${markerA}`, `/registry/oligos?q=${sequence}`, "/registry/oligos", "/workspace/projects", "/workspace/teams", "/workspace/users", "/workspace/admin/users", "/workspace/dashboard", "/registry/oligos/export.csv"]) {
      const response = await api(other, path, tokenB);
      expect(response.status()).toBe(200);
      const body = await response.text();
      const leaked = [markerA, sequence, "admin@qualification.invalid", "member@qualification.invalid", meA.external_identity_id].some((value) => body.includes(value));
      expect(leaked).toBe(false);
    }
    // Direct modification attempts, including the most privileged foreign role, are refused.
    expect((await api(other, `/registry/oligos/${oligo.public_id}`, tokenB, "PATCH", { name: "overwritten" })).status()).toBe(404);
    expect((await api(other, `/workspace/projects/${project.public_id}`, tokenB, "PATCH", { name: "overwritten" })).status()).toBe(404);
    expect((await api(other, `/workspace/projects/${project.public_id}/members/${meB.id}`, tokenB, "PUT", { role: "admin" })).status()).toBe(404);
    expect((await api(other, `/workspace/teams/${team.id}/members/${meB.id}`, tokenB, "PUT", { role: "admin" })).status()).toBe(404);
    expect((await api(other, `/workspace/admin/users/${meA.id}`, tokenB, "PATCH", { active: false })).status()).toBe(404);
    expect((await api(other, `/workspace/admin/users/${meA.id}`, tokenB, "PATCH", { global_role: "viewer" })).status()).toBe(404);
    // Foreign keys cannot reference another organization's team or project.
    for (const [path, body] of [["/workspace/projects", { name: `fk-${markerB}`, team_id: team.id }], ["/registry/oligos", { name: `fk-${markerB}`, sequence: "ACGTACGTACGTAAAACCCC", owner_project_id: project.id }]] as const) {
      expect([403, 404, 422]).toContain((await api(other, path, tokenB, "POST", body)).status());
    }
    // The foreign administrator is untouched and organization A data is unchanged.
    const stillA = await api(page, "/me", tokenA);
    expect(stillA.status()).toBe(200);
    expect((await stillA.json()).role).toBe("admin");
    expect((await (await api(page, `/registry/oligos/${oligo.public_id}`, tokenA)).json()).name).toBe(`oligo-${markerA}`);
    expect((await (await api(page, `/workspace/projects/${project.public_id}`, tokenA)).json()).name).toBe(`project-${markerA}`);

    // Reverse direction: organization B data is invisible to organization A's administrator.
    const ownProject = await (await api(other, "/workspace/projects", tokenB, "POST", { name: `project-${markerB}`, visibility: "organization" })).json();
    expect((await api(page, `/workspace/projects/${ownProject.public_id}`, tokenA)).status()).toBe(404);
    expect((await (await api(page, "/workspace/projects", tokenA)).text()).includes(markerB)).toBe(false);
    expect((await (await api(page, "/workspace/admin/users", tokenA)).text()).includes("foreign@qualification.invalid")).toBe(false);

    // Through the interface, foreign records are simply not found and not rendered.
    await other.goto(`/projects/${project.public_id}`);
    await expect(other.getByText("This page could not be found.")).toBeVisible();
    await expect(other.locator("body")).not.toContainText(markerA);
    await other.goto(`/oligos/${oligo.public_id}`);
    await expect(other.getByText("This page could not be found.")).toBeVisible();
    await expect(other.locator("body")).not.toContainText(markerA);
    await other.goto("/admin");
    await expect(other.getByRole("heading", { level: 1, name: "Administration" })).toBeVisible();
    await expect(other.locator("body")).toContainText("foreign@qualification.invalid");
    await expect(other.locator("body")).not.toContainText("member@qualification.invalid");
    await expect(other.locator("body")).not.toContainText(markerA);
  } finally { await otherContext.close(); }
});

const LOAD_LEVELS = [1, 4, 8, 16];
const REQUESTS_PER_PHASE = 80;

function round1(value: number) { return Math.round(value * 10) / 10; }
function percentile(sorted: number[], rank: number) {
  return sorted[Math.max(0, Math.min(sorted.length - 1, Math.ceil((rank / 100) * sorted.length) - 1))];
}

async function measure(endpoint: string, concurrency: number, call: () => Promise<boolean>) {
  const durations: number[] = [];
  let errors = 0;
  let issued = 0;
  const started = performance.now();
  await Promise.all(Array.from({ length: concurrency }, async () => {
    while (issued < REQUESTS_PER_PHASE) {
      issued += 1;
      const begin = performance.now();
      let ok = false;
      try { ok = await call(); } catch { ok = false; }
      durations.push(performance.now() - begin);
      if (!ok) errors += 1;
    }
  }));
  const seconds = (performance.now() - started) / 1000;
  durations.sort((left, right) => left - right);
  return {
    endpoint, concurrency, requests: REQUESTS_PER_PHASE, errors,
    p50_ms: round1(percentile(durations, 50)), p95_ms: round1(percentile(durations, 95)),
    max_ms: round1(durations[durations.length - 1]), throughput_rps: round1(REQUESTS_PER_PHASE / seconds),
  };
}

async function status(page: Page, path: string, token?: string) {
  const response = await api(page, path, token);
  const code = response.status();
  await response.dispose();
  return code;
}

test("introspection cost is measured under light concurrency without request errors", async ({ page }) => {
  await login(page, "member");
  for (let warmup = 0; warmup < 5; warmup += 1) expect(await status(page, "/me", (await session(page)).accessToken)).toBe(200);
  const results = [];
  for (const level of LOAD_LEVELS) {
    results.push(await measure("health_live_without_authentication", level, async () => (await status(page, "/health/live")) === 200));
    let token = (await session(page)).accessToken!;
    results.push(await measure("api_me_jwt_introspection_and_database", level, async () => (await status(page, "/me", token)) === 200));
    token = (await session(page)).accessToken!;
    results.push(await measure("keycloak_introspection_direct", level, async () => {
      const response = await page.request.post(`${issuer}/protocol/openid-connect/token/introspect`, {
        form: { token, client_id: "oligospace-web", client_secret: process.env.QUALIFICATION_CLIENT_SECRET! },
      });
      const active = response.status() === 200 && (await response.json()).active === true;
      return active;
    }));
  }
  writeFileSync("/evidence/introspection-load.json", JSON.stringify({ requests_per_phase: REQUESTS_PER_PHASE, results }, null, 2));
  // Valid credentials must never be refused because of the measurement load.
  expect(results.reduce((sum, item) => sum + item.errors, 0)).toBe(0);
});

async function orchestrate(request: string, acknowledgement: string) {
  writeFileSync(`/evidence/${request}`, "");
  await expect.poll(() => existsSync(`/evidence/${acknowledgement}`), { timeout: 120_000, intervals: [500] }).toBe(true);
  expect(readFileSync(`/evidence/${acknowledgement}`, "utf8")).toBe("ok");
}

test("Keycloak outage fails closed without cached acceptance and recovers", async ({ page }) => {
  test.setTimeout(420_000);
  await login(page, "member");
  const token = (await session(page)).accessToken!;
  const expiresAt = Number(JSON.parse(Buffer.from(token.split(".")[1], "base64url").toString("utf8")).exp) * 1000;
  expect(await status(page, "/me", token)).toBe(200);
  await orchestrate("outage-request", "outage-ack");
  const sequential: { code: number; ms: number }[] = [];
  for (let index = 0; index < 10; index += 1) {
    const begin = performance.now();
    sequential.push({ code: await status(page, "/me", token), ms: performance.now() - begin });
  }
  const concurrent = await Promise.all(Array.from({ length: 16 }, () => status(page, "/me", token)));
  const liveDuringOutage = await status(page, "/health/live");
  await page.goto("/");
  const sessionRequired = await page.getByRole("heading", { name: "Session required" }).isVisible();
  // The assertion is meaningful only while the already issued token is still unexpired.
  const tokenStillValid = Date.now() < expiresAt;
  const durations = sequential.map((item) => item.ms).sort((left, right) => left - right);
  const nonRefusals = sequential.filter((item) => item.code !== 401).length + concurrent.filter((code) => code !== 401).length;
  const restoreStarted = Date.now();
  await orchestrate("restore-request", "restore-ack");
  await expect.poll(async () => {
    try { return (await page.request.get(`${issuer}/.well-known/openid-configuration`)).status() === 200; }
    catch { return false; }
  }, { timeout: 180_000, intervals: [1000, 2000, 5000] }).toBe(true);
  const recoverySeconds = round1((Date.now() - restoreStarted) / 1000);
  const oldTokenAfterRecovery = await status(page, "/me", token);
  await page.context().clearCookies();
  await login(page, "member");
  const newLogin = await status(page, "/me", (await session(page)).accessToken);
  writeFileSync("/evidence/keycloak-outage.json", JSON.stringify({
    token_valid_during_outage: tokenStillValid,
    outage_requests: sequential.length + concurrent.length,
    outage_non_401: nonRefusals,
    outage_p50_ms: round1(percentile(durations, 50)),
    outage_max_ms: round1(durations[durations.length - 1]),
    health_live_status: liveDuringOutage,
    ui_session_required: sessionRequired,
    recovery_old_token_status: oldTokenAfterRecovery,
    recovery_new_login_status: newLogin,
    seconds_to_recover: recoverySeconds,
  }, null, 2));
  expect(tokenStillValid).toBe(true);
  expect(nonRefusals).toBe(0);
  expect(liveDuringOutage).toBe(200);
  expect(sessionRequired).toBe(true);
  expect(newLogin).toBe(200);
});
