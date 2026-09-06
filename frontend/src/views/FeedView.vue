<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { PhCamera, PhFilmSlate, PhSmiley, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import FeedLayout from '@/components/feed/FeedLayout.vue'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import CreatePostModal from '@/components/modals/CreatePostModal.vue'
import { useFeedStore, type FeedPost } from '@/stores/feed'
import { formatTimeAgo } from '@/utils/timeAgo'
import { mockCurrentUser } from '@/mocks/users'
import { useAuthStore } from '@/stores/auth'
import { usePlayersStore } from '@/stores/players'
import { resolveAvatarUrl } from '@/utils/avatar'

const feedStore = useFeedStore()
const authStore = useAuthStore()
const playersStore = usePlayersStore()
const toast = useToast()
const composerAvatarUrl = computed(() =>
  resolveAvatarUrl(authStore.user?.id ?? mockCurrentUser.id, playersStore.mine?.avatarUrl),
)

onMounted(() => {
  feedStore.fetchFeed()
})

const createPostOpen = ref(false)

async function toggleFollow(post: FeedPost) {
  try {
    await feedStore.toggleFollow(post.authorId, post.following)
  } catch (err) {
    toast.add({
      title: post.following ? 'Could not unfollow' : 'Could not follow',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}

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
  <FeedLayout active="feed">
    <div class="rounded-xl bg-gray-800/70 p-4">
      <div class="flex items-center gap-3">
        <UAvatar :src="composerAvatarUrl" size="md" class="shrink-0 bg-white/10 text-slate-300">
          <PhUserCircle :size="20" />
        </UAvatar>
        <UInput
          placeholder="Share something with your squad..."
          variant="subtle"
          class="w-full rounded-full"
          :ui="{ base: 'rounded-full cursor-pointer' }"
          readonly
          @click="createPostOpen = true"
        />
      </div>
      <div class="mt-3 flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full" @click="createPostOpen = true">
            <PhCamera :size="16" weight="bold" />
            Photo
          </UButton>
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full" @click="createPostOpen = true">
            <PhFilmSlate :size="16" weight="bold" />
            Clip
          </UButton>
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full" @click="createPostOpen = true">
            <PhSmiley :size="16" weight="bold" />
            Emoji
          </UButton>
        </div>
        <UButton color="primary" class="rounded-full px-6" @click="createPostOpen = true">Post</UButton>
      </div>
    </div>

    <CreatePostModal v-model:open="createPostOpen" />

    <FeedPostCard
      v-for="post in feedStore.posts"
      :key="post.id"
      :id="post.id"
      :author="post.author"
      :handle="post.handle"
      :tier="post.tier"
      :time-ago="formatTimeAgo(post.createdAt)"
      :text="post.text ?? ''"
      :has-image="post.hasImage"
      :likes="post.likes"
      :comments="post.comments"
      :liked="post.liked"
      @toggle-like="toggleLike(post)"
    >
      <template #action>
        <UButton
          :color="post.following ? 'neutral' : 'primary'"
          :variant="post.following ? 'soft' : 'solid'"
          size="sm"
          class="rounded-full"
          @click="toggleFollow(post)"
        >
          {{ post.following ? 'Following' : 'Follow' }}
        </UButton>
      </template>
    </FeedPostCard>
  </FeedLayout>
</template>
