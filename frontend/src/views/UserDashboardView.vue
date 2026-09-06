<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@nuxt/ui/composables/useToast'
import {
  PhCamera,
  PhChatCircleDots,
  PhClockAfternoon,
  PhCurrencyDollar,
  PhFilmSlate,
  PhGameController,
  PhPencilSimple,
  PhSmiley,
  PhUserCircle,
} from '@phosphor-icons/vue'
import { useAuthStore } from '@/stores/auth'
import { useFeedStore, type FeedPost } from '@/stores/feed'
import FeedLayout from '@/components/feed/FeedLayout.vue'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import FeedPostSkeleton from '@/components/feed/FeedPostSkeleton.vue'
import FeedPostThread from '@/components/feed/FeedPostThread.vue'
import FollowListPanel from '@/components/feed/FollowListPanel.vue'
import CreatePostModal from '@/components/modals/CreatePostModal.vue'
import { resolveAvatarUrl } from '@/utils/avatar'
import { formatTimeAgo } from '@/utils/timeAgo'

const router = useRouter()
const authStore = useAuthStore()
const feedStore = useFeedStore()
const toast = useToast()

const avatarUrl = computed(() => resolveAvatarUrl(authStore.user?.id ?? '', null))

const perks = [
  { icon: PhCurrencyDollar, label: 'Set your own rates', description: 'Price every service the way you want, per game or per hour.' },
  { icon: PhClockAfternoon, label: 'Play on your schedule', description: 'Go online whenever you have time, pause anytime.' },
  { icon: PhChatCircleDots, label: 'Chat before you play', description: 'Buyers message you first, no surprises when a session starts.' },
]

function formatCount(count: number) {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`
}

const postsLoading = ref(true)
const posts = ref<FeedPost[]>([])

onMounted(async () => {
  const userId = authStore.user?.id
  if (!userId) {
    postsLoading.value = false
    return
  }
  try {
    posts.value = await feedStore.fetchAuthorPosts(userId)
  } catch {
    posts.value = []
  } finally {
    postsLoading.value = false
  }
})

const createPostOpen = ref(false)

const activePostId = ref<string | null>(null)

const followListTab = ref<'followers' | 'following' | null>(null)

const editingPost = ref<FeedPost | null>(null)
const editModalOpen = ref(false)

function openEdit(post: FeedPost) {
  editingPost.value = post
  editModalOpen.value = true
}

function onPostUpdated(updated: FeedPost) {
  const index = posts.value.findIndex((p) => p.id === updated.id)
  if (index !== -1) posts.value[index] = updated
}

async function toggleLike(post: FeedPost) {
  try {
    const updated = await feedStore.toggleLike(post)
    const index = posts.value.findIndex((p) => p.id === updated.id)
    if (index !== -1) posts.value[index] = updated
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
  <FeedLayout active="profile">
    <FeedPostThread v-if="activePostId" :post-id="activePostId" @back="activePostId = null" />

    <FollowListPanel
      v-else-if="followListTab && authStore.user"
      :key="followListTab"
      :user-id="authStore.user.id"
      :initial-tab="followListTab"
      @back="followListTab = null"
    />

    <template v-else>
      <div class="rounded-xl bg-gray-800/70 p-5">
        <div class="flex items-start gap-4">
          <UAvatar :src="avatarUrl" size="3xl" class="shrink-0 bg-white/10 text-slate-300">
            <PhUserCircle :size="40" />
          </UAvatar>
          <div>
            <h1 class="text-2xl font-bold text-white">{{ authStore.user?.displayName ?? 'Account' }}</h1>
            <p v-if="authStore.user?.handle" class="mt-1 text-sm text-slate-400">{{ authStore.user.handle }}</p>
          </div>
        </div>

        <div class="mt-5 grid w-full max-w-xs grid-cols-3 divide-x divide-white/10 border-t border-white/10 pt-4">
          <div class="pr-4">
            <p class="font-semibold text-white">{{ formatCount(authStore.user?.postsCount ?? 0) }}</p>
            <p class="text-xs text-slate-400">Posts</p>
          </div>
          <button
            type="button"
            class="block w-full px-4 text-left transition-opacity hover:opacity-80"
            @click="followListTab = 'followers'"
          >
            <p class="font-semibold text-white">{{ formatCount(authStore.user?.followersCount ?? 0) }}</p>
            <p class="text-xs text-slate-400">Followers</p>
          </button>
          <button
            type="button"
            class="block w-full pl-4 text-left transition-opacity hover:opacity-80"
            @click="followListTab = 'following'"
          >
            <p class="font-semibold text-white">{{ formatCount(authStore.user?.followingCount ?? 0) }}</p>
            <p class="text-xs text-slate-400">Following</p>
          </button>
        </div>
      </div>

      <div class="flex items-center justify-between gap-4 rounded-xl bg-linear-to-br from-brand-900/50 to-squadup-bg p-4">
        <div>
          <span class="inline-flex items-center gap-1.5 rounded-full bg-brand-900/60 px-3 py-1 text-xs font-medium text-brand-300 ring-1 ring-inset ring-brand-700">
            <PhGameController :size="14" weight="fill" />
            Become a Pal
          </span>
          <p class="mt-2 text-sm text-slate-300">Turn your game time into Squad Coin. Set your own rates and get discovered by buyers.</p>
        </div>
        <UButton color="primary" class="shrink-0 rounded-full px-5" @click="router.push('/become-player')">
          Become a Pal
        </UButton>
      </div>
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div v-for="perk in perks" :key="perk.label" class="rounded-xl bg-linear-to-br from-brand-900/50 to-squadup-bg p-3">
          <div class="flex items-center gap-2 mb-2">
            <component :is="perk.icon" :size="20" class="text-brand-300" />
            <p class="text-xs font-semibold text-white">{{ perk.label }}</p>
          </div>
          <p class="mt-0.5 text-xs text-slate-400">{{ perk.description }}</p>
        </div>
      </div>

      <div class="rounded-xl bg-gray-800/70 p-4">
        <div class="flex items-center gap-3">
          <UAvatar :src="avatarUrl" size="md" class="shrink-0 bg-white/10 text-slate-300">
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
      <CreatePostModal v-model:open="editModalOpen" :post="editingPost" @updated="onPostUpdated" />

      <template v-if="postsLoading">
        <FeedPostSkeleton v-for="n in 3" :key="n" />
      </template>
      <template v-else>
        <p v-if="posts.length === 0" class="py-10 text-center text-sm text-slate-400">
          You haven't posted anything yet.
        </p>
        <FeedPostCard
          v-for="post in posts"
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
          <template v-if="post.kind !== 'status'" #action>
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
  </FeedLayout>
</template>
