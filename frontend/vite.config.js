import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: true, // listen on 0.0.0.0 so it works inside Docker
  },
});
