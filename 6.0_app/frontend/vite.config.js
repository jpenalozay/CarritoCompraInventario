import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true
  },
  define: {
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify(process.env.VITE_API_BASE_URL || 'http://localhost:3003/api/v1'),
    'import.meta.env.VITE_RL_API_URL': JSON.stringify(process.env.VITE_RL_API_URL || 'http://localhost:5000/api/v1'),
    'import.meta.env.VITE_RL_DASHBOARD_URL': JSON.stringify(process.env.VITE_RL_DASHBOARD_URL || 'http://localhost:8050')
  }
})