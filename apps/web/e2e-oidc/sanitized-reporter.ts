import type { Reporter, TestCase, TestResult } from "@playwright/test/reporter";

// Never serialize errors: Playwright errors can include callback URLs, cookies,
// request headers and evaluated session objects. No traces, video or HAR exist.
export default class SanitizedReporter implements Reporter {
  onTestEnd(test: TestCase, result: TestResult) {
    process.stdout.write(`${JSON.stringify({ test: test.title, status: result.status })}\n`);
  }
  onEnd(result: { status: string }) {
    process.stdout.write(`${JSON.stringify({ qualification: result.status })}\n`);
  }
}
