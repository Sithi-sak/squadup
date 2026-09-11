<script setup lang="ts">
import { computed, onActivated, ref } from 'vue'
import { PhCamera, PhFilmSlate, PhPencilSimple, PhSmiley, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import FeedPostSkeleton from '@/components/feed/FeedPostSkeleton.vue'
import FeedPostThread from '@/components/feed/FeedPostThread.vue'
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
const currentUserId = computed(() => authStore.user?.id ?? mockCurrentUser.id)
const composerAvatarUrl = computed(() => resolveAvatarUrl(currentUserId.value, playersStore.mine?.avatarUrl))

onActivated(() => {
  feedStore.fetchFeed()
})

const createPostOpen = ref(false)

const activePostId = ref<string | null>(null)

const editingPost = ref<FeedPost | null>(null)
const editModalOpen = ref(false)

function openEdit(post: FeedPost) {
  editingPost.value = post
  editModalOpen.value = true
}

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
  <div class="flex min-w-0 flex-col gap-4">
    <FeedPostThread v-if="activePostId" :post-id="activePostId" @back="activePostId = null" />

    <template v-else>
      <div class="rounded-xl bg-gray-800/50 p-4">
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
      <CreatePostModal v-model:open="editModalOpen" :post="editingPost" />

      <template v-if="feedStore.postsLoading">
        <FeedPostSkeleton v-for="n in 3" :key="n" />
      </template>

      <template v-else>
        <FeedPostCard
          v-for="post in feedStore.posts"
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
          <template v-if="post.authorId !== currentUserId" #action>
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
          <template v-else-if="post.kind !== 'status'" #action>
            <UButton
              color="neutral"
              variant="ghost"
              square
              :ui="{ base: 'rounded-full' }"
              aria-label="Edit post"
              @click="openEdit(post)"
            >
              <PhPencilSimple :size="16" />
            </UButton>
          </template>
        </FeedPostCard>
      </template>
    </template>
  </div>
</template>
