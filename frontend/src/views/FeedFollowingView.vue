<script setup lang="ts">
import { computed, onActivated, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@nuxt/ui/composables/useToast'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import FeedPostSkeleton from '@/components/feed/FeedPostSkeleton.vue'
import FeedPostThread from '@/components/feed/FeedPostThread.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useFeedStore, type FeedPost } from '@/stores/feed'
import { formatTimeAgo } from '@/utils/timeAgo'

const router = useRouter()
const feedStore = useFeedStore()
const toast = useToast()

onActivated(() => {
  feedStore.fetchFollowing()
})

const filters = [
  { key: 'all', label: 'All' },
  { key: 'online', label: 'Online now' },
  { key: 'games', label: 'Games' },
  { key: 'chilling', label: 'Chilling' },
  { key: 'clips', label: 'Clips' },
] as const

const activeFilter = ref<(typeof filters)[number]['key']>('all')
const activePostId = ref<string | null>(null)

const visiblePosts = computed(() => {
  if (activeFilter.value === 'all') return feedStore.following
  if (activeFilter.value === 'online') return feedStore.following.filter((p) => p.online)
  return feedStore.following.filter((p) => p.category === activeFilter.value)
})

async function toggleLike(post: FeedPost) {
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
</script>

<template>
  <div class="flex min-w-0 flex-col gap-4">
    <FeedPostThread v-if="activePostId" :post-id="activePostId" @back="activePostId = null" />

    <template v-else>
      <div class="flex flex-wrap items-center gap-2">
        <UButton
          v-for="filter in filters"
          :key="filter.key"
          :color="activeFilter === filter.key ? 'primary' : 'neutral'"
          :variant="activeFilter === filter.key ? 'solid' : 'soft'"
          size="md"
          class="rounded-full"
          @click="activeFilter = filter.key"
        >
          {{ filter.label }}
        </UButton>
      </div>

      <template v-if="feedStore.followingLoading">
        <FeedPostSkeleton v-for="n in 3" :key="n" />
      </template>

      <div v-else-if="feedStore.following.length === 0" class="rounded-xl bg-gray-800/70">
        <EmptyState
          badge="Quiet in here"
          title="Your feed is quiet"
          description="Follow Pals to see their posts, clips and updates, or share the first one."
        >
          <template #actions>
            <UButton color="primary" class="rounded-full px-6" @click="router.push('/players')">
              Discover Pals
            </UButton>
            <UButton color="neutral" variant="soft" class="rounded-full px-6">Create a post</UButton>
          </template>
        </EmptyState>
      </div>
      <p v-else-if="visiblePosts.length === 0" class="py-16 text-center text-sm text-slate-400">
        No posts from Pals you follow match this filter yet.
      </p>

      <template v-else>
        <FeedPostCard
          v-for="post in visiblePosts"
          :key="post.id"
          :id="post.id"
          :author-id="post.authorId"
          :author="post.author"
          :avatar-url="post.avatarUrl"
          :handle="post.handle"
          :tier="post.tier"
          :player-id="post.playerId"
          :time-ago="formatTimeAgo(post.createdAt)"
          :text="post.text ?? ''"
          :has-image="post.hasImage"
          :image-url="post.imageUrl"
          :likes="post.likes"
          :comments="post.comments"
          :liked="post.liked"
          :kind="post.kind"
          @toggle-like="toggleLike(post)"
          @open-comments="activePostId = post.id"
        >
          <template #action>
            <UButton color="neutral" variant="soft" size="sm" class="rounded-full">Following</UButton>
          </template>
        </FeedPostCard>
      </template>
    </template>
  </div>
</template>
