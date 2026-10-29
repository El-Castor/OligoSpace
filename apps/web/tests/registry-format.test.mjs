import assert from "node:assert/strict";
import { test } from "node:test";
import { formatMetric, formatPercent } from "../lib/registry-format.ts";

test("formatMetric keeps zero and renders missing values as an em dash", () => {
  assert.equal(formatMetric(0, "bp"), "0 bp");
  assert.equal(formatMetric(null, "bp"), "—");
});

test("formatPercent keeps zero and renders missing values as an em dash", () => {
  assert.equal(formatPercent(0), "0%");
  assert.equal(formatPercent(null), "—");
});
