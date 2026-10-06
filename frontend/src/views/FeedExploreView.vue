<script setup lang="ts">
import { computed, onActivated, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  PhCopy,
  PhGameController,
  PhHeart,
  PhMagnifyingGlass,
  PhPlay,
  PhSpinnerGap,
  PhUserCircle,
  PhWarningCircle,
} from '@phosphor-icons/vue'
import { games } from '@/data/games'
import { exploreCategories } from '@/mocks/feed'
import { useFeedStore, type FeedPost } from '@/stores/feed'
import { resolveAvatarUrl } from '@/utils/avatar'

const route = useRoute()
const feedStore = useFeedStore()

onActivated(() => {
  feedStore.fetchFeed()
})

const search = ref('')
// Deep-linkable from `FeedRightRail.vue`'s "Trending now" (`?category=`), e.g. clicking a real
// post category there. Falls back to the "Trending" (unfiltered) tab otherwise.
const activeCategory = ref(
  typeof route.query.category === 'string' ? route.query.category : 'Trending',
)
watch(
  () => route.query.category,
  (category) => {
    if (typeof category === 'string') activeCategory.value = category
  },
)

/** A post is reachable by its `category` (the feed_category enum) and by its composer `tag`
 * (a game or service name), since `FeedPostCard.vue`'s hashtag links here with the tag. */
function topicsOf(post: FeedPost) {
  return [post.category, post.tag].filter((t): t is string => !!t).map((t) => t.toLowerCase())
}

/** System-generated `status` posts have nothing visual to show, so they stay out of the grid. */
const explorePosts = computed(() => feedStore.posts.filter((p) => p.kind !== 'status'))

const visiblePosts = computed(() => {
  const filtered =
    activeCategory.value === 'Trending'
      ? explorePosts.value
      : explorePosts.value.filter((p) => topicsOf(p).includes(activeCategory.value.toLowerCase()))

  if (!search.value) return filtered
  const q = search.value.toLowerCase()
  return filtered.filter(
    (p) => topicsOf(p).some((topic) => topic.includes(q)) || p.author.toLowerCase().includes(q),
  )
})

const gameCoverByName = new Map(
  games.filter((g) => g.coverUrl).map((g) => [g.name.toLowerCase(), g.coverUrl as string]),
)

type Tile =
  | { kind: 'media'; src: string; clip: boolean; multi: boolean }
  | { kind: 'clip-pending'; status: 'processing' | 'failed' }
  | { kind: 'text'; text: string }
  | { kind: 'cover'; src: string }
  | { kind: 'empty' }

/** What fills a tile, best first: the clip poster or first photo, an unfinished clip's state
 * (only its author sees those), the post's text, the tagged game's cover art, then nothing. */
function tileOf(post: FeedPost): Tile {
  if (post.videoPosterUrl) {
    return { kind: 'media', src: post.videoPosterUrl, clip: true, multi: false }
  }
  if (post.videoStatus === 'processing' || post.videoStatus === 'failed') {
    return { kind: 'clip-pending', status: post.videoStatus }
  }
  const photo = post.imageUrls[0] ?? post.imageUrl
  if (photo) return { kind: 'media', src: photo, clip: false, multi: post.imageUrls.length > 1 }
  if (post.text?.trim()) return { kind: 'text', text: post.text.trim() }
  const cover = post.tag ? gameCoverByName.get(post.tag.toLowerCase()) : undefined
  if (cover) return { kind: 'cover', src: cover }
  return { kind: 'empty' }
}

const tiles = computed(() => visiblePosts.value.map((post) => ({ post, tile: tileOf(post) })))

const categoryGradients: Record<string, string> = {
  games: 'from-indigo-500/40 via-slate-800 to-slate-900',
  chilling: 'from-teal-500/40 via-slate-800 to-slate-900',
  clips: 'from-rose-500/40 via-slate-800 to-slate-900',
}

function gradientOf(post: FeedPost) {
  return (
    categoryGradients[post.category.toLowerCase()] ??
    'from-emerald-500/40 via-slate-800 to-slate-900'
  )
}

function formatCount(count: number) {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`
}
</script>

<template>
  <div class="flex min-w-0 flex-col gap-4">
    <div>
      <h1 class="text-2xl font-bold text-white">Explore</h1>
      <p class="mt-1 text-sm text-slate-400">
        Discover trending posts, clips and creators across SquadUp
      </p>
    </div>

    <UInput
      v-model="search"
      placeholder="Search posts, clips, games or creators..."
      variant="subtle"
      size="lg"
      class="w-full rounded-full"
      :ui="{ base: 'rounded-full' }"
    >
      <template #leading>
        <PhMagnifyingGlass :size="18" />
      </template>
    </UInput>

    <div class="flex flex-wrap items-center gap-2">
      <UButton
        v-for="category in exploreCategories"
        :key="category"
        :color="activeCategory === category ? 'primary' : 'neutral'"
        :variant="activeCategory === category ? 'solid' : 'soft'"
        size="sm"
        class="rounded-full"
        @click="activeCategory = category"
      >
        {{ category }}
      </UButton>
    </div>

    <p v-if="visiblePosts.length === 0" class="py-16 text-center text-sm text-slate-400">
      No posts match this search.
    </p>

    <div v-else class="grid grid-cols-2 gap-4 sm:grid-cols-3">
      <router-link
        v-for="{ post, tile } in tiles"
        :key="post.id"
        :to="`/feed/${post.id}`"
        class="relative aspect-square overflow-hidden rounded-lg bg-white/5"
      >
        <template v-if="tile.kind === 'media'">
          <img
            :src="tile.src"
            alt=""
            loading="lazy"
            class="absolute inset-0 size-full object-cover"
          />
          <span
            v-if="tile.clip || tile.multi"
            class="absolute top-2 right-2 flex size-7 items-center justify-center rounded-full bg-black/50 text-white"
          >
            <PhPlay v-if="tile.clip" :size="14" weight="fill" />
            <PhCopy v-else :size="14" weight="fill" />
          </span>
        </template>
        <div
          v-else-if="tile.kind === 'clip-pending'"
          class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-slate-950 px-4 text-center text-sm text-slate-400"
        >
          <template v-if="tile.status === 'processing'">
            <PhSpinnerGap :size="24" class="animate-spin text-slate-300" />
            <p>Processing your clip</p>
          </template>
          <template v-else>
            <PhWarningCircle :size="24" class="text-red-400" />
            <p>This clip couldn't be processed</p>
          </template>
        </div>
        <div
          v-else-if="tile.kind === 'text'"
          class="absolute inset-0 flex items-center bg-linear-to-br px-4 pt-10 pb-14"
          :class="gradientOf(post)"
        >
          <p
            class="line-clamp-5 text-base font-semibold wrap-break-word whitespace-pre-line text-white"
          >
            {{ tile.text }}
          </p>
        </div>
        <template v-else-if="tile.kind === 'cover'">
          <img
            :src="tile.src"
            alt=""
            loading="lazy"
            class="absolute inset-0 size-full object-cover"
          />
          <div class="absolute inset-0 bg-black/30" />
        </template>
        <div
          v-else
          class="absolute inset-0 flex items-center justify-center bg-linear-to-br"
          :class="gradientOf(post)"
        >
          <PhGameController :size="40" class="text-white/30" />
        </div>
        <UBadge
          color="neutral"
          variant="solid"
          size="sm"
          class="absolute top-2 left-2 rounded-full bg-black/50 text-xs"
        >
          {{ post.category }}
        </UBadge>
        <div
          class="absolute inset-x-0 bottom-0 flex items-center justify-between gap-2 bg-linear-to-t from-black/70 to-transparent p-2.5"
        >
          <div class="flex min-w-0 items-center gap-1.5">
            <UAvatar
              :src="resolveAvatarUrl(post.authorId, post.avatarUrl)"
              size="sm"
              class="shrink-0 bg-white/10 text-slate-300"
            >
              <PhUserCircle :size="20" />
            </UAvatar>
            <span class="truncate text-sm font-medium text-white">{{ post.author }}</span>
          </div>
          <span class="flex shrink-0 items-center gap-1 text-sm text-white">
            <PhHeart :size="14" weight="fill" class="text-red-400" />
            {{ formatCount(post.likes) }}
          </span>
        </div>
      </router-link>
    </div>
  </div>
</template>
