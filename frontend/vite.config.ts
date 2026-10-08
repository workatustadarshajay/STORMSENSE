/// <reference types="vitest/config" />
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The built app is copied into backend/static and served by the same process as the API.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173, proxy: { "/api": "http://localhost:8000" } },
  // Fonts are embedded in the stylesheet: the Databricks workspace refuses to store binary font files in an app bundle.
  build: { outDir: "dist", sourcemap: false, assetsInlineLimit: 120_000 },
  test: { environment: "jsdom", globals: true, setupFiles: ["./src/test/setup.ts"], css: false, exclude: ["e2e/**", "node_modules/**"] },
});
