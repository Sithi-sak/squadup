<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhCaretDown, PhCaretLeft, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import FeedCommentItem from '@/components/feed/FeedCommentItem.vue'
import { useFeedStore, type FeedComment, type FeedPost } from '@/stores/feed'
import { findFeedPost, type FeedPostDetail } from '@/mocks/feed'
import { formatTimeAgo } from '@/utils/timeAgo'
import { mockCurrentUser } from '@/mocks/users'
import { useAuthStore } from '@/stores/auth'
import { usePlayersStore } from '@/stores/players'
import { resolveAvatarUrl } from '@/utils/avatar'

const route = useRoute()
const router = useRouter()
const feedStore = useFeedStore()
const authStore = useAuthStore()
const playersStore = usePlayersStore()
const toast = useToast()
const composerAvatarUrl = computed(() =>
  resolveAvatarUrl(authStore.user?.id ?? mockCurrentUser.id, playersStore.mine?.avatarUrl),
)

const postId = computed(() => String(route.params.postId))
const post = ref<FeedPost | null>(null)

/** Adapts `findFeedPost`'s thinner mock shape into a `FeedPost` for the fallback path, same
 * "adapt at the boundary" approach `stores/feed.ts`'s `feedPostFromMock` uses. */
function postFromMockDetail(detail: FeedPostDetail): FeedPost {
  return {
    id: detail.id,
    authorId: detail.id,
    author: detail.author,
    handle: detail.handle,
    tier: detail.tier,
    avatarUrl: null,
    online: false,
    text: detail.text,
    hasImage: detail.hasImage,
    category: 'games',
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
  const id = postId.value
  const existing = feedStore.getPost(id)
  if (existing) {
    post.value = existing
    return
  }
  try {
    post.value = await feedStore.fetchPost(id)
  } catch {
    const detail = findFeedPost(id)
    post.value = detail ? postFromMockDetail(detail) : null
  }
}

function load() {
  loadPost()
  feedStore.fetchComments(postId.value)
}

onMounted(load)
watch(() => route.params.postId, load)

const sort = ref<'top' | 'newest'>('top')
const sortItems = [
  [
    { label: 'Top', onSelect: () => (sort.value = 'top') },
    { label: 'Newest', onSelect: () => (sort.value = 'newest') },
  ],
]

const comments = computed(() => {
  const list = [...(feedStore.commentsByPost[postId.value] ?? [])]
  return sort.value === 'top'
    ? list.sort((a, b) => b.likes - a.likes)
    : list.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
})

const newComment = ref('')

async function postComment() {
  const text = newComment.value.trim()
  if (!text) return
  try {
    await feedStore.postComment(postId.value, text)
    newComment.value = ''
  } catch (err) {
    toast.add({
      title: 'Could not post comment',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}

async function toggleCommentLike(comment: FeedComment) {
  try {
    await feedStore.toggleCommentLike(postId.value, comment)
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
  <div class="min-h-[calc(100vh-4rem)] px-4 pt-8 pb-14 md:px-6">
    <div class="mx-auto flex max-w-2xl flex-col gap-5">
      <button
        type="button"
        class="flex w-fit items-center gap-1 text-sm text-slate-400 transition-colors hover:text-white"
        @click="router.push('/feed')"
      >
        <PhCaretLeft :size="16" weight="bold" />
        Back to feed
      </button>

      <template v-if="post">
        <FeedPostCard
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
          @toggle-like="toggleLike"
        >
          <template #action>
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
        </FeedPostCard>

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
            @keyup.enter="postComment"
          />
          <UButton color="primary" class="shrink-0 rounded-full px-6" @click="postComment">Post</UButton>
        </div>

        <UEmpty
          v-if="comments.length === 0"
          title="No comments yet"
          description="Be the first to share your thoughts."
          class="py-12 text-white"
        />
        <div v-else class="flex flex-col gap-4">
          <FeedCommentItem
            v-for="comment in comments"
            :key="comment.id"
            :comment="comment"
            @toggle-like="toggleCommentLike"
          />
        </div>
      </template>

      <UEmpty
        v-else
        title="Post not found"
        description="This post may have been removed."
        class="py-16 text-white"
      />
    </div>
  </div>
</template>
