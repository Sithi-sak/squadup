<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhCopy, PhDotsThree, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { usePlayersStore, type PlayerProfile, type PlayerSummary } from '@/stores/players'
import { useSubscriptionsStore } from '@/stores/subscriptions'
import { useAuthStore } from '@/stores/auth'
import { useUsersStore } from '@/stores/users'
import { useFeedStore } from '@/stores/feed'
import SubscriptionModal from './SubscriptionModal.vue'
import ReportProfileModal from '@/components/modals/ReportProfileModal.vue'
import BlockProfileModal from '@/components/modals/BlockProfileModal.vue'
import { resolveAvatarUrl } from '@/utils/avatar'

const route = useRoute()

const props = defineProps<{
  player: PlayerSummary
  profile: PlayerProfile
  isOwnProfile?: boolean
}>()

/** Lifted so the Services tab and the About card can drop their Chat/Book buttons the moment a
 * block lands, instead of offering actions the API would 403. */
const emit = defineEmits<{ 'blocked-change': [boolean] }>()

const feedStore = useFeedStore()
const playersStore = usePlayersStore()
const authStore = useAuthStore()
const usersStore = useUsersStore()
const router = useRouter()
const toast = useToast()

const following = ref(props.profile.following)
watch(
  () => props.profile.following,
  (value) => (following.value = value),
)

const followLoading = ref(false)

async function toggleFollow() {
  const userId = props.profile.userId ?? props.player.userId
  if (!userId || followLoading.value) return
  followLoading.value = true
  try {
    following.value = (await feedStore.toggleFollow(userId, following.value)).following
  } catch (err) {
    toast.add({
      title: following.value ? 'Could not unfollow' : 'Could not follow',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    followLoading.value = false
  }
}

function copyUsername() {
  navigator.clipboard?.writeText(props.profile.handle)
  toast.add({ title: 'Username copied', color: 'success' })
}

const subscriptionsStore = useSubscriptionsStore()
onMounted(() => {
  subscriptionsStore.fetchSubscriptions()
})

const subscribed = computed(() =>
  subscriptionsStore.list.some((s) => s.status === 'active' && s.playerId === props.player.id),
)

const subscriptionModalOpen = ref(false)

const reportModalOpen = ref(false)
const blockModalOpen = ref(false)
/** Seeded from the profile read: `blocked` is true only when *this viewer* is the one who
 * blocked the Pal. The reverse never gets here - the Pal's block 403s the profile read. */
const blocked = ref(props.profile.blocked ?? false)
watch(
  () => props.profile.blocked,
  (value) => (blocked.value = value ?? false),
)
const reportSubmitting = ref(false)
const blockPending = ref(false)

/** `users.id`, which is what a block keys on - null for a seed Pal with no linked account, and
 * there is nothing to block in that case. */
const palUserId = computed(() => props.profile.userId ?? props.player.userId)

const profileMenuItems = computed(() => [
  [
    { label: 'Report', onSelect: (): void => { reportModalOpen.value = true } },
    ...(palUserId.value
      ? [
          blocked.value
            ? { label: 'Unblock', onSelect: (): void => void setBlocked(false) }
            : {
                label: 'Block',
                color: 'error' as const,
                onSelect: (): void => { blockModalOpen.value = true },
              },
        ]
      : []),
  ],
])

/** Block/unblock (4.39). Blocking drops the follow in both directions server-side, so the
 * Follow button is reset here rather than left claiming a relationship that no longer exists. */
async function setBlocked(next: boolean) {
  const targetId = palUserId.value
  if (!targetId || blockPending.value) return
  if (!authStore.isAuthenticated) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  blockPending.value = true
  try {
    if (next) await usersStore.blockUser(targetId)
    else await usersStore.unblockUser(targetId)
    blocked.value = next
    emit('blocked-change', next)
    if (next) following.value = false
    blockModalOpen.value = false
    toast.add({
      title: next ? `Blocked ${props.profile.handle}` : `Unblocked ${props.profile.handle}`,
      description: next
        ? "They can't message, book, or view your profile."
        : 'They can interact with you again.',
      color: 'success',
    })
  } catch (err) {
    toast.add({
      title: next ? 'Could not block' : 'Could not unblock',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    blockPending.value = false
  }
}

/** The modal used to only emit into this handler, which set a local `blocked` flag and dropped
 * the report on the floor - nothing ever reached `admin_flags`, so the admin moderation queue
 * had nothing to show. It now files the report before closing. */
async function submitReport(payload: { reason: string; details: string; alsoBlock: boolean }) {
  if (reportSubmitting.value) return
  if (!authStore.isAuthenticated) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  reportSubmitting.value = true
  try {
    await playersStore.reportPlayer(props.player.id, payload)
    reportModalOpen.value = false
    if (payload.alsoBlock) await setBlocked(true)
    toast.add({
      title: 'Report submitted',
      description: 'Our moderation team will review it.',
      color: 'success',
    })
  } catch (err) {
    toast.add({
      title: 'Could not submit report',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    reportSubmitting.value = false
  }
}

function confirmBlock() {
  void setBlocked(true)
}
</script>

<template>
  <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
    <div class="flex items-start gap-4">
      <div class="relative shrink-0">
        <UAvatar :src="resolveAvatarUrl(player.id, player.avatarUrl)" size="3xl" class="bg-white/10 text-slate-300 size-24">
          <PhUserCircle :size="40" />
        </UAvatar>
        <span
          v-if="player.online"
          class="absolute right-1 bottom-1 h-3 w-3 rounded-full bg-brand-400 ring-2 ring-squadup-bg"
        />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-white">{{ player.displayName }}</h1>
        <p class="mt-1 text-sm text-slate-400">
          {{ profile.handle }} · {{ profile.timezone }} · {{ profile.language }}
        </p>
        <div class="mt-3 flex flex-wrap items-center gap-2">
          <UBadge v-if="player.online" color="primary" variant="primary" size="md" class="rounded-full text-sm">
            <span class="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-brand-400" />
            Online
          </UBadge>
          <UBadge color="neutral" variant="soft" size="md" class="rounded-full text-sm">{{ profile.tier }}</UBadge>
          <UBadge
            v-if="profile.highlightBadge"
            color="neutral"
            variant="soft"
            size="sm"
            class="rounded-full text-amber-400 text-xs"
          >
            {{ profile.highlightBadge }}
          </UBadge>
        </div>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <UDropdownMenu v-if="!isOwnProfile" :items="profileMenuItems">
        <UButton
          color="neutral"
          variant="soft"
          square
          :ui="{ base: 'rounded-full' }"
          aria-label="More options"
        >
          <PhDotsThree :size="24" weight="regular" />
        </UButton>
      </UDropdownMenu>
      <UButton
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
        v-if="!isOwnProfile && !blocked && (profile.userId ?? player.userId)"
        :color="following ? 'neutral' : 'primary'"
        :variant="following ? 'soft' : 'solid'"
        class="rounded-full"
        :loading="followLoading"
        @click="toggleFollow"
      >
        {{ following ? 'Following' : 'Follow' }}
      </UButton>
      <UButton
        v-if="false && !isOwnProfile && profile.subscribeLabel"
        color="primary"
        :variant="subscribed ? 'soft' : 'outline'"
        class="rounded-full"
        :disabled="subscribed"
        @click="subscriptionModalOpen = true"
      >
        {{ subscribed ? 'Subscribed' : profile.subscribeLabel }}
      </UButton>
    </div>

    <SubscriptionModal
      v-model:open="subscriptionModalOpen"
      :player-id="player.id"
      :service-id="profile.highlightedServiceId"
      :pal-name="player.displayName"
      :tagline="player.tagline ?? profile.tier"
      :rating="player.rating"
      :subscriber-count="profile.followersCount"
    />

    <ReportProfileModal
      v-model:open="reportModalOpen"
      :handle="profile.handle"
      :submitting="reportSubmitting"
      @submit="submitReport"
    />

    <BlockProfileModal v-model:open="blockModalOpen" :handle="profile.handle" @confirm="confirmBlock" />
  </div>
</template>
