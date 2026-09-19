<script setup lang="ts">
import { ref, watch } from 'vue'
import { PhCamera, PhFilmSlate, PhSmiley, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import CreatePostModal from '@/components/modals/CreatePostModal.vue'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import FeedPostThread from '@/components/feed/FeedPostThread.vue'
import SuggestedPalsCard from '@/components/feed/SuggestedPalsCard.vue'
import { useFeedStore, type FeedPost } from '@/stores/feed'
import type { PlayerSummary } from '@/stores/players'
import { formatTimeAgo } from '@/utils/timeAgo'
import { resolveAvatarUrl } from '@/utils/avatar'

/** `player` is narrowed to what this component actually renders so the buyer profile page
 * (`MyProfileView.vue`), which has no player row to pass, can reuse it. */
const props = defineProps<{
  player: Pick<PlayerSummary, 'id' | 'displayName' | 'avatarUrl'>
  handle: string | null
  feed: FeedPost[]
  isOwnProfile?: boolean
}>()

/** Re-emitted for the own-profile pages that show a post count in their own header
 * (`MyProfileView`) - the tab owns the composer, but not the header. */
const emit = defineEmits<{ created: [post: FeedPost] }>()

const feedStore = useFeedStore()
const toast = useToast()

/** Local copy so a like toggle can patch in place without the parent's `profile.feed` (loaded
 * once via `usePlayerProfileData`) needing its own mutation path. */
const localFeed = ref<FeedPost[]>([...props.feed])
watch(
  () => props.feed,
  (feed) => (localFeed.value = [...feed]),
)

const createPostOpen = ref(false)
const activePostId = ref<string | null>(null)

function onPostCreated(post: FeedPost) {
  localFeed.value.unshift(post)
  emit('created', post)
}

async function toggleLike(post: FeedPost) {
  try {
    const updated = await feedStore.toggleLike(post)
    const index = localFeed.value.findIndex((p) => p.id === updated.id)
    if (index !== -1) localFeed.value[index] = updated
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
  <div
    class="grid grid-cols-1 gap-4 lg:items-start"
    :class="$slots.aside ? 'lg:grid-cols-[280px_1fr_300px]' : 'lg:grid-cols-[1fr_300px]'"
  >
    <div v-if="$slots.aside" class="hidden lg:block">
      <slot name="aside" />
    </div>

    <div class="flex flex-col gap-4">
      <FeedPostThread
        v-if="activePostId"
        :post-id="activePostId"
        @back="activePostId = null"
        @deleted="localFeed = localFeed.filter((p) => p.id !== $event)"
      />

      <template v-else>
        <div v-if="isOwnProfile" class="rounded-xl bg-gray-800/70 p-4">
          <div class="flex items-center gap-3">
            <UAvatar
              :src="resolveAvatarUrl(player.id, player.avatarUrl)"
              size="md"
              class="shrink-0 bg-white/10 text-slate-300"
            >
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
              <UButton
                color="neutral"
                variant="soft"
                size="sm"
                class="rounded-full"
                @click="createPostOpen = true"
              >
                <PhCamera :size="16" weight="bold" />
                Photo
              </UButton>
              <UButton
                color="neutral"
                variant="soft"
                size="sm"
                class="rounded-full"
                @click="createPostOpen = true"
              >
                <PhFilmSlate :size="16" weight="bold" />
                Clip
              </UButton>
              <UButton
                color="neutral"
                variant="soft"
                size="sm"
                class="rounded-full"
                @click="createPostOpen = true"
              >
                <PhSmiley :size="16" weight="bold" />
                Emoji
              </UButton>
            </div>
            <UButton color="primary" class="rounded-full px-6" @click="createPostOpen = true"
              >Post</UButton
            >
          </div>
        </div>

        <CreatePostModal
          v-if="isOwnProfile"
          v-model:open="createPostOpen"
          @created="onPostCreated"
        />

        <p v-if="localFeed.length === 0" class="py-10 text-center text-sm text-slate-400">
          {{ isOwnProfile ? "You haven't" : `${player.displayName} hasn't` }} posted anything yet.
        </p>

        <FeedPostCard
          v-for="post in localFeed"
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
          :image-urls="post.imageUrls"
          :tag="post.tag"
          :likes="post.likes"
          :comments="post.comments"
          :liked="post.liked"
          :kind="post.kind"
          @toggle-like="toggleLike(post)"
          @open-comments="activePostId = post.id"
        />
      </template>
    </div>

    <div class="hidden lg:sticky lg:top-20 lg:block">
      <SuggestedPalsCard />
    </div>
  </div>
</template>
