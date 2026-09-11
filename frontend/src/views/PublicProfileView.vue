<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhCloudWarning, PhUserCircle } from '@phosphor-icons/vue'
import { useAuthStore } from '@/stores/auth'
import { useFeedStore, type FeedPost } from '@/stores/feed'
import { useUsersStore, type PublicProfile } from '@/stores/users'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import FeedPostSkeleton from '@/components/feed/FeedPostSkeleton.vue'
import FeedPostThread from '@/components/feed/FeedPostThread.vue'
import FollowListPanel from '@/components/feed/FollowListPanel.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { resolveAvatarUrl } from '@/utils/avatar'
import { formatTimeAgo } from '@/utils/timeAgo'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const feedStore = useFeedStore()
const usersStore = useUsersStore()
const toast = useToast()

const userId = computed(() => String(route.params.id))

const loading = ref(true)
const profile = ref<PublicProfile | null>(null)
const posts = ref<FeedPost[]>([])

function formatCount(count: number) {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`
}

async function load() {
  const id = userId.value

  // Your own account has its own self-view page (no follow button, composer, ...) - which
  // forwards Pals on to `/players/{id}` in turn.
  if (id === authStore.user?.id) {
    router.replace({ name: 'my-profile' })
    return
  }

  loading.value = true
  profile.value = null
  posts.value = []
  try {
    profile.value = await usersStore.fetchPublicProfile(id)
    if (profile.value.playerId) {
      router.replace(`/players/${profile.value.playerId}`)
      return
    }
    posts.value = await feedStore.fetchAuthorPosts(id)
  } catch {
    profile.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(userId, load)

const followPending = ref(false)
async function toggleFollow() {
  if (!profile.value || followPending.value) return
  followPending.value = true
  try {
    const result = await feedStore.toggleFollow(profile.value.id, profile.value.following)
    profile.value = {
      ...profile.value,
      following: result.following,
      followersCount: result.followersCount,
    }
  } catch (err) {
    toast.add({
      title: profile.value.following ? 'Could not unfollow' : 'Could not follow',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    followPending.value = false
  }
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

const activePostId = ref<string | null>(null)
const followListTab = ref<'followers' | 'following' | null>(null)
</script>

<template>
  <div class="flex min-w-0 flex-col gap-4">
    <FeedPostThread v-if="activePostId" :post-id="activePostId" @back="activePostId = null" />

    <FollowListPanel
      v-else-if="followListTab && profile"
      :key="followListTab"
      :user-id="profile.id"
      :initial-tab="followListTab"
      @back="followListTab = null"
    />

    <template v-else-if="loading">
      <div class="rounded-xl bg-gray-800/70 p-5">
        <div class="flex items-start gap-4">
          <USkeleton class="h-20 w-20 shrink-0 rounded-full" />
          <div class="flex flex-col gap-2 pt-1">
            <USkeleton class="h-6 w-40" />
            <USkeleton class="h-4 w-28" />
          </div>
        </div>
      </div>
      <FeedPostSkeleton v-for="n in 3" :key="n" />
    </template>

    <EmptyState
      v-else-if="!profile"
      :icon="PhCloudWarning"
      badge="Not found"
      title="Profile not found"
      description="This account may no longer exist."
      class="py-16"
    />

    <template v-else>
      <div class="rounded-xl bg-gray-800/70 p-5">
        <div class="flex items-start justify-between gap-4">
          <div class="flex items-start gap-4">
            <UAvatar :src="resolveAvatarUrl(profile.id, profile.avatarUrl)" size="3xl" class="shrink-0 bg-white/10 text-slate-300">
              <PhUserCircle :size="40" />
            </UAvatar>
            <div>
              <h1 class="text-2xl font-bold text-white">{{ profile.displayName ?? 'SquadUp user' }}</h1>
              <p v-if="profile.handle" class="mt-1 text-sm text-slate-400">{{ profile.handle }}</p>
            </div>
          </div>

          <UButton
            v-if="authStore.user"
            :color="profile.following ? 'neutral' : 'primary'"
            :variant="profile.following ? 'soft' : 'solid'"
            class="shrink-0 rounded-full px-5"
            :loading="followPending"
            @click="toggleFollow"
          >
            {{ profile.following ? 'Following' : 'Follow' }}
          </UButton>
        </div>

        <div class="mt-5 grid w-full max-w-xs grid-cols-3 divide-x divide-white/10 border-t border-white/10 pt-4">
          <div class="pr-4">
            <p class="font-semibold text-white">{{ formatCount(profile.postsCount) }}</p>
            <p class="text-xs text-slate-400">Posts</p>
          </div>
          <button
            type="button"
            class="block w-full px-4 text-left transition-opacity hover:opacity-80"
            @click="followListTab = 'followers'"
          >
            <p class="font-semibold text-white">{{ formatCount(profile.followersCount) }}</p>
            <p class="text-xs text-slate-400">Followers</p>
          </button>
          <button
            type="button"
            class="block w-full pl-4 text-left transition-opacity hover:opacity-80"
            @click="followListTab = 'following'"
          >
            <p class="font-semibold text-white">{{ formatCount(profile.followingCount) }}</p>
            <p class="text-xs text-slate-400">Following</p>
          </button>
        </div>
      </div>

      <p v-if="posts.length === 0" class="py-10 text-center text-sm text-slate-400">
        {{ profile.displayName ?? 'This user' }} hasn't posted anything yet.
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
      />
    </template>
  </div>
</template>
