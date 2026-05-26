import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// VITE_PUBLIC_BASE is read as the build-time `base` so the same repo can
// produce a bundle mountable at any URL prefix. Default "./" (relative)
// makes a single build work both at root (HF Space at /) AND under any
// reverse-proxy mount (e.g. apps.thorwhalen.com/typola/) without rebuilding.
// Override only if you need an absolute prefix baked in at build time.
const PUBLIC_BASE = process.env.VITE_PUBLIC_BASE || "./";

export default defineConfig({
  base: PUBLIC_BASE,
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // In dev the frontend defaults to VITE_API_BASE=/api and the backend
      // serves unprefixed routes on port 8765 — strip /api here.
      "/api": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
});
