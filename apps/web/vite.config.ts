import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /v1 to the API so the web app never hardcodes a
// cross-origin base URL in local development; production builds read
// VITE_API_BASE_URL instead.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/v1": "http://localhost:8000" },
  },
});
