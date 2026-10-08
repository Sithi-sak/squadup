<script setup lang="ts">
/**
 * Video.js 10 player for post clips (feed cards and the create-post preview). Wraps the
 * packaged `<video-skin>`, themed to the brand through its public CSS custom properties.
 * Class and other attrs land on the skin, which owns the player's size and layout. The theme
 * variables sit on the player so a caller can override one (e.g. the radius) from that class.
 */
import '@videojs/html/video/player'
import '@videojs/html/video/skin'

defineOptions({ inheritAttrs: false })

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
    <video-skin v-bind="$attrs" class="clip-player-skin block w-full">
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
