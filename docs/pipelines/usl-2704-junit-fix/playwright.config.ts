import * as dotenv from 'dotenv';
import path from 'path';
import { defineConfig, type ReporterDescription } from '@playwright/test';

// Load the correct .env file based on ENV variable
const envFile = `.env.${process.env.ENV || 'qa'}`;
dotenv.config({ path: path.resolve(process.cwd(), 'lib', 'config', envFile) });

// Azure Pipelines sets TF_BUILD (NOT CI). GitHub Actions / others set CI.
// Detect either so the JUnit report is always produced on any CI system.
const isCI = !!process.env.CI || !!process.env.TF_BUILD;

// Base reporters used everywhere (local + CI).
const reporters: ReporterDescription[] = [
  ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ['line'],
  ['allure-playwright'],
];

// On CI, also emit JUnit XML consumed by the "Publish Test Results" task.
// Uses Playwright's BUILT-IN junit reporter (no dependency on a custom file).
if (isCI) {
  reporters.push(['junit', { outputFile: 'test-results/junit.xml' }]);
}

export default defineConfig({
  testDir: './tests',
  reporter: reporters,
  use: {
    baseURL: process.env.BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'smoke', grep: /@smoke/ },
    { name: 'regression', grep: /@regression/ },
    { name: 'all', grepInvert: /@smoke|@regression/ },
  ],
  globalTeardown: '',
});
