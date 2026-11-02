import assert from "node:assert/strict";
import test from "node:test";
import { accountRecovery } from "../lib/auth-presentation.ts";

test("expected authentication failures offer recovery without changing unrelated errors", () => {
  for (const code of ["invalid_token", "authentication_required", "development_session_required"]) assert.equal(accountRecovery(code).title, "Session required");
  for (const code of ["account_disabled", "account_not_provisioned", "identity_provider_mismatch"]) assert.equal(accountRecovery(code).title, "Account access unavailable");
  for (const code of ["forbidden", "not_found", "database_error"]) assert.equal(accountRecovery(code), null);
});
