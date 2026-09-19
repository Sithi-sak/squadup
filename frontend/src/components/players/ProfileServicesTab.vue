<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { PhStar } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import type { PlayerReview, PlayerServiceDetail, PlayerServiceListing } from '@/stores/players'
import { usePalChat } from '@/composables/usePalChat'
import { gameCoverForName } from '@/lib/covers'
import ProfileServiceSidebar from '@/components/players/ProfileServiceSidebar.vue'
import ServiceReviewsPanel from '@/components/players/ServiceReviewsPanel.vue'

/** The service picker lives in this tab, not in the page shell: it only means anything beside a
 * service detail, and rendering it page-level left it stranded on Feeds/Album/Wish. */
const props = defineProps<{
  playerId: string
  playerUserId?: string | null
  services: PlayerServiceListing[]
  serviceId: string
  detail: PlayerServiceDetail
  reviews: PlayerReview[]
  isOwnProfile?: boolean
  /** Viewer has blocked this Pal (4.39) - Chat and Book would 403, so they don't render. */
  blocked?: boolean
}>()

defineEmits<{ select: [id: string] }>()

const router = useRouter()
const startChat = usePalChat()

const coverSrc = computed(() => props.detail.coverImageUrl ?? gameCoverForName(props.detail.title))
</script>

<template>
  <div
    class="grid grid-cols-1 gap-4 lg:items-start"
    :class="services.length ? 'lg:grid-cols-[280px_1fr_320px]' : 'lg:grid-cols-[1fr_320px]'"
  >
    <ProfileServiceSidebar
      v-if="services.length"
      :services="services"
      :selected-id="serviceId"
      class="lg:sticky lg:top-20"
      @select="$emit('select', $event)"
    />

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
      <div class="aspect-square w-full overflow-hidden rounded-xl bg-white/5">
        <img v-if="coverSrc" :src="coverSrc" :alt="detail.title" class="h-full w-full object-cover" />
      </div>

      <div v-if="!isOwnProfile && !blocked" class="rounded-xl bg-gray-800/70 p-4">
        <UButton
          color="primary"
          variant="outline"
          block
          size="lg"
          class="rounded-full"
          @click="startChat(playerUserId)"
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
