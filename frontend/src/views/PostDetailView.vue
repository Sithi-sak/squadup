<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhCaretDown, PhCaretLeft, PhUserCircle } from '@phosphor-icons/vue'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import FeedCommentItem from '@/components/feed/FeedCommentItem.vue'
import { findFeedPost, mockPostComments } from '@/mocks/feed'

const route = useRoute()
const router = useRouter()

const postId = computed(() => String(route.params.postId))
const post = computed(() => findFeedPost(postId.value))

const following = ref(false)

const sort = ref<'top' | 'newest'>('top')
const sortItems = [
  [
    { label: 'Top', onSelect: () => (sort.value = 'top') },
    { label: 'Newest', onSelect: () => (sort.value = 'newest') },
  ],
]

function parseHoursAgo(timeAgo: string) {
  const match = /^(\d+)h$/.exec(timeAgo)
  return match ? Number(match[1]) : Number.POSITIVE_INFINITY
}

const comments = computed(() => {
  const list = [...(mockPostComments[postId.value] ?? [])]
  return sort.value === 'top'
    ? list.sort((a, b) => b.likes - a.likes)
    : list.sort((a, b) => parseHoursAgo(a.timeAgo) - parseHoursAgo(b.timeAgo))
})

const newComment = ref('')
const draftComments = reactive<{ id: string; author: string; timeAgo: string; text: string; likes: number }[]>([])

function postComment() {
  const text = newComment.value.trim()
  if (!text) return
  draftComments.unshift({
    id: `draft-${Date.now()}`,
    author: 'You',
    timeAgo: 'now',
    text,
    likes: 0,
  })
  newComment.value = ''
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
          :time-ago="post.timeAgo"
          :text="post.text"
          :has-image="post.hasImage"
          :likes="post.likes"
          :comments="post.comments"
        >
          <template #action>
            <UButton
              :color="following ? 'neutral' : 'primary'"
              :variant="following ? 'soft' : 'solid'"
              size="sm"
              class="rounded-full"
              @click="following = !following"
            >
              {{ following ? 'Following' : 'Follow' }}
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
          <UAvatar size="md" class="shrink-0 bg-white/10 text-slate-300">
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
          v-if="draftComments.length === 0 && comments.length === 0"
          title="No comments yet"
          description="Be the first to share your thoughts."
          class="py-12 text-white"
        />
        <div v-else class="flex flex-col gap-4">
          <FeedCommentItem
            v-for="comment in draftComments"
            :key="comment.id"
            :id="comment.id"
            :author="comment.author"
            :time-ago="comment.timeAgo"
            :text="comment.text"
            :likes="comment.likes"
          />
          <FeedCommentItem
            v-for="comment in comments"
            :key="comment.id"
            :id="comment.id"
            :author="comment.author"
            :time-ago="comment.timeAgo"
            :text="comment.text"
            :likes="comment.likes"
            :is-creator="comment.isCreator"
            :replies="comment.replies"
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
