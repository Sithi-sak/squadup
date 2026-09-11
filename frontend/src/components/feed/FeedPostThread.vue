<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { PhCaretDown, PhCaretLeft, PhCloudWarning, PhPencilSimple, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import CreatePostModal from '@/components/modals/CreatePostModal.vue'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import FeedPostSkeleton from '@/components/feed/FeedPostSkeleton.vue'
import FeedCommentItem from '@/components/feed/FeedCommentItem.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useFeedStore, type FeedComment, type FeedPost } from '@/stores/feed'
import { findFeedPost, type FeedPostDetail } from '@/mocks/feed'
import { formatTimeAgo } from '@/utils/timeAgo'
import { mockCurrentUser } from '@/mocks/users'
import { useAuthStore } from '@/stores/auth'
import { usePlayersStore } from '@/stores/players'
import { resolveAvatarUrl } from '@/utils/avatar'

const props = defineProps<{ postId: string }>()
const emit = defineEmits<{ back: [] }>()

const feedStore = useFeedStore()
const authStore = useAuthStore()
const playersStore = usePlayersStore()
const toast = useToast()
const currentUserId = computed(() => authStore.user?.id ?? mockCurrentUser.id)
const composerAvatarUrl = computed(() => resolveAvatarUrl(currentUserId.value, playersStore.mine?.avatarUrl))

const post = ref<FeedPost | null>(null)
const postLoading = ref(true)

/** Adapts `findFeedPost`'s thinner mock shape into a `FeedPost` for the fallback path, same
 * "adapt at the boundary" approach `stores/feed.ts`'s `feedPostFromMock` uses. */
function postFromMockDetail(detail: FeedPostDetail): FeedPost {
  return {
    id: detail.id,
    authorId: detail.id,
    author: detail.author,
    handle: detail.handle,
    tier: detail.tier,
    playerId: null,
    avatarUrl: null,
    online: false,
    text: detail.text,
    hasImage: detail.hasImage,
    imageUrl: null,
    category: 'games',
    kind: 'user',
    likes: detail.likes,
    comments: detail.comments,
    liked: false,
    following: false,
    createdAt: new Date().toISOString(),
  }
}

/** Prefers a post already loaded by Feed/Following (`feedStore.getPost`), then `GET
 * /feed/posts/{id}` for a direct/deep link, then the mock fixtures - same resilience pattern as
 * `OrderDetailView.vue`'s `loadBooking`. */
async function loadPost() {
  postLoading.value = true
  const id = props.postId
  const existing = feedStore.getPost(id)
  if (existing) {
    post.value = existing
    postLoading.value = false
    return
  }
  try {
    post.value = await feedStore.fetchPost(id)
  } catch {
    const detail = findFeedPost(id)
    post.value = detail ? postFromMockDetail(detail) : null
  } finally {
    postLoading.value = false
  }
}

function load() {
  loadPost()
  feedStore.fetchComments(props.postId)
}

onMounted(load)
watch(() => props.postId, load)

const editModalOpen = ref(false)

const sort = ref<'top' | 'newest'>('top')
const sortItems = [
  [
    { label: 'Top', onSelect: () => (sort.value = 'top') },
    { label: 'Newest', onSelect: () => (sort.value = 'newest') },
  ],
]

const comments = computed(() => {
  const list = [...(feedStore.commentsByPost[props.postId] ?? [])]
  return sort.value === 'top'
    ? list.sort((a, b) => b.likes - a.likes)
    : list.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
})

const newComment = ref('')
const posting = ref(false)

async function postComment() {
  if (posting.value) return
  const text = newComment.value.trim()
  if (!text) return
  posting.value = true
  try {
    await feedStore.postComment(props.postId, text)
    newComment.value = ''
  } catch (err) {
    toast.add({
      title: 'Could not post comment',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    posting.value = false
  }
}

async function toggleCommentLike(comment: FeedComment) {
  try {
    await feedStore.toggleCommentLike(props.postId, comment)
  } catch (err) {
    toast.add({
      title: 'Could not update like',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}

async function toggleFollow() {
  if (!post.value) return
  try {
    const result = await feedStore.toggleFollow(post.value.authorId, post.value.following)
    post.value.following = result.following
  } catch (err) {
    toast.add({
      title: post.value.following ? 'Could not unfollow' : 'Could not follow',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}

async function toggleLike() {
  if (!post.value) return
  try {
    post.value = await feedStore.toggleLike(post.value)
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
  <div class="flex flex-col gap-5">
    <button
      type="button"
      class="flex w-fit items-center gap-1 text-sm text-slate-400 transition-colors hover:text-white"
      @click="emit('back')"
    >
      <PhCaretLeft :size="16" weight="bold" />
      Back to feed
    </button>

    <FeedPostSkeleton v-if="postLoading" />

    <template v-else-if="post">
      <FeedPostCard
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
        @toggle-like="toggleLike"
      >
        <template v-if="post.authorId !== currentUserId" #action>
          <UButton
            :color="post.following ? 'neutral' : 'primary'"
            :variant="post.following ? 'soft' : 'solid'"
            size="sm"
            class="rounded-full"
            @click="toggleFollow"
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
            @click="editModalOpen = true"
          >
            <PhPencilSimple :size="16" />
          </UButton>
        </template>
      </FeedPostCard>

      <CreatePostModal v-model:open="editModalOpen" :post="post" @updated="post = $event" />

      <div class="flex items-center justify-between">
        <h2 class="text-lg font-bold text-white">Comments</h2>
        <UDropdownMenu :items="sortItems">
          <button type="button" class="flex items-center gap-1 text-sm text-slate-400 hover:text-white">
            {{ sort === 'top' ? 'Top' : 'Newest' }}
            <PhCaretDown :size="14" />
          </button>
        </UDropdownMenu>
      </div>

      <div class="flex items-center gap-3">
        <UAvatar :src="composerAvatarUrl" size="md" class="shrink-0 bg-white/10 text-slate-300">
          <PhUserCircle :size="20" />
        </UAvatar>
        <UInput
          v-model="newComment"
          placeholder="Add a comment..."
          variant="subtle"
          class="w-full rounded-full"
          :ui="{ base: 'rounded-full' }"
          :disabled="posting"
          @keyup.enter="postComment"
        />
        <UButton
          color="primary"
          class="shrink-0 rounded-full px-6"
          :loading="posting"
          :disabled="posting"
          @click="postComment"
        >
          Post
        </UButton>
      </div>

      <p v-if="comments.length === 0" class="py-10 text-center text-sm text-slate-400">
        No comments yet. Be the first to share your thoughts.
      </p>
      <div v-else class="flex flex-col gap-4">
        <FeedCommentItem
          v-for="comment in comments"
          :key="comment.id"
          :comment="comment"
          @toggle-like="toggleCommentLike"
        />
      </div>
    </template>

    <EmptyState
      v-else
      :icon="PhCloudWarning"
      badge="Not found"
      title="Post not found"
      description="This post may have been removed."
      class="py-16"
    />
  </div>
</template>
