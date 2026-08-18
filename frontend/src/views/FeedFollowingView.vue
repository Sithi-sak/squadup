<script setup lang="ts">
import { computed, ref } from 'vue'
import FeedLayout from '@/components/feed/FeedLayout.vue'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import { mockFollowingPosts } from '@/mocks/feed'

const filters = [
  { key: 'all', label: 'All' },
  { key: 'online', label: 'Online now' },
  { key: 'games', label: 'Games' },
  { key: 'chilling', label: 'Chilling' },
  { key: 'clips', label: 'Clips' },
] as const

const activeFilter = ref<(typeof filters)[number]['key']>('all')

const visiblePosts = computed(() => {
  if (activeFilter.value === 'all') return mockFollowingPosts
  if (activeFilter.value === 'online') return mockFollowingPosts.filter((p) => p.online)
  return mockFollowingPosts.filter((p) => p.category === activeFilter.value)
})
</script>

<template>
  <FeedLayout active="following" show-create-post>
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

    <p v-if="visiblePosts.length === 0" class="py-16 text-center text-sm text-slate-400">
      No posts from Pals you follow match this filter yet.
    </p>

    <FeedPostCard
      v-for="post in visiblePosts"
      :key="post.id"
      :id="post.id"
      :author="post.author"
      :handle="post.handle"
      :tier="post.tier"
      :time-ago="post.timeAgo"
      :text="post.text"
      :has-image="post.hasImage"
      :likes="post.likes"
      :comments="post.comments"
    >
      <template #action>
        <UButton color="neutral" variant="soft" size="sm" class="rounded-full">Following</UButton>
      </template>
    </FeedPostCard>
  </FeedLayout>
</template>
