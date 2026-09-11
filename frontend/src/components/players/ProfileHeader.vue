<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { PhCopy, PhDotsThree, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import type { PlayerProfile, PlayerSummary } from '@/stores/players'
import { useSubscriptionsStore } from '@/stores/subscriptions'
import { useFeedStore } from '@/stores/feed'
import SubscriptionModal from './SubscriptionModal.vue'
import ReportProfileModal from '@/components/modals/ReportProfileModal.vue'
import BlockProfileModal from '@/components/modals/BlockProfileModal.vue'
import { resolveAvatarUrl } from '@/utils/avatar'

const props = defineProps<{ player: PlayerSummary; profile: PlayerProfile }>()

const feedStore = useFeedStore()
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
const blocked = ref(false)

const profileMenuItems = computed(() => [
  [
    { label: 'Report', onSelect: (): void => { reportModalOpen.value = true } },
    { label: 'Block', color: 'error' as const, onSelect: (): void => { blockModalOpen.value = true } },
  ],
])

function submitReport(payload: { alsoBlock: boolean }) {
  if (payload.alsoBlock) blocked.value = true
}

function confirmBlock() {
  blocked.value = true
  blockModalOpen.value = false
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
      <UDropdownMenu :items="profileMenuItems">
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
        v-if="profile.userId ?? player.userId"
        :color="following ? 'neutral' : 'primary'"
        :variant="following ? 'soft' : 'solid'"
        class="rounded-full"
        :loading="followLoading"
        @click="toggleFollow"
      >
        {{ following ? 'Following' : 'Follow' }}
      </UButton>
      <UButton
        v-if="profile.subscribeLabel"
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

    <ReportProfileModal v-model:open="reportModalOpen" :handle="profile.handle" @submit="submitReport" />

    <BlockProfileModal v-model:open="blockModalOpen" :handle="profile.handle" @confirm="confirmBlock" />
  </div>
</template>
