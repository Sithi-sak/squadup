<script setup lang="ts">
import { computed, onActivated, ref } from 'vue'
import { PhBookmarkSimple } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import coinIcon from '@/assets/squadup-coin.svg'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import FeedPostThread from '@/components/feed/FeedPostThread.vue'
import { useFeedStore, type FeedPost, type FeedSavedItem } from '@/stores/feed'
import { formatTimeAgo } from '@/utils/timeAgo'

const feedStore = useFeedStore()
const toast = useToast()

onActivated(() => {
  feedStore.fetchSaved()
})

const filters = [
  { key: 'all', label: 'All' },
  { key: 'post', label: 'Posts' },
  { key: 'clip', label: 'Clips' },
  { key: 'service', label: 'Services' },
  { key: 'pal', label: 'Pals' },
] as const

const activeFilter = ref<(typeof filters)[number]['key']>('all')
const activePostId = ref<string | null>(null)

const visibleItems = computed(() => {
  if (activeFilter.value === 'all') return feedStore.saved
  return feedStore.saved.filter((item) => savedFilterKey(item) === activeFilter.value)
})

/** Saved rows are only ever `post` or `service`; a post with a clip files under Clips. */
function savedFilterKey(item: FeedSavedItem) {
  if (item.kind === 'post' && item.post?.videoUrl) return 'clip'
  return item.kind
}

async function toggleLike(post: FeedPost | null | undefined) {
  if (!post) return
  try {
    await feedStore.toggleLike(post)
  } catch (err) {
    toast.add({
      title: 'Could not update like',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}

async function unsave(item: FeedSavedItem) {
  try {
    await feedStore.toggleSaved(item.kind, (item.kind === 'post' ? item.postId : item.serviceId) ?? item.id)
  } catch (err) {
    toast.add({
      title: 'Could not unsave',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}
</script>

<template>
  <div class="flex min-w-0 flex-col gap-4">
    <FeedPostThread v-if="activePostId" :post-id="activePostId" @back="activePostId = null" />

    <template v-else>
      <div>
        <h1 class="text-2xl font-bold text-white">Saved</h1>
        <p class="mt-1 text-sm text-slate-400">Your bookmarked posts, clips, Pals and services</p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <UButton
          v-for="filter in filters"
          :key="filter.key"
          :color="activeFilter === filter.key ? 'primary' : 'neutral'"
          :variant="activeFilter === filter.key ? 'solid' : 'soft'"
          size="sm"
          class="rounded-full"
          @click="activeFilter = filter.key"
        >
          {{ filter.label }}
        </UButton>
      </div>

      <UEmpty v-if="visibleItems.length === 0" title="Nothing saved here yet" class="py-16 text-white" />

      <template v-for="item in visibleItems" :key="item.id">
        <FeedPostCard
          v-if="item.kind === 'post' && item.post"
          :id="item.post.id"
          :author-id="item.post.authorId"
          :author="item.post.author"
          :avatar-url="item.post.avatarUrl"
          :handle="item.post.handle"
          :tier="item.post.tier"
          :player-id="item.post.playerId"
          :time-ago="formatTimeAgo(item.post.createdAt)"
          :text="item.post.text ?? ''"
          :has-image="item.post.hasImage"
          :image-url="item.post.imageUrl"
          :image-urls="item.post.imageUrls"
          :video-url="item.post.videoUrl"
          :video-poster-url="item.post.videoPosterUrl"
          :video-status="item.post.videoStatus"
          :tag="item.post.tag"
          :likes="item.post.likes"
          :comments="item.post.comments"
          :liked="item.post.liked"
          :kind="item.post.kind"
          @toggle-like="toggleLike(item.post)"
          @open-comments="activePostId = item.post?.id ?? item.postId ?? null"
        />

        <FeedPostCard
          v-else-if="item.kind === 'post'"
          :id="item.postId ?? item.id"
          :author-id="item.authorId"
          :author="item.author ?? ''"
          :avatar-url="item.avatarUrl"
          :handle="item.handle ?? ''"
          :tier="item.tier"
          :player-id="item.playerId"
          :time-ago="formatTimeAgo(item.createdAt)"
          :text="item.text ?? ''"
          :has-image="item.hasImage ?? false"
          :likes="item.likes ?? 0"
          :comments="item.comments ?? 0"
          @open-comments="activePostId = item.postId ?? item.id"
        />

        <div v-else class="flex items-center gap-4 rounded-xl bg-gray-800/70 p-4">
          <div class="h-16 w-16 shrink-0 rounded-lg bg-white/5 ring-1 ring-inset ring-white/10" />
          <div class="min-w-0 flex-1">
            <p class="truncate font-semibold text-white">{{ item.name }}</p>
            <p class="truncate text-sm text-slate-400">by {{ item.by }} · {{ item.category }}</p>
            <p class="mt-1 flex items-center gap-1 text-sm text-slate-300">
              <img :src="coinIcon" alt="" class="h-4 w-4" />
              {{ item.priceCoins }} {{ item.priceUnit }}
              <span v-if="item.promoLabel" class="text-brand-400">· {{ item.promoLabel }}</span>
            </p>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <UButton
              color="neutral"
              variant="ghost"
              square
              :ui="{ base: 'rounded-full' }"
              aria-label="Unsave"
              @click="unsave(item)"
            >
              <PhBookmarkSimple :size="18" weight="fill" class="text-brand-400" />
            </UButton>
            <UButton color="primary" size="sm" class="rounded-full">Book</UButton>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>
