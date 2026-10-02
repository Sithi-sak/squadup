<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhCloudWarning, PhCopy, PhHeart, PhImage, PhUserCircle } from '@phosphor-icons/vue'
import { useAuthStore } from '@/stores/auth'
import { useFeedStore, type FeedPost } from '@/stores/feed'
import { useUsersStore, type PublicProfile } from '@/stores/users'
import ProfileFeedsTab from '@/components/players/ProfileFeedsTab.vue'
import UserAboutCard from '@/components/players/UserAboutCard.vue'
import FollowListPanel from '@/components/feed/FollowListPanel.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { resolveAvatarUrl } from '@/utils/avatar'

/** Someone else's non-Pal profile. Laid out like the Pal profile page and `MyProfileView`
 * (full-width header plus a `UTabs` row) rather than inside the feed shell, which read as
 * "still the feed page" when a feed author's name was clicked. */
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

const tabItems = [
  { label: 'Feeds', value: 'feeds' },
  { label: 'Album', value: 'album' },
  { label: 'Wish', value: 'wish' },
]
const activeTab = ref('feeds')
/** The follower/following counts open their list in place of the tab content. */
const followListTab = ref<'followers' | 'following' | null>(null)

/** `ProfileFeedsTab` is shared with the Pal profile page, which feeds it a `PlayerSummary` -
 * a buyer has no player row, so this stands in with the three fields that component reads. */
const author = computed(() => ({
  id: profile.value?.id ?? '',
  displayName: profile.value?.displayName ?? 'SquadUp user',
  avatarUrl: profile.value?.avatarUrl ?? null,
}))

async function load() {
  const id = userId.value

  // Your own account has its own self-view page (no follow button, composer, ...) - which
  // forwards Pals on to `/players/{id}` in turn. Normally already handled by this route's
  // `beforeEnter` guard before this component ever mounts; kept here too since `watch(userId,
  // load)` re-runs on param changes the guard doesn't see again.
  if (id === authStore.user?.id) {
    router.replace({ name: 'my-profile' })
    return
  }

  loading.value = true
  profile.value = null
  posts.value = []
  activeTab.value = 'feeds'
  followListTab.value = null
  try {
    // The route guard already fetched this and would have redirected a Pal straight to
    // `/players/{id}`, so reaching here with a hand-off means it's already the plain profile -
    // only a direct param change (no guard re-run) falls through to fetching it here instead.
    profile.value =
      usersStore.takePrefetchedProfile(id) ?? (await usersStore.fetchPublicProfile(id))
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

function copyUsername() {
  if (!profile.value?.handle) return
  navigator.clipboard?.writeText(profile.value.handle)
  toast.add({ title: 'Username copied', color: 'success' })
}
</script>

<template>
  <div class="mx-auto max-w-4/5 px-4 pt-8 pb-14 md:px-6">
    <div v-if="loading">
      <div class="flex items-start gap-4">
        <USkeleton class="h-24 w-24 shrink-0 rounded-full" />
        <div class="flex flex-col gap-2 pt-2">
          <USkeleton class="h-7 w-40" />
          <USkeleton class="h-4 w-28" />
          <USkeleton class="mt-1 h-4 w-56" />
        </div>
      </div>
      <div class="mt-6 flex w-fit gap-6">
        <USkeleton v-for="n in 3" :key="n" class="h-5 w-16" />
      </div>
      <div class="mt-4">
        <USkeleton class="h-32 w-full rounded-xl" />
        <USkeleton class="mt-4 h-40 w-full rounded-xl" />
      </div>
    </div>

    <EmptyState
      v-else-if="!profile"
      :icon="PhCloudWarning"
      badge="Not found"
      title="Profile not found"
      description="This account may no longer exist."
      class="py-16"
    />

    <template v-else>
      <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div class="flex items-start gap-4">
          <div class="relative shrink-0">
            <UAvatar
              :src="resolveAvatarUrl(profile.id, profile.avatarUrl)"
              size="3xl"
              class="size-24 bg-white/10 text-slate-300"
            >
              <PhUserCircle :size="40" />
            </UAvatar>
            <span
              v-if="profile.online"
              class="absolute right-1 bottom-1 h-3 w-3 rounded-full bg-brand-400 ring-2 ring-squadup-bg"
            />
          </div>
          <div>
            <h1 class="text-3xl font-bold text-white">
              {{ profile.displayName ?? 'SquadUp user' }}
            </h1>
            <p v-if="profile.handle" class="mt-1 text-sm text-slate-400">{{ profile.handle }}</p>
            <div class="mt-3 flex flex-wrap items-center gap-5 text-sm">
              <span>
                <span class="font-semibold text-white">{{ profile.postsCount.toLocaleString() }}</span>
                <span class="ml-1.5 text-slate-400">Posts</span>
              </span>
              <button
                type="button"
                class="transition-opacity hover:opacity-80"
                @click="followListTab = 'followers'"
              >
                <span class="font-semibold text-white">{{ profile.followersCount.toLocaleString() }}</span>
                <span class="ml-1.5 text-slate-400">Followers</span>
              </button>
              <button
                type="button"
                class="transition-opacity hover:opacity-80"
                @click="followListTab = 'following'"
              >
                <span class="font-semibold text-white">{{ profile.followingCount.toLocaleString() }}</span>
                <span class="ml-1.5 text-slate-400">Following</span>
              </button>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <UButton
            v-if="profile.handle"
            color="neutral"
            variant="soft"
            square
            :ui="{ base: 'rounded-full' }"
            aria-label="Copy username"
            @click="copyUsername"
          >
            <PhCopy :size="24" weight="regular" />
          </UButton>
          <UButton
            v-if="authStore.user"
            :color="profile.following ? 'neutral' : 'primary'"
            :variant="profile.following ? 'soft' : 'solid'"
            class="rounded-full px-5"
            :loading="followPending"
            @click="toggleFollow"
          >
            {{ profile.following ? 'Following' : 'Follow' }}
          </UButton>
        </div>
      </div>

      <UTabs
        v-model="activeTab"
        variant="link"
        :items="tabItems"
        :content="false"
        class="mt-6 w-fit"
        :ui="{ label: 'text-white' }"
        @update:model-value="followListTab = null"
      />

      <div class="mt-4">
        <FollowListPanel
          v-if="followListTab"
          :key="followListTab"
          :user-id="profile.id"
          :initial-tab="followListTab"
          @back="followListTab = null"
        />
        <ProfileFeedsTab
          v-else-if="activeTab === 'feeds'"
          :player="author"
          :handle="profile.handle"
          :feed="posts"
        >
          <template #aside>
            <UserAboutCard :profile="profile" />
          </template>
        </ProfileFeedsTab>
        <EmptyState
          v-else-if="activeTab === 'album'"
          :icon="PhImage"
          badge="Album"
          title="No highlights yet"
          description="Clips and screenshots they save will show up here."
        />
        <EmptyState
          v-else
          :icon="PhHeart"
          badge="Wish"
          title="No wishes saved yet"
          description="Games and services they wishlist will show up here."
        />
      </div>
    </template>
  </div>
</template>
