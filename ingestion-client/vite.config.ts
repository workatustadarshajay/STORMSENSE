import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The built client is served by the StormSense backend at /ingest/, next to the planner app.
// In development it runs on its own port and sends /api to the backend.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/ingest/" : "/",
  plugins: [react()],
  server: { port: 5174, proxy: { "/api": "http://localhost:8000" } },
  build: { outDir: "dist", sourcemap: false },
  test: { environment: "jsdom", globals: true },
}));
