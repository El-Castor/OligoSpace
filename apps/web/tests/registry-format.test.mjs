import assert from "node:assert/strict";

import { formatMetric, formatPercent } from "../lib/registry-format.ts";

assert.equal(formatMetric(0, "bp"), "0 bp");
assert.equal(formatMetric(null, "bp"), "—");
assert.equal(formatPercent(0), "0%");
assert.equal(formatPercent(null), "—");
