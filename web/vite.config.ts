import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The Python API (python -m puzzle.server) runs on :8000; `npm run build`
// emits into web/dist, which that same server then serves at "/".
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
