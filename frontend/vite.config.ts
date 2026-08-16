import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import ui from '@nuxt/ui/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    ui({
      // SquadUp is dark-theme only (no light/dark toggle), so the @vueuse/core
      // color-mode integration is disabled — `dark` is set statically on <html>.
      colorMode: false,
      ui: {
        colors: {
          // 'brand' is a custom ramp defined in src/styles/theme.css, anchored
          // to the exact SquadUp brand hexes — the stock Tailwind 'emerald'
          // scale (OKLCH-based in v4) doesn't match #059669 precisely.
          primary: 'brand',
          neutral: 'slate',
        },
      },
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
