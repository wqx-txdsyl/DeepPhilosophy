import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { readFileSync } from 'node:fs';
const release = JSON.parse(readFileSync(new URL('../backend/agent_release.json', import.meta.url), 'utf8'));
export default defineConfig({
  define: { __PHIAGENT_VERSION__: JSON.stringify(release.release_version) },
  plugins: [react()],
  server: {
    host: true,
    port: 5201,
    headers: { 'Cache-Control': 'no-cache' },
    proxy: { '/api': { target: process.env.AGENT_API_TARGET || 'http://127.0.0.1:8011', changeOrigin: true } },
  },
});
