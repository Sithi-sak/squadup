<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  PhCaretLeft,
  PhCaretRight,
  PhChatCircle,
  PhHeart,
  PhShareFat,
  PhUserCircle,
  PhX,
} from '@phosphor-icons/vue'
import { useAuthStore } from '@/stores/auth'
import { useSharePost } from '@/composables/useSharePost'
import { resolveAvatarUrl } from '@/utils/avatar'
import { profileRouteFor } from '@/utils/profileRoute'

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
  /** First image. `imageUrls` carries the whole set; this stays for the mock-backed views that
   * only ever had one. */
  imageUrl?: string | null
  imageUrls?: string[] | null
  /** The composer's "Tag a game or service" pick, rendered as a hashtag under the post. Null on
   * posts made before tagging existed and on the mock-backed views. */
  tag?: string | null
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
const copyPostLink = useSharePost()
const shareItems = computed(() => [
  [{ label: 'Copy link', onSelect: () => copyPostLink(props.id) }],
])

/** Falsy when there's no author to link to (e.g. `FeedSavedView`'s local mock fallback). */
const profileRoute = computed(() =>
  profileRouteFor(props.authorId, authStore.user?.id, props.playerId),
)

function goToProfile() {
  if (profileRoute.value) router.push(profileRoute.value)
}

const localLiked = reactive<Record<string, boolean>>({})
const isLiked = computed(() =>
  props.liked !== undefined ? props.liked : (localLiked[props.id] ?? false),
)
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

const photos = computed(() =>
  props.imageUrls?.length ? props.imageUrls : props.imageUrl ? [props.imageUrl] : [],
)
/** Past five, the collage shows four tiles plus a "+N" cover on the fifth, like Facebook does. */
const visiblePhotos = computed(() => photos.value.slice(0, 5))
const hiddenCount = computed(() => photos.value.length - visiblePhotos.value.length)

/** Collage shapes by photo count: two side by side, a tall one beside a stacked pair for three,
 * a 2x2 for four, and for five or more a row of two over a row of three (a 6-column grid is the
 * smallest that divides into both halves and thirds). */
const gridClass = computed(() => {
  const count = visiblePhotos.value.length
  if (count === 2) return 'grid-cols-2 grid-rows-1'
  if (count >= 5) return 'grid-cols-6 grid-rows-2'
  return 'grid-cols-2 grid-rows-2'
})

function cellClass(index: number) {
  const count = visiblePhotos.value.length
  if (count === 3 && index === 0) return 'row-span-2'
  if (count >= 5) return index < 2 ? 'col-span-3' : 'col-span-2'
  return ''
}

const lightboxOpen = ref(false)
const lightboxIndex = ref(0)
const lightboxPhoto = computed(() => photos.value[lightboxIndex.value] ?? null)

function openLightbox(index: number) {
  lightboxIndex.value = index
  lightboxOpen.value = true
}

function stepLightbox(delta: number) {
  const count = photos.value.length
  if (count < 2) return
  lightboxIndex.value = (lightboxIndex.value + delta + count) % count
}

/** The modal's content isn't focused on open, so arrow keys have to come off the window. */
function onLightboxKey(event: KeyboardEvent) {
  if (event.key === 'ArrowLeft') stepLightbox(-1)
  else if (event.key === 'ArrowRight') stepLightbox(1)
}

watch(lightboxOpen, (isOpen) => {
  if (isOpen) window.addEventListener('keydown', onLightboxKey)
  else window.removeEventListener('keydown', onLightboxKey)
})
onBeforeUnmount(() => window.removeEventListener('keydown', onLightboxKey))
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
            <UBadge
              v-if="tier"
              color="neutral"
              variant="soft"
              size="sm"
              class="rounded-full text-sm"
              >{{ tier }}</UBadge
            >
          </div>
          <p class="text-sm text-slate-400">{{ handle ? `${handle} · ` : '' }}{{ timeAgo }}</p>
        </div>
      </component>
      <slot name="action" />
    </div>

    <p class="mt-3 text-md leading-relaxed" :class="isStatus ? 'text-slate-300' : 'text-slate-200'">
      {{ text }}
    </p>

    <button
      v-if="photos.length === 1"
      type="button"
      class="mt-3 block w-full cursor-zoom-in"
      aria-label="View full-size image"
      @click="openLightbox(0)"
    >
      <img
        :src="photos[0]"
        alt=""
        class="aspect-video w-full rounded-lg bg-slate-950 object-contain ring-1 ring-inset ring-white/10"
      />
    </button>
    <div
      v-else-if="photos.length > 1"
      class="mt-3 grid aspect-video w-full gap-1 overflow-hidden rounded-lg ring-1 ring-inset ring-white/10"
      :class="gridClass"
    >
      <button
        v-for="(photo, index) in visiblePhotos"
        :key="photo"
        type="button"
        class="relative cursor-zoom-in bg-slate-950"
        :class="cellClass(index)"
        :aria-label="`View photo ${index + 1} of ${photos.length}`"
        @click="openLightbox(index)"
      >
        <img :src="photo" alt="" class="h-full w-full object-cover" />
        <span
          v-if="hiddenCount > 0 && index === visiblePhotos.length - 1"
          class="absolute inset-0 flex items-center justify-center bg-black/55 text-2xl font-semibold text-white"
        >
          +{{ hiddenCount }}
        </span>
      </button>
    </div>
    <div
      v-else-if="hasImage"
      class="mt-3 aspect-video w-full rounded-lg bg-white/5 ring-1 ring-inset ring-white/10"
    />

    <button
      v-if="tag"
      type="button"
      class="mt-3 inline-flex rounded-full bg-white/5 px-3 py-1 text-xs font-medium text-slate-300 hover:bg-white/10 hover:text-white"
      @click="router.push({ path: '/feed/explore', query: { category: tag } })"
    >
      #{{ tag }}
    </button>

    <UModal
      v-if="photos.length"
      v-model:open="lightboxOpen"
      title="Image preview"
      :ui="{
        content: 'max-w-none w-auto bg-transparent shadow-none ring-0',
        overlay: 'bg-black/90',
      }"
    >
      <template #content="{ close }">
        <div class="relative flex items-center justify-center" @click="close">
          <img
            v-if="lightboxPhoto"
            :src="lightboxPhoto"
            alt=""
            class="max-h-[90vh] max-w-[90vw] rounded-lg object-contain"
            @click.stop
          />
          <UButton
            color="neutral"
            variant="solid"
            square
            class="absolute top-2 right-2 rounded-full bg-black/70 text-white hover:bg-black/80"
            aria-label="Close image preview"
            @click="close"
          >
            <PhX :size="18" />
          </UButton>

          <template v-if="photos.length > 1">
            <UButton
              color="neutral"
              variant="solid"
              square
              class="absolute top-1/2 left-2 -translate-y-1/2 rounded-full bg-black/70 text-white hover:bg-black/80"
              aria-label="Previous photo"
              @click.stop="stepLightbox(-1)"
            >
              <PhCaretLeft :size="18" weight="bold" />
            </UButton>
            <UButton
              color="neutral"
              variant="solid"
              square
              class="absolute top-1/2 right-2 -translate-y-1/2 rounded-full bg-black/70 text-white hover:bg-black/80"
              aria-label="Next photo"
              @click.stop="stepLightbox(1)"
            >
              <PhCaretRight :size="18" weight="bold" />
            </UButton>
            <span
              class="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full bg-black/70 px-3 py-1 text-xs text-white"
            >
              {{ lightboxIndex + 1 }} / {{ photos.length }}
            </span>
          </template>
        </div>
      </template>
    </UModal>

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
      <button
        type="button"
        class="flex items-center gap-1.5 transition-colors hover:text-white"
        @click="emit('open-comments')"
      >
        <PhChatCircle :size="24" />
        {{ comments }}
      </button>
      <UDropdownMenu :items="shareItems" class="ml-auto">
        <button
          type="button"
          class="text-slate-400 transition-colors hover:text-white"
          aria-label="Share"
        >
          <PhShareFat :size="24" />
        </button>
      </UDropdownMenu>
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
      <button
        type="button"
        class="flex items-center gap-1.5 transition-colors hover:text-white"
        @click="emit('open-comments')"
      >
        <PhChatCircle :size="20" />
        {{ comments }}
      </button>
    </div>
  </article>
</template>
