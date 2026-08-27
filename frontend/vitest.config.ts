import path from 'node:path';
import { fileURLToPath } from 'node:url';

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.join(rootDir, 'src'),
    },
  },
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/**/*.test.{ts,tsx}', 'src/api/schema.d.ts'],
    },
    environment: 'jsdom',
    exclude: ['e2e/**', 'node_modules/**'],
    setupFiles: ['./vitest.setup.ts'],
    pool: 'threads',
    fileParallelism: false,
    maxWorkers: 1,
  },
});
