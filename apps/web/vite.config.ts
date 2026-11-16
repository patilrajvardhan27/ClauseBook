import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxies /v1 to the API in dev; production builds read VITE_API_BASE_URL instead.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/v1": "http://localhost:8000" },
  },
});
