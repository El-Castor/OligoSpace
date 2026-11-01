import assert from "node:assert/strict";
import test from "node:test";
import { jobStateDescription, jobInputSequences, jobSourceHref } from "../lib/scientific-presentation.ts";

test("only actual backend states have descriptions; unknown states remain explicit", () => {
  for (const state of ["queued", "running", "retrying", "succeeded", "failed"]) assert.ok(jobStateDescription(state));
  assert.match(jobStateDescription("queued"), /No result is confirmed/);
  assert.match(jobStateDescription("failed"), /failed/);
  assert.equal(jobStateDescription("future_state"), "Server-reported state: future_state.");
});
test("input snapshots retain exact stored orientation, content and association order", () => {
  assert.equal(jobInputSequences({ subject: { type: "oligo" }, sequence: { normalized: "ACGT" } })[0].sequence, "ACGT");
  const pair = jobInputSequences({ forward: { normalized_sequence: "AAAA" }, reverse: { normalized_sequence: "CGTA" } });
  assert.deepEqual(pair.map((item) => item.sequence), ["AAAA", "CGTA"]);
  assert.deepEqual(jobInputSequences({}), []);
  assert.deepEqual(jobInputSequences({ sequence: { normalized: "invented-without-subject" } }), []);
});
test("source navigation uses supported persisted subject types only", () => {
  assert.equal(jobSourceHref({ subject: { type: "oligo", public_id: "OLG-000001" } }), "/oligos/OLG-000001");
  assert.equal(jobSourceHref({ subject: { type: "assay", public_id: "ASY-000001" } }), "/assays/ASY-000001");
  assert.equal(jobSourceHref({ subject: { type: "future", public_id: "X" } }), undefined);
});
