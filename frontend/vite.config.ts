import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In development the UI calls /api/... and Vite forwards it to Flask,
// so the browser sees one origin (no CORS), exactly like nginx in Docker.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:8000' },
  },
});
