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
        input: {
          // Every text field across the SquadUp mockups (auth, settings, create
          // service, ...) is a full pill, never Nuxt UI's default rounded-md —
          // set that once here instead of overriding it on every UInput.
          slots: {
            base: 'w-full rounded-full border-0 appearance-none placeholder:text-dimmed disabled:cursor-not-allowed disabled:opacity-75 transition-colors',
          },
        },
        select: {
          slots: {
            base: [
              'relative group rounded-full inline-flex items-center disabled:cursor-not-allowed disabled:opacity-75 transition-colors',
            ],
          }
        }
      },
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
