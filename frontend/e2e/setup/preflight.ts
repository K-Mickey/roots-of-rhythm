import { chromium } from '@playwright/test';
import { existsSync } from 'node:fs';
import { BACKEND_URL, FRONTEND_URL } from './env';

function formatError(error: unknown): string {
  if (!(error instanceof Error)) return String(error);
  if (error.cause instanceof Error)
    return `${error.message}: ${error.cause.message}`;
  if (error.cause !== undefined)
    return `${error.message}: ${String(error.cause)}`;
  return error.message;
}

async function requireUp(name: string, url: string): Promise<void> {
  let response: Response;
  try {
    response = await fetch(url, { signal: AbortSignal.timeout(5000) });
  } catch (error) {
    throw new Error(
      `E2E target ${name} (${url}) is unreachable: ${formatError(error)}\n` +
        'Start the stack and load the corpus: make up && make migrate && make seed',
    );
  }
  if (!response.ok) {
    throw new Error(
      `E2E target ${name} (${url}) responded with HTTP ${response.status}`,
    );
  }
}

export default async function preflight(): Promise<void> {
  const execPath = chromium.executablePath(); // сам учитывает PLAYWRIGHT_BROWSERS_PATH и ОС
  if (!existsSync(execPath)) {
    throw new Error(
      `Playwright Chromium is missing (expected at ${execPath}): ` +
        'cd frontend && pnpm exec playwright install chromium',
    );
  }
  await requireUp('frontend', `${FRONTEND_URL}/api/health`);
  await requireUp('backend', `${BACKEND_URL}/health/ready`);
}
