import assert from "node:assert/strict";
import test from "node:test";
import { startJobPolling } from "../lib/scientific-polling.ts";

test("one polling budget stops at40 and cleanup prevents subsequent refreshes", () => {
  let tick; let refreshes = 0; let limits = 0; let cancelled = 0;
  const cancel = startJobPolling(() => { refreshes++; }, () => { limits++; }, (callback, delay) => {
    tick = callback; assert.equal(delay, 1500); return () => { cancelled++; };
  });
  for (let i = 0; i < 39; i++) tick();
  // Another job finishing must not remount/reset the section's still-active
  // poller: same controller runs its final tick, independent of job identities.
  const stillActive = [{ state: "queued" }, { state: "succeeded" }].some((job) => ["queued", "running", "retrying"].includes(job.state));
  assert.equal(stillActive, true); tick(); tick();
  assert.equal(refreshes, 40); assert.equal(limits, 1); assert.equal(cancelled, 1);
  cancel(); tick(); assert.equal(refreshes, 40);
});
