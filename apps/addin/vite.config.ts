import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Office Add-ins load over HTTPS even in dev, via office-addin-dev-certs.
export default defineConfig({
  plugins: [react()],
  server: { port: 3000, https: true },
});
