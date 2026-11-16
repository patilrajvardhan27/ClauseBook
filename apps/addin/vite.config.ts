import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Office Add-ins load over HTTPS even in dev, so the dev server is told
// to serve a self-signed cert the way office-addin-dev-certs expects.
export default defineConfig({
  plugins: [react()],
  server: { port: 3000, https: true },
});
