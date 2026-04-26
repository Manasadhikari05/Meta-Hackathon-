import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:7860',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // WS upgrade is flaky with some http-proxy setups; LiveDiscord connects
      // directly to :7860 in dev. Keep this for HTTPS / unified-host setups.
      '/ws': {
        target: 'http://localhost:7860',
        changeOrigin: false,
        ws: true,
      },
    },
  },
})
