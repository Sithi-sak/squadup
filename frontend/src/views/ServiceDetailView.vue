<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhCaretLeft, PhCheckCircle, PhStar } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { fallbackServiceDetail } from '@/mocks/playerProfiles'
import { usePlayerProfileData } from '@/composables/usePlayerProfileData'
import ServiceReviewsPanel from '@/components/players/ServiceReviewsPanel.vue'
import BookingModal from '@/components/players/BookingModal.vue'

const route = useRoute()
const router = useRouter()

const playerId = computed(() => String(route.params.id))
const { loading, player, profile } = usePlayerProfileData(playerId)
const serviceId = computed(() => String(route.params.serviceId))

const service = computed(
  () => profile.value.services.find((s) => s.id === serviceId.value) ?? profile.value.services[0]!,
)
const detail = computed(
  () =>
    profile.value.serviceDetails[serviceId.value] ??
    fallbackServiceDetail(
      service.value.name,
      service.value.priceCoins,
      service.value.priceUnit,
      service.value.promoBadge,
    ),
)
const reviews = computed(() => profile.value.reviews[serviceId.value] ?? [])

const selectedTypeIndex = ref(0)
watch(detail, () => (selectedTypeIndex.value = 0))
const selectedType = computed(
  () => detail.value.serviceTypes[selectedTypeIndex.value] ?? detail.value.serviceTypes[0]!,
)

const tags = computed(() => [
  ...detail.value.platforms,
  ...detail.value.styles,
  ...player.value.languages,
])

const bookingOpen = ref(false)
</script>

<template>
  <div class="mx-auto max-w-4/5 px-4 pt-8 pb-14 md:px-6">
    <div v-if="loading" class="py-16 text-center text-sm text-slate-400">Loading service...</div>

    <template v-else>
      <button
        type="button"
        class="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-white"
        @click="router.push(`/players/${player.id}`)"
      >
        <PhCaretLeft :size="14" weight="bold" />
        {{ player.displayName }} · Services
      </button>

      <div class="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
        <div class="flex flex-col gap-4">
          <div class="aspect-video w-full rounded-xl bg-white/5 ring-1 ring-inset ring-white/10" />

          <div class="rounded-xl bg-gray-800/70 p-5">
            <h1 class="text-2xl font-bold text-white">{{ detail.title }}</h1>

            <div class="mt-3 flex flex-wrap items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <div class="h-10 w-10 shrink-0 rounded-full bg-white/10" />
                <div>
                  <p class="font-medium text-white">{{ player.displayName }}</p>
                  <p class="inline-flex items-center gap-1 text-xs text-slate-400">
                    <PhStar :size="12" weight="fill" class="text-amber-400" />
                    {{ detail.rating ? detail.rating.toFixed(1) : '--' }} ({{
                      detail.servedCount.toLocaleString()
                    }})
                  </p>
                </div>
              </div>
              <UButton
                color="primary"
                variant="soft"
                size="sm"
                class="rounded-full"
                @click="router.push('/messages')"
              >
                Message
              </UButton>
            </div>

            <div v-if="tags.length" class="mt-4 flex flex-wrap gap-2">
              <UBadge
                v-for="tag in tags"
                :key="tag"
                color="neutral"
                variant="soft"
                size="sm"
                class="rounded-full text-xs"
              >
                {{ tag }}
              </UBadge>
            </div>
          </div>

          <div class="rounded-xl bg-gray-800/70 p-5">
            <h2 class="text-lg font-bold text-white">About this service</h2>
            <p class="mt-2 text-sm leading-relaxed text-slate-300">{{ detail.description }}</p>
          </div>

          <div class="rounded-xl bg-gray-800/70 p-5">
            <h2 class="text-lg font-bold text-white">Service types</h2>
            <div class="mt-3 flex flex-col gap-2">
              <button
                v-for="(type, index) in detail.serviceTypes"
                :key="type.label"
                type="button"
                class="flex w-full items-center justify-between gap-3 rounded-full px-4 py-3 text-left ring-1 ring-inset transition-colors"
                :class="
                  index === selectedTypeIndex
                    ? 'bg-brand-900/30 ring-brand-500'
                    : 'bg-gray-700/50 ring-transparent hover:ring-gray-600'
                "
                @click="selectedTypeIndex = index"
              >
                <span
                  class="flex size-4 shrink-0 items-center justify-center rounded-full ring-1 ring-inset"
                  :class="
                    index === selectedTypeIndex ? 'bg-brand-500 ring-brand-500' : 'ring-slate-500'
                  "
                >
                  <span v-if="index === selectedTypeIndex" class="size-1.5 rounded-full bg-white" />
                </span>
                <span class="min-w-0 flex-1 text-sm font-medium text-white">{{ type.label }}</span>
                <span class="inline-flex items-center gap-1 text-sm font-semibold text-white">
                  <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                  {{ type.priceCoins }}{{ type.priceUnit }}
                </span>
              </button>
            </div>
          </div>

          <div v-if="detail.whatsIncluded.length" class="rounded-xl bg-gray-800/70 p-5">
            <h2 class="text-lg font-bold text-white">What's included</h2>
            <ul class="mt-3 flex flex-col gap-2.5">
              <li
                v-for="item in detail.whatsIncluded"
                :key="item"
                class="flex items-center gap-2 text-sm text-slate-300"
              >
                <PhCheckCircle :size="18" weight="fill" class="shrink-0 text-brand-400" />
                {{ item }}
              </li>
            </ul>
          </div>

          <ServiceReviewsPanel :reviews="reviews" />
        </div>

        <div class="h-fit rounded-xl bg-gray-800/70 p-5 lg:sticky lg:top-24">
          <div class="flex flex-wrap items-center gap-2">
            <p class="inline-flex items-center gap-1.5 text-2xl font-bold text-white">
              <img :src="coinIcon" alt="" class="h-5 w-5" />
              {{ selectedType.priceCoins }}
              <span class="text-sm font-normal text-slate-400">{{ selectedType.priceUnit }}</span>
            </p>
            <UBadge
              v-if="selectedType.promoBadge"
              color="primary"
              variant="soft"
              size="sm"
              class="rounded-full text-xs text-brand-500"
            >
              {{ selectedType.promoBadge }}
            </UBadge>
          </div>

          <div class="mt-4 flex flex-col gap-2 border-t border-white/10 pt-4 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Service type</span>
              <span class="font-medium text-white">{{ selectedType.label }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Quantity</span>
              <span class="font-medium text-white">1</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Subtotal</span>
              <span class="inline-flex items-center gap-1 font-medium text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ selectedType.priceCoins }}
              </span>
            </div>
          </div>

          <div class="mt-3 flex items-center justify-between border-t border-white/10 pt-3">
            <span class="text-base font-bold text-white">Total</span>
            <span class="inline-flex items-center gap-1 text-lg font-bold text-white">
              <img :src="coinIcon" alt="" class="h-4 w-4" />
              {{ selectedType.priceCoins }}
            </span>
          </div>

          <UButton
            color="primary"
            block
            size="lg"
            class="mt-4 rounded-full"
            @click="bookingOpen = true"
          >
            Book now
          </UButton>
          <UButton
            color="primary"
            variant="outline"
            block
            size="lg"
            class="mt-2.5 rounded-full"
            @click="router.push('/messages')"
          >
            Chat first
          </UButton>
          <p class="mt-3 text-center text-xs text-slate-400">
            Avg response {{ detail.avgResponseTime }}
          </p>
        </div>
      </div>

      <BookingModal
        v-model:open="bookingOpen"
        :player-id="player.id"
        :service-id="serviceId"
        :pal-name="player.displayName"
        :pal-tagline="detail.title"
        :pal-rating="detail.rating"
        :pal-served-count="detail.servedCount"
        :service-type="selectedType"
      />
    </template>
  </div>
</template>
