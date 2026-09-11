<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhCloudWarning, PhCopy, PhHeart, PhImage, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import { useFeedStore, type FeedPost } from '@/stores/feed'
import { useUsersStore, type PublicProfile } from '@/stores/users'
import ProfileFeedsTab from '@/components/players/ProfileFeedsTab.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { resolveAvatarUrl } from '@/utils/avatar'

const router = useRouter()
const authStore = useAuthStore()
const feedStore = useFeedStore()
const usersStore = useUsersStore()
const toast = useToast()

const loading = ref(true)
const profile = ref<PublicProfile | null>(null)
const posts = ref<FeedPost[]>([])

const tabItems = [
  { label: 'Feeds', value: 'feeds' },
  { label: 'Album', value: 'album' },
  { label: 'Wish', value: 'wish' },
]
const activeTab = ref('feeds')

/** `ProfileFeedsTab` is shared with the Pal profile page, which feeds it a `PlayerSummary` -
 * a buyer has no player row, so this stands in with the three fields that component reads. */
const author = computed(() => ({
  id: profile.value?.id ?? '',
  displayName: profile.value?.displayName ?? 'SquadUp user',
  avatarUrl: profile.value?.avatarUrl ?? null,
}))

onMounted(async () => {
  const id = authStore.user!.id
  try {
    profile.value = await usersStore.fetchPublicProfile(id)
    // A Pal's own profile is the richer `/players/{id}` page (services, reviews, ...), which
    // renders its own self-view. Only non-Pal accounts belong on this stripped-down page.
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
})

function copyUsername() {
  if (!profile.value?.handle) return
  navigator.clipboard?.writeText(profile.value.handle)
  toast.add({ title: 'Username copied', color: 'success' })
}
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 pt-8 pb-14 md:px-6">
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
      badge="Unavailable"
      title="Couldn't load your profile"
      description="Something went wrong on our end. Please refresh and try again."
      class="py-16"
    />

    <template v-else>
      <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div class="flex items-start gap-4">
          <UAvatar
            :src="resolveAvatarUrl(profile.id, profile.avatarUrl)"
            size="3xl"
            class="size-24 shrink-0 bg-white/10 text-slate-300"
          >
            <PhUserCircle :size="40" />
          </UAvatar>
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
              <span>
                <span class="font-semibold text-white">{{ profile.followersCount.toLocaleString() }}</span>
                <span class="ml-1.5 text-slate-400">Followers</span>
              </span>
              <span>
                <span class="font-semibold text-white">{{ profile.followingCount.toLocaleString() }}</span>
                <span class="ml-1.5 text-slate-400">Following</span>
              </span>
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
          <UButton to="/settings" color="neutral" variant="soft" class="rounded-full px-4">
            Edit profile
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
      />

      <div class="mt-4">
        <ProfileFeedsTab
          v-if="activeTab === 'feeds'"
          :player="author"
          :handle="profile.handle"
          :feed="posts"
          is-own-profile
          @created="profile.postsCount += 1"
        />
        <EmptyState
          v-else-if="activeTab === 'album'"
          :icon="PhImage"
          badge="Album"
          title="No highlights yet"
          description="Clips and screenshots you save will show up here."
        />
        <EmptyState
          v-else
          :icon="PhHeart"
          badge="Wish"
          title="No wishes saved yet"
          description="Games and services you wishlist will show up here."
        />
      </div>
    </template>
  </div>
</template>
