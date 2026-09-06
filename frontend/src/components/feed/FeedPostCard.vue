<script setup lang="ts">
import { computed, reactive } from 'vue'
import { PhChatCircle, PhHeart, PhShareFat, PhUserCircle } from '@phosphor-icons/vue'
import { resolveAvatarUrl } from '@/utils/avatar'

const props = defineProps<{
  id: string
  author: string
  handle?: string | null
  tier?: string | null
  timeAgo: string
  text: string
  hasImage?: boolean
  likes: number
  comments: number
  /** Omit for local-only mock views (`FeedSavedView`/`PostDetailView`, still on mock fixtures
   * until 3.8f/3.8g); pass it once a view is store-backed to make the like state controlled and
   * emit `toggle-like` for the parent to persist instead of toggling local state. */
  liked?: boolean
}>()

const emit = defineEmits<{ 'toggle-like': [] }>()

const localLiked = reactive<Record<string, boolean>>({})
const isLiked = computed(() => (props.liked !== undefined ? props.liked : (localLiked[props.id] ?? false)))
const displayLikes = computed(() =>
  props.liked !== undefined ? props.likes : props.likes + (localLiked[props.id] ? 1 : 0),
)

function toggleLike() {
  if (props.liked !== undefined) {
    emit('toggle-like')
    return
  }
  localLiked[props.id] = !localLiked[props.id]
}
</script>

<template>
  <article class="rounded-xl bg-gray-800/70 p-4">
    <div class="flex items-start justify-between gap-3">
      <div class="flex items-center gap-3">
        <UAvatar :src="resolveAvatarUrl(props.author)" size="md" class="shrink-0 bg-white/10 text-slate-300">
          <PhUserCircle :size="20" />
        </UAvatar>
        <div>
          <div class="flex items-center gap-2">
            <span class="font-semibold text-white">{{ author }}</span>
            <UBadge v-if="tier" color="neutral" variant="soft" size="sm" class="rounded-full text-xs">{{ tier }}</UBadge>
          </div>
          <p class="text-xs text-slate-400">{{ handle ? `${handle} · ` : '' }}{{ timeAgo }}</p>
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
        :class="isLiked && 'text-brand-400'"
        @click="toggleLike"
      >
        <PhHeart :size="18" :weight="isLiked ? 'fill' : 'regular'" />
        {{ displayLikes }}
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
