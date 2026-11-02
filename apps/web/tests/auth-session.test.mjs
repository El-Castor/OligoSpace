import assert from "node:assert/strict";
import test from "node:test";
import { refreshSessionToken, endProviderSession } from "../lib/auth-session.ts";

const config = { issuer: "https://identity.test/realms/lab", clientId: "app", clientSecret: "synthetic-test-only" };
const original = { sub: "subject", accessToken: "synthetic-old", refreshToken: "synthetic-refresh", accessTokenExpires: 1 };
test("refresh rotates credentials and preserves the subject", async () => {
  const fetcher = async (url, init) => {
    assert.equal(url, `${config.issuer}/protocol/openid-connect/token`);
    assert.equal(init.body.get("grant_type"), "refresh_token");
    assert.equal(init.cache, "no-store");
    assert.equal(init.redirect, "error");
    return Response.json({ access_token: "synthetic-new", refresh_token: "synthetic-rotated", expires_in: 60 });
  };
  const result = await refreshSessionToken(original, config, fetcher);
  assert.equal(result.sub, original.sub);
  assert.equal(result.accessToken, "synthetic-new");
  assert.equal(result.refreshToken, "synthetic-rotated");
  assert.ok(result.accessTokenExpires > Date.now());
});
test("refresh denial, malformed expiry and network failure erase usable credentials", async () => {
  for (const fetcher of [
    async () => Response.json({ error: "invalid_grant" }, { status: 400 }),
    async () => Response.json({ access_token: "synthetic-new", expires_in: "60" }),
    async () => Response.json({ access_token: "synthetic-new", expires_in: -1 }),
    async () => { throw new Error("synthetic-private-diagnostic"); },
  ]) {
    const result = await refreshSessionToken(original, config, fetcher);
    assert.equal(result.error, "RefreshAccessTokenError");
    assert.equal(result.accessToken, undefined);
    assert.equal(result.refreshToken, undefined);
  }
});
test("missing refresh token does not contact the identity provider", async () => {
  const result = await refreshSessionToken({ accessToken: "synthetic-old" }, config, async () => { assert.fail("must not fetch"); });
  assert.equal(result.error, "RefreshAccessTokenError");
  assert.equal(result.accessToken, undefined);
});
test("logout submits refresh credentials server-side and never follows redirects", async () => {
  const ok = await endProviderSession(original, config, async (url, init) => {
    assert.equal(url, `${config.issuer}/protocol/openid-connect/logout`);
    assert.equal(init.method, "POST");
    assert.equal(init.body.get("refresh_token"), original.refreshToken);
    assert.equal(init.body.get("client_secret"), config.clientSecret);
    assert.equal(init.redirect, "error");
    return new Response(null, { status: 204 });
  });
  assert.equal(ok, true);
  assert.equal(await endProviderSession(original, config, async () => new Response(null, { status: 503 })), false);
  assert.equal(await endProviderSession(original, config, async () => { throw new Error("private"); }), false);
});
