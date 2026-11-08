import type { Reporter, TestCase, TestResult } from "@playwright/test/reporter";

// Never serialize errors: Playwright errors can include callback URLs, cookies,
// request headers and evaluated session objects. No traces, video or HAR exist.
export default class SanitizedReporter implements Reporter {
  onTestEnd(test: TestCase, result: TestResult) {
    const error = result.errors[0];
    const message = error?.message ?? "";
    // Only fixed categories and numeric source coordinates leave the runner.
    // Never emit assertion values, call logs, snippets, error text or stacks.
    const category = message.includes("toHaveURL") ? "navigation"
      : message.includes("toBeVisible") ? "visibility"
      : message.includes("toBe(") ? "equality"
      : message.includes("Timeout") ? "timeout" : "other";
    const match = error?.stack?.match(/(?:authentication|scientific)\.spec\.ts:(\d+):\d+/);
    const sourceLine = error ? (error.location?.line ?? (match ? Number(match[1]) : null)) : null;
    process.stdout.write(`${JSON.stringify({ test: test.title, status: result.status, source_line: sourceLine, rule_id: error ? category : null })}\n`);
  }
  onEnd(result: { status: string }) {
    process.stdout.write(`${JSON.stringify({ qualification: result.status })}\n`);
  }
}
