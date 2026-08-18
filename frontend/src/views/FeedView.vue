<script setup lang="ts">
import { reactive } from 'vue'
import { PhCamera, PhFilmSlate, PhSmiley, PhUserCircle } from '@phosphor-icons/vue'
import FeedLayout from '@/components/feed/FeedLayout.vue'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import { mockFeedPosts } from '@/mocks/feed'

const following = reactive<Record<string, boolean>>({})
function toggleFollow(id: string, current: boolean) {
  following[id] = !current
}
function isFollowing(post: { id: string; following: boolean }) {
  return following[post.id] ?? post.following
}
</script>

<template>
  <FeedLayout active="feed">
    <div class="rounded-xl bg-gray-800/70 p-4">
      <div class="flex items-center gap-3">
        <UAvatar size="md" class="shrink-0 bg-white/10 text-slate-300">
          <PhUserCircle :size="20" />
        </UAvatar>
        <UInput
          placeholder="Share something with your squad..."
          variant="subtle"
          class="w-full rounded-full"
          :ui="{ base: 'rounded-full' }"
        />
      </div>
      <div class="mt-3 flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full">
            <PhCamera :size="16" weight="bold" />
            Photo
          </UButton>
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full">
            <PhFilmSlate :size="16" weight="bold" />
            Clip
          </UButton>
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full">
            <PhSmiley :size="16" weight="bold" />
            Emoji
          </UButton>
        </div>
        <UButton color="primary" class="rounded-full px-6">Post</UButton>
      </div>
    </div>

    <FeedPostCard
      v-for="post in mockFeedPosts"
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
        <UButton
          :color="isFollowing(post) ? 'neutral' : 'primary'"
          :variant="isFollowing(post) ? 'soft' : 'solid'"
          size="sm"
          class="rounded-full"
          @click="toggleFollow(post.id, isFollowing(post))"
        >
          {{ isFollowing(post) ? 'Following' : 'Follow' }}
        </UButton>
      </template>
    </FeedPostCard>
  </FeedLayout>
</template>
