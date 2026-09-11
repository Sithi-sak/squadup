<script setup lang="ts">
import { useRouter } from 'vue-router'
import { PhStar } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import coinIcon from '@/assets/squadup-coin.svg'
import type { PlayerReview, PlayerServiceDetail } from '@/stores/players'
import { useMessagesStore } from '@/stores/messages'
import { useAuthStore } from '@/stores/auth'
import ServiceReviewsPanel from '@/components/players/ServiceReviewsPanel.vue'

const props = defineProps<{
  playerId: string
  playerUserId?: string | null
  serviceId: string
  detail: PlayerServiceDetail
  reviews: PlayerReview[]
  isOwnProfile?: boolean
}>()

const router = useRouter()
const messagesStore = useMessagesStore()
const authStore = useAuthStore()
const toast = useToast()

async function handleMessage() {
  if (!authStore.isAuthenticated) {
    router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
    return
  }
  if (!props.playerUserId) {
    toast.add({ title: "Can't message this Pal yet", color: 'error' })
    return
  }
  try {
    await messagesStore.startThread(props.playerUserId)
    router.push('/messages')
  } catch (err) {
    toast.add({
      title: "Couldn't start chat",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}
</script>

<template>
  <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
    <div class="flex flex-col gap-4">
      <div class="rounded-xl bg-gray-800/70 p-5">
        <h2 class="text-2xl font-bold text-white">{{ detail.title }}</h2>
        <p class="mt-2 inline-flex items-center gap-1.5 text-sm text-slate-400">
          <PhStar :size="14" weight="fill" class="text-amber-400" />
          {{ detail.rating ? detail.rating.toFixed(1) : '--' }}
          <span>· {{ detail.servedCount.toLocaleString() }} Served</span>
        </p>
        <p class="mt-4 text-sm leading-relaxed text-slate-300">{{ detail.description }}</p>

        <div class="mt-4 flex flex-col gap-2 text-sm">
          <div v-if="detail.styles.length" class="flex items-center justify-between gap-4">
            <span class="text-slate-400">Styles</span>
            <span class="text-right font-medium text-white">{{ detail.styles.join(', ') }}</span>
          </div>
          <div v-if="detail.platforms.length" class="flex items-center justify-between gap-4">
            <span class="text-slate-400">Platforms</span>
            <span class="text-right font-medium text-white">{{ detail.platforms.join(', ') }}</span>
          </div>
        </div>
      </div>

      <div class="rounded-xl bg-gray-800/70 p-5">
        <h3 class="text-lg font-bold text-white">Service Types · {{ detail.serviceTypes.length }}</h3>
        <div class="mt-3 flex flex-col gap-2">
          <div
            v-for="type in detail.serviceTypes"
            :key="type.label"
            class="flex items-center justify-between gap-3 rounded-full bg-gray-700/50 px-4 py-3"
          >
            <span class="text-sm font-medium text-white">{{ type.label }}</span>
            <div class="flex items-center gap-2">
              <span class="inline-flex items-center gap-1 text-sm font-semibold text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ type.priceCoins }}{{ type.priceUnit }}
              </span>
              <UBadge v-if="type.promoBadge" color="primary" variant="soft" size="sm" class="rounded-full text-xs text-brand-500">
                {{ type.promoBadge }}
              </UBadge>
            </div>
          </div>
        </div>
      </div>

      <ServiceReviewsPanel :reviews="reviews" />
    </div>

    <div class="flex flex-col gap-4">
      <div class="aspect-video w-full rounded-xl bg-white/5" />

      <div v-if="!isOwnProfile" class="rounded-xl bg-gray-800/70 p-4">
        <UButton
          color="primary"
          variant="outline"
          block
          size="lg"
          class="rounded-full"
          @click="handleMessage"
        >
          Chat
        </UButton>
        <UButton
          color="primary"
          block
          size="lg"
          class="mt-2.5 rounded-full"
          @click="router.push(`/players/${playerId}/services/${serviceId}`)"
        >
          Book
        </UButton>
        <p class="mt-3 text-center text-xs text-slate-400">Avg Response Time {{ detail.avgResponseTime }}</p>
      </div>
    </div>
  </div>
</template>
