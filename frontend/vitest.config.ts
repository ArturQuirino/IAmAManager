import { resolve } from 'node:path';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './vitest.setup.ts',
  },
  resolve: {
    // Mirror the tsconfig path alias ("@/*" -> "./*") so imports like
    // "@/lib/api" resolve the same way in tests as they do in the app.
    alias: {
      '@': resolve(__dirname, '.'),
    },
  },
});
