import { defineConfig } from 'vite';
export default defineConfig({
  build: { rollupOptions: { input: { photo: 'index.html', room: 'room.html' } } },
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  preview: { proxy: { '/api': 'http://127.0.0.1:8000' } },
});
