<script setup lang="ts">
import { computed, watch } from 'vue'
import { PhCaretRight, PhPlus, PhX } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { availabilityDays, type PricingModel, type RatesStepData } from './types'

const data = defineModel<RatesStepData>({ required: true })

const props = defineProps<{ selectedGames: string[] }>()

const emit = defineEmits<{ continue: []; back: [] }>()

const gameOptions = [
  'Valorant',
  'League of Legends',
  'Mobile Legends: Bang Bang',
  'Dota 2',
  'Counter-Strike 2',
  'Overwatch 2',
  'Apex Legends',
  'PUBG Mobile',
  'Free Fire',
  'Honor of Kings',
]

watch(
  () => props.selectedGames,
  (games) => {
    for (const game of games) {
      if (!data.value.rates.some((rate) => rate.game === game)) {
        data.value.rates.push({ game, price: null })
      }
    }
  },
  { immediate: true },
)

const remainingGames = computed(() =>
  gameOptions.filter((game) => !data.value.rates.some((rate) => rate.game === game)),
)

const gameMenuItems = computed(() =>
  remainingGames.value.map((game) => ({ label: game, onSelect: () => addGame(game) })),
)

function addGame(game: string) {
  data.value.rates.push({ game, price: null })
}

function removeGame(game: string) {
  data.value.rates = data.value.rates.filter((rate) => rate.game !== game)
}

const pricingModelOptions: { label: string; value: PricingModel }[] = [
  { label: 'Per game', value: 'per-game' },
  { label: 'Per hour', value: 'per-hour' },
  { label: 'Per session', value: 'per-session' },
]

const rateUnit = computed(() => {
  if (data.value.pricingModel === 'per-hour') return '/ hour'
  if (data.value.pricingModel === 'per-session') return '/ session'
  return '/ game'
})

const timeWindowOptions = [
  'Mornings · 6:00 AM – 12:00 PM',
  'Afternoons · 12:00 PM – 6:00 PM',
  'Evenings · 6:00 PM – 12:00 AM',
  'Late night · 12:00 AM – 6:00 AM',
]

function toggleDay(key: string) {
  data.value.availableDays = data.value.availableDays.includes(key)
    ? data.value.availableDays.filter((d) => d !== key)
    : [...data.value.availableDays, key]
}

const canSubmit = computed(
  () =>
    data.value.rates.length > 0 &&
    data.value.rates.every((rate) => rate.price !== null && rate.price > 0) &&
    data.value.availableDays.length > 0 &&
    data.value.timeWindow.length > 0,
)

const selectUi = { base: 'bg-gray-800/70 px-5 py-3.5 text-sm ring-0 hover:bg-gray-800' }
</script>

<template>
  <h2 class="text-2xl font-semibold text-white sm:text-3xl">Set your rates &amp; availability</h2>
  <p class="mt-2 text-slate-400">
    Buyers see these prices and when you're online. You can change them anytime.
  </p>

  <form class="mt-8 flex flex-col gap-6" @submit.prevent="canSubmit && emit('continue')">
    <div class="flex flex-col gap-3">
      <label class="text-sm font-medium text-white">Per-game rate (99 coin = 1$)</label>
      <div class="flex flex-col gap-3">
        <div
          v-for="rate in data.rates"
          :key="rate.game"
          class="flex items-center justify-between gap-4 rounded-full bg-gray-800/70 px-6 py-2"
        >
          <span class="text-sm font-medium text-white">{{ rate.game }}</span>
          <div class="flex items-center gap-2">
            <img :src="coinIcon" alt="" class="h-4 w-4" />
            <UInputNumber
              v-model="rate.price"
              :min="0"
              :increment="true"
              :decrement="true"
              placeholder="0"
              variant="subtle"
              size="sm"
              class="w-25"
              :ui="{ base: 'bg-transparent px-1 text-sm text-right ring-0 focus-visible:ring-0' }"
            />
            <span class="text-sm text-slate-400">{{ rateUnit }}</span>
            <button
              type="button"
              class="cursor-pointer text-slate-500 hover:text-slate-300"
              :aria-label="`Remove ${rate.game}`"
              @click="removeGame(rate.game)"
            >
              <PhX :size="16" weight="bold" />
            </button>
          </div>
        </div>

        <UDropdownMenu v-if="remainingGames.length" :items="gameMenuItems">
          <UButton
            color="neutral"
            variant="soft"
            class="w-fit gap-2 rounded-full bg-gray-800/70 text-white hover:bg-brand-600"
          >
            <PhPlus :size="16" />
            Add a game you offer
          </UButton>
        </UDropdownMenu>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <label class="text-sm font-medium text-white">Pricing model</label>
      <div class="flex flex-wrap items-center gap-3">
        <button
          v-for="option in pricingModelOptions"
          :key="option.value"
          type="button"
          class="cursor-pointer rounded-full px-5 py-1.5 text-sm font-medium transition-colors"
          :class="
            data.pricingModel === option.value
              ? 'bg-brand-600 text-white'
              : 'bg-gray-800 text-slate-300 hover:bg-gray-800/70'
          "
          @click="data.pricingModel = option.value"
        >
          {{ option.label }}
        </button>
      </div>
    </div>

    <div class="flex items-center justify-between gap-4 rounded-full bg-gray-800/70 px-6 py-4">
      <div>
        <p class="text-sm font-medium text-white">Offer first order free</p>
        <p class="text-sm text-slate-400">A free first order helps you attract new buyers.</p>
      </div>
      <USwitch v-model="data.offerFirstOrderFree" color="primary" />
    </div>

    <div class="flex flex-col gap-3">
      <label class="text-sm font-medium text-white">Weekly availability</label>
      <div class="flex flex-wrap items-center gap-3">
        <button
          v-for="(day, index) in availabilityDays"
          :key="`${day.key}-${index}`"
          type="button"
          class="flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-full text-sm font-medium transition-colors"
          :class="
            data.availableDays.includes(day.key)
              ? 'bg-brand-600 text-white'
              : 'bg-gray-800 text-white hover:bg-brand-600'
          "
          :aria-pressed="data.availableDays.includes(day.key)"
          @click="toggleDay(day.key)"
        >
          {{ day.label }}
        </button>
      </div>

      <USelect
        v-model="data.timeWindow"
        :items="timeWindowOptions"
        placeholder="Select a time window"
        variant="subtle"
        size="md"
        :ui="selectUi"
      />
    </div>

    <div class="flex items-center justify-between gap-4 rounded-full bg-gray-800/70 px-6 py-4">
      <div>
        <p class="text-sm font-medium text-white">Instant booking</p>
        <p class="text-sm text-slate-400">Let buyers book without waiting for you to accept.</p>
      </div>
      <USwitch v-model="data.instantBooking" color="primary" />
    </div>

    <USeparator />

    <div class="flex justify-between">
      <UButton
        type="button"
        color="neutral"
        variant="soft"
        class="rounded-full bg-gray-800 px-8 py-2 text-base text-white hover:bg-gray-700"
        @click="emit('back')"
      >
        Back
      </UButton>
      <UButton
        type="submit"
        color="primary"
        :disabled="!canSubmit"
        class="rounded-full px-8 py-2 text-base"
      >
        Continue
      </UButton>
    </div>
  </form>
</template>
