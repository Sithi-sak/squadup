<script setup lang="ts">
import { reactive } from 'vue'
import { PhChatCircle, PhHeart, PhShareFat, PhUserCircle } from '@phosphor-icons/vue'

const props = defineProps<{
  id: string
  author: string
  handle: string
  tier?: string | null
  timeAgo: string
  text: string
  hasImage?: boolean
  likes: number
  comments: number
}>()

const liked = reactive<Record<string, boolean>>({})
function toggleLike() {
  liked[props.id] = !liked[props.id]
}
</script>

<template>
  <article class="rounded-xl bg-gray-800/70 p-4">
    <div class="flex items-start justify-between gap-3">
      <div class="flex items-center gap-3">
        <UAvatar size="md" class="shrink-0 bg-white/10 text-slate-300">
          <PhUserCircle :size="20" />
        </UAvatar>
        <div>
          <div class="flex items-center gap-2">
            <span class="font-semibold text-white">{{ author }}</span>
            <UBadge v-if="tier" color="neutral" variant="soft" size="sm" class="rounded-full text-xs">{{ tier }}</UBadge>
          </div>
          <p class="text-xs text-slate-400">{{ handle }} · {{ timeAgo }}</p>
        </div>
      </div>
      <slot name="action" />
    </div>

    <p class="mt-3 text-sm leading-relaxed text-slate-200">{{ text }}</p>

    <div v-if="hasImage" class="mt-3 aspect-video w-full rounded-lg bg-white/5 ring-1 ring-inset ring-white/10" />

    <div class="mt-3 flex items-center gap-4 text-sm text-slate-400">
      <button
        type="button"
        class="flex items-center gap-1.5 transition-colors hover:text-white"
        :class="liked[id] && 'text-brand-400'"
        @click="toggleLike"
      >
        <PhHeart :size="18" :weight="liked[id] ? 'fill' : 'regular'" />
        {{ likes + (liked[id] ? 1 : 0) }}
      </button>
      <router-link :to="`/feed/${id}`" class="flex items-center gap-1.5 transition-colors hover:text-white">
        <PhChatCircle :size="18" />
        {{ comments }}
      </router-link>
      <button type="button" class="ml-auto text-slate-400 transition-colors hover:text-white" aria-label="Share">
        <PhShareFat :size="18" />
      </button>
    </div>
  </article>
</template>
