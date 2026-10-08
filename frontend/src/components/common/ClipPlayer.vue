<script setup lang="ts">
/**
 * Video.js 10 player for post clips (feed cards and the create-post preview). Wraps the
 * packaged `<video-skin>`, themed to the brand through its public CSS custom properties.
 * Class and other attrs land on the skin, which owns the player's size and layout. The theme
 * variables sit on the player so a caller can override one (e.g. the radius) from that class.
 */
import { onMounted, ref } from 'vue'
import '@videojs/html/video/player'
import '@videojs/html/video/skin'

defineOptions({ inheritAttrs: false })

/**
 * The packaged skin keeps its controls up whenever the clip is paused, which leaves a control
 * bar on every clip in the feed. With a mouse, hide them unless the pointer (or keyboard
 * focus) is on the player; while playing, the skin's own idle timer still applies. Touch
 * devices can't hover, so they keep the skin's default. The skin's styles live in its
 * shadow root, so this sheet is adopted there too; it targets only the public
 * `<media-controls-*>` tags, not the skin's private class names.
 */
const hoverControlsSheet = new CSSStyleSheet()
hoverControlsSheet.replaceSync(`
  @media (hover: hover) {
    :host(:not(:hover):not(:focus-within))
      :is(media-controls-backdrop, media-controls-content, media-controls-group) {
      opacity: 0;
      pointer-events: none;
    }
  }
`)

const skin = ref<HTMLElement | null>(null)

onMounted(async () => {
  await customElements.whenDefined('video-skin')
  const root = skin.value?.shadowRoot
  if (root && !root.adoptedStyleSheets.includes(hoverControlsSheet)) {
    root.adoptedStyleSheets = [...root.adoptedStyleSheets, hoverControlsSheet]
  }
})

withDefaults(
  defineProps<{
    src: string
    poster?: string | null
    preload?: 'none' | 'metadata' | 'auto'
  }>(),
  { poster: null, preload: 'metadata' },
)
</script>

<template>
  <!-- The skin only shows a poster set on the player, not one set on the <video>. -->
  <video-player :poster="poster ?? undefined" class="clip-player block">
    <video-skin ref="skin" v-bind="$attrs" class="clip-player-skin block w-full">
      <video :src="src" :preload="preload" playsinline />
    </video-skin>
  </video-player>
</template>

<style scoped>
.clip-player {
  --media-accent-color: var(--color-brand-600);
  --media-accent-text-color: white;
  --media-border-color: rgb(255 255 255 / 0.1);
  --media-border-radius: var(--radius-lg);
}

.clip-player-skin {
  border-radius: var(--media-border-radius);
  background-color: var(--color-slate-950);
}

.clip-player-skin:not(:defined) {
  visibility: hidden;
}
</style>
