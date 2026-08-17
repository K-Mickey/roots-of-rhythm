import eslintConfigPrettier from 'eslint-config-prettier/flat';
import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';

export default defineConfig([
  ...nextVitals,
  eslintConfigPrettier,
  globalIgnores([
    '.next/**',
    'coverage/**',
    'playwright-report/**',
    'test-results/**',
  ]),
]);
