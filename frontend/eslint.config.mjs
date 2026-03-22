import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

/** @see https://nextjs.org/docs/app/api-reference/config/eslint */
export default defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    // CommonJS config; require() is intentional.
    files: ["next.config.js"],
    rules: {
      "@typescript-eslint/no-require-imports": "off",
    },
  },
  {
    // Sync setState at effect start (e.g. setLoading(true)) is standard for data fetching;
    // full migration to derived state / transitions is tracked separately.
    rules: {
      "react-hooks/set-state-in-effect": "off",
    },
  },
  globalIgnores([
    ".next/**",
    "node_modules/**",
    "node_modules/.cache/**",
    "out/**",
    "build/**",
    "playwright-report/**",
    "test-results/**",
    "next-env.d.ts",
  ]),
]);
