<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { PhChatCircle, PhHeart, PhShareFat, PhUserCircle } from '@phosphor-icons/vue'
import { useAuthStore } from '@/stores/auth'
import { resolveAvatarUrl } from '@/utils/avatar'

const props = defineProps<{
  id: string
  authorId?: string | null
  author: string
  avatarUrl?: string | null
  handle?: string | null
  tier?: string | null
  /** Non-null only when the author has also become a Pal - routes the name/avatar click to
   * `/players/{playerId}` instead of the plain profile page. */
  playerId?: string | null
  timeAgo: string
  text: string
  hasImage?: boolean
  imageUrl?: string | null
  likes: number
  comments: number
  /** Omit for local-only mock views (`FeedSavedView`/`PostDetailView`, still on mock fixtures
   * until 3.8f/3.8g); pass it once a view is store-backed to make the like state controlled and
   * emit `toggle-like` for the parent to persist instead of toggling local state. */
  liked?: boolean
  /** `'status'` renders a compact, visually muted card (smaller avatar, trimmed action row, no
   * share button) for system-generated activity posts - see `FeedPost.kind`. Defaults to `'user'`
   * for every view not yet passing it through (`FeedSavedView`). */
  kind?: 'user' | 'status'
}>()

const isStatus = computed(() => props.kind === 'status')

const emit = defineEmits<{ 'toggle-like': []; 'open-comments': [] }>()

const router = useRouter()
const authStore = useAuthStore()

/** Where clicking the author's name/avatar goes: their own posts jump to "Your profile", a
 * Pal's to their full `/players/{id}` page, everyone else to a plain public profile. Falsy
 * when there's no author to link to (e.g. `FeedSavedView`'s local mock fallback). */
const profileRoute = computed(() => {
  if (!props.authorId) return null
  if (props.authorId === authStore.user?.id) return { name: 'feed-profile' }
  if (props.playerId) return { name: 'player-profile', params: { id: props.playerId } }
  return { name: 'user-profile', params: { id: props.authorId } }
})

function goToProfile() {
  if (profileRoute.value) router.push(profileRoute.value)
}

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
  <article
    class="rounded-xl p-4"
    :class="isStatus ? 'bg-gray-800/40 ring-1 ring-inset ring-white/5' : 'bg-gray-800/50'"
  >
    <div class="flex items-start justify-between gap-3">
      <component
        :is="profileRoute ? 'button' : 'div'"
        :type="profileRoute ? 'button' : undefined"
        class="flex items-center gap-3 text-left"
        :class="profileRoute && 'cursor-pointer'"
        @click="goToProfile"
      >
        <UAvatar
          :src="resolveAvatarUrl(props.authorId ?? props.author, props.avatarUrl)"
          :size="isStatus ? 'lg' : 'xl'"
          class="shrink-0 bg-white/10 text-slate-300"
        >
          <PhUserCircle :size="isStatus ? 16 : 20" />
        </UAvatar>
        <div>
          <div class="flex items-center gap-2">
            <span
              class="font-semibold text-white"
              :class="[isStatus && 'text-sm', profileRoute && 'hover:underline']"
              >{{ author }}</span
            >
            <UBadge v-if="tier" color="neutral" variant="soft" size="sm" class="rounded-full text-sm">{{ tier }}</UBadge>
          </div>
          <p class="text-sm text-slate-400">{{ handle ? `${handle} · ` : '' }}{{ timeAgo }}</p>
        </div>
      </component>
      <slot name="action" />
    </div>

    <p class="mt-3 text-md leading-relaxed" :class="isStatus ? 'text-slate-300' : 'text-slate-200'">{{ text }}</p>

    <img
      v-if="imageUrl"
      :src="imageUrl"
      alt=""
      class="mt-3 aspect-video w-full rounded-lg object-cover ring-1 ring-inset ring-white/10"
    />
    <div v-else-if="hasImage" class="mt-3 aspect-video w-full rounded-lg bg-white/5 ring-1 ring-inset ring-white/10" />

    <div v-if="!isStatus" class="mt-3 flex items-center gap-4 text-md text-slate-400">
      <button
        type="button"
        class="flex items-center gap-1.5 transition-colors hover:text-white"
        :class="isLiked && 'text-brand-400'"
        @click="toggleLike"
      >
        <PhHeart :size="24" :weight="isLiked ? 'fill' : 'regular'" />
        {{ displayLikes }}
      </button>
      <button type="button" class="flex items-center gap-1.5 transition-colors hover:text-white" @click="emit('open-comments')">
        <PhChatCircle :size="24" />
        {{ comments }}
      </button>
      <button type="button" class="ml-auto text-slate-400 transition-colors hover:text-white" aria-label="Share">
        <PhShareFat :size="24" />
      </button>
    </div>
    <div v-else class="mt-2 flex items-center gap-4 text-sm text-slate-400">
      <button
        type="button"
        class="flex items-center gap-1.5 transition-colors hover:text-white"
        :class="isLiked && 'text-brand-400'"
        @click="toggleLike"
      >
        <PhHeart :size="20" :weight="isLiked ? 'fill' : 'regular'" />
        {{ displayLikes }}
      </button>
      <button type="button" class="flex items-center gap-1.5 transition-colors hover:text-white" @click="emit('open-comments')">
        <PhChatCircle :size="20" />
        {{ comments }}
      </button>
    </div>
  </article>
</template>
