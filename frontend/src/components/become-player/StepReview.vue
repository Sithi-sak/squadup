<script setup lang="ts">
import { computed } from 'vue'
import type {
  AccountStepData,
  GamesStepData,
  RatesStepData,
  ReviewStepData,
  VerifyStepData,
} from './types'
import { availabilityDays, mockWalletHandle } from './types'

const data = defineModel<ReviewStepData>({ required: true })

const props = defineProps<{
  accountData: AccountStepData
  gamesData: GamesStepData
  ratesData: RatesStepData
  verifyData: VerifyStepData
}>()

const emit = defineEmits<{ submit: []; back: []; edit: [stepId: number] }>()

const rateSummary = computed(() => {
  const prices = props.ratesData.rates.map((rate) => rate.price).filter((price) => price !== null)
  const unit =
    props.ratesData.pricingModel === 'per-hour'
      ? '/ hour'
      : props.ratesData.pricingModel === 'per-session'
        ? '/ session'
        : '/ game'
  if (prices.length === 0) return `— ${unit}`
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const priceLabel = min === max ? `${min} SC` : `${min}–${max} SC`
  return `${priceLabel} ${unit}`
})

const dayRangeLabel = computed(() => {
  const selected = availabilityDays.filter((day) => props.ratesData.availableDays.includes(day.key))
  if (selected.length === 0) return 'No days selected'
  const dayNames: Record<string, string> = {
    mon: 'Mon',
    tue: 'Tue',
    wed: 'Wed',
    thu: 'Thu',
    fri: 'Fri',
    sat: 'Sat',
    sun: 'Sun',
  }
  const indices = selected.map((day) => availabilityDays.findIndex((d) => d.key === day.key))
  const isContiguous = indices.every((idx, i) => {
    const prev = indices[i - 1]
    return i === 0 || (prev !== undefined && idx === prev + 1)
  })
  const first = selected[0]
  const last = selected[selected.length - 1]
  if (isContiguous && selected.length > 1 && first && last) {
    return `${dayNames[first.key]}–${dayNames[last.key]}`
  }
  return selected.map((day) => dayNames[day.key]).join(', ')
})

const timeWindowLabel = computed(() => {
  const window = props.ratesData.timeWindow
  const [, timeRange] = window.split('·')
  return timeRange ? timeRange.trim() : window
})

const payoutScheduleLabel = computed(() => {
  if (props.verifyData.payoutSchedule === 'bi-weekly') return 'Bi-weekly'
  if (props.verifyData.payoutSchedule === 'monthly') return 'Monthly'
  return 'Weekly'
})

const reviewSections = computed(() => [
  {
    stepId: 1,
    title: 'Account',
    line1: `${props.accountData.displayName || 'Pal'} · @${mockWalletHandle}`,
    line2: [props.accountData.email, props.accountData.region, props.accountData.timezone]
      .filter(Boolean)
      .join(' · '),
  },
  {
    stepId: 2,
    title: 'Games & skills',
    line1: [props.gamesData.games.join(', '), props.gamesData.highestRank].filter(Boolean).join(' · '),
    line2: `Mains ${props.gamesData.role} · Speaks ${props.gamesData.languages.join(', ')}`,
  },
  {
    stepId: 3,
    title: 'Rates & availability',
    line1: [rateSummary.value, props.ratesData.offerFirstOrderFree ? 'First order free' : null]
      .filter(Boolean)
      .join(' · '),
    line2: `Available ${dayRangeLabel.value}, ${timeWindowLabel.value} · Instant booking ${props.ratesData.instantBooking ? 'on' : 'off'}`,
  },
  {
    stepId: 4,
    title: 'Verify & payout',
    line1: `ID ${props.verifyData.idFrontFileName ? 'verified' : 'not uploaded'} · Selfie ${props.verifyData.selfieVerified ? 'verified' : 'pending review'}`,
    line2: `Squad Coin wallet @${mockWalletHandle} · ${payoutScheduleLabel.value} payout`,
  },
])

const canSubmit = computed(() => data.value.confirmedAccurate)
</script>

<template>
  <h2 class="text-2xl font-semibold text-white sm:text-3xl">Review &amp; submit</h2>
  <p class="mt-2 text-slate-400">
    Double-check everything below. Once approved, your Pal profile goes live.
  </p>

  <form class="mt-6 flex flex-col gap-4" @submit.prevent="canSubmit && emit('submit')">
    <div
      v-for="section in reviewSections"
      :key="section.stepId"
      class="flex flex-col gap-1 rounded-2xl bg-gray-800/70 px-6 py-5"
    >
      <div class="flex items-center justify-between gap-4">
        <p class="text-base font-semibold text-white">{{ section.title }}</p>
        <button
          type="button"
          class="cursor-pointer text-sm font-medium text-brand-300 hover:text-brand-200"
          @click="emit('edit', section.stepId)"
        >
          Edit
        </button>
      </div>
      <p class="text-sm text-white">{{ section.line1 }}</p>
      <p class="text-sm text-slate-400">{{ section.line2 }}</p>
    </div>

    <UCheckbox v-model="data.confirmedAccurate" class="mt-2">
      <template #label>
        <span class="text-sm text-slate-300">
          I agree to the <span class="text-brand-300">Pal Terms</span>,
          <span class="text-brand-300">Payout Policy</span>, and
          <span class="text-brand-300">Community Guidelines</span>, and confirm the information above
          is accurate.
        </span>
      </template>
    </UCheckbox>

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
      <UButton type="submit" color="primary" :disabled="!canSubmit" class="rounded-full px-8 py-2 text-base">
        Submit application
      </UButton>
    </div>
  </form>
</template>
