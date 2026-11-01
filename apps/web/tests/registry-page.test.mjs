import assert from "node:assert/strict";
import test from "node:test";
import { registryOffset, registryHref, registryFailure } from "../lib/registry-page.ts";

test("pagination normalizes invalid offsets and preserves encoded searches", () => {
  for (const input of [undefined, "-1", "1.5", "Infinity", "9007199254740992", "<script>"]) assert.equal(registryOffset(input), 0);
  assert.equal(registryOffset("50"), 50);
  assert.equal(registryHref("/oligos", "A&C + α", 50), "/oligos?q=A%26C+%2B+%CE%B1&offset=50");
  assert.equal(registryHref("/oligos", "", 0), "/oligos");
});
test("authorization and session failures never become empty lists or raw server errors", () => {
  assert.match(registryFailure(403), /Access denied/);
  assert.match(registryFailure(401), /Session required/);
  assert.match(registryFailure(500), /could not be loaded/);
  assert.equal(registryFailure(), registryFailure(500));
});
