<script setup lang="ts">
import { computed, ref } from 'vue'
import { PhArrowUp, PhCheck, PhLock } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { mockWalletHandle, type PayoutSchedule, type VerifyStepData } from './types'

const data = defineModel<VerifyStepData>({ required: true })

const emit = defineEmits<{ continue: []; back: [] }>()

const frontFileInput = ref<HTMLInputElement | null>(null)
const backFileInput = ref<HTMLInputElement | null>(null)

function openFilePicker(side: 'front' | 'back') {
  ;(side === 'front' ? frontFileInput : backFileInput).value?.click()
}

function onFileSelected(event: Event, side: 'front' | 'back') {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (side === 'front') data.value.idFrontFile = file
  else data.value.idBackFile = file
}

function toggleSelfie() {
  data.value.selfieVerified = !data.value.selfieVerified
}

const payoutScheduleOptions: { label: string; value: PayoutSchedule }[] = [
  { label: 'Weekly', value: 'weekly' },
  { label: 'Bi-weekly', value: 'bi-weekly' },
  { label: 'Monthly', value: 'monthly' },
]

const canSubmit = computed(() => data.value.idFrontFile !== null)
</script>

<template>
  <h2 class="text-2xl font-semibold text-white sm:text-3xl">Verify your identity &amp; payout</h2>
  <p class="mt-2 text-slate-400">
    We verify every Pal to keep SquadUp safe. Payouts are sent in Squad Coin.
  </p>

  <div class="mt-6 flex items-center gap-3 rounded-full bg-brand-600/10 px-6 py-2.5 text-brand-300">
    <PhLock :size="18" weight="fill" />
    <span class="text-sm">Your ID is encrypted and never shown on your public profile.</span>
  </div>

  <form class="mt-6 flex flex-col gap-6" @submit.prevent="canSubmit && emit('continue')">
    <div class="flex flex-col gap-3">
      <label class="text-sm font-medium text-white">Government ID</label>
      <div class="grid gap-4 sm:grid-cols-2">
        <button
          type="button"
          class="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 px-6 py-10 text-center transition-colors"
          :class="
            data.idFrontFile
              ? 'border-brand-600 bg-brand-600/5'
              : 'border-dashed border-gray-700 hover:border-gray-600'
          "
          @click="openFilePicker('front')"
        >
          <span
            class="flex size-10 items-center justify-center rounded-full"
            :class="data.idFrontFile ? 'bg-brand-600 text-white' : 'bg-gray-800 text-white'"
          >
            <PhCheck v-if="data.idFrontFile" :size="20" weight="bold" />
            <PhArrowUp v-else :size="20" weight="bold" />
          </span>
          <div>
            <p class="text-sm font-semibold text-white">
              {{ data.idFrontFile ? 'ID uploaded, front' : 'Upload ID, front' }}
            </p>
            <p class="mt-1 text-xs text-slate-400">
              {{ data.idFrontFile?.name ?? 'PNG, JPG or PDF · Max 10 MB' }}
            </p>
          </div>
        </button>

        <button
          type="button"
          class="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 px-6 py-10 text-center transition-colors"
          :class="
            data.idBackFile
              ? 'border-brand-600 bg-brand-600/5'
              : 'border-dashed border-gray-700 hover:border-gray-600'
          "
          @click="openFilePicker('back')"
        >
          <span
            class="flex size-10 items-center justify-center rounded-full"
            :class="data.idBackFile ? 'bg-brand-600 text-white' : 'bg-gray-800 text-white'"
          >
            <PhCheck v-if="data.idBackFile" :size="20" weight="bold" />
            <PhArrowUp v-else :size="20" weight="bold" />
          </span>
          <div>
            <p class="text-sm font-semibold text-white">
              {{ data.idBackFile ? 'ID uploaded, back' : 'Upload ID, back' }}
            </p>
            <p class="mt-1 text-xs text-slate-400">
              {{ data.idBackFile?.name ?? 'PNG, JPG or PDF · Max 10 MB' }}
            </p>
          </div>
        </button>
      </div>
      <input
        ref="frontFileInput"
        type="file"
        accept="image/png,image/jpeg,application/pdf"
        class="hidden"
        @change="onFileSelected($event, 'front')"
      />
      <input
        ref="backFileInput"
        type="file"
        accept="image/png,image/jpeg,application/pdf"
        class="hidden"
        @change="onFileSelected($event, 'back')"
      />
    </div>

    <div class="flex flex-col gap-3">
      <label class="text-sm font-medium text-white">Selfie verification</label>
      <button
        type="button"
        class="flex cursor-pointer items-center justify-between gap-4 rounded-full bg-gray-800/70 px-6 py-4 text-left"
        @click="toggleSelfie"
      >
        <div>
          <p class="text-sm font-medium text-white">Take a selfie holding your ID</p>
          <p class="text-sm text-slate-400">Used only to confirm it is really you.</p>
        </div>
        <UBadge :color="data.selfieVerified ? 'success' : 'warning'" variant="subtle" class="rounded-full">
          {{ data.selfieVerified ? 'Verified' : 'Pending' }}
        </UBadge>
      </button>
    </div>

    <div class="flex flex-col gap-3">
      <label class="text-sm font-medium text-white">Payout method</label>
      <div
        class="flex items-center justify-between gap-4 rounded-full border-2 border-brand-600 bg-brand-600/5 px-6 py-4"
      >
        <div class="flex items-center gap-3">
          <img :src="coinIcon" alt="" class="size-9 shrink-0" />
          <div>
            <p class="text-sm font-medium text-white">Squad Coin Wallet</p>
            <p class="text-sm text-slate-400">@{{ mockWalletHandle }} · Balance 0 SC</p>
          </div>
        </div>
        <UBadge color="success" variant="subtle" class="rounded-full">Selected</UBadge>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <label class="text-sm font-medium text-white">Payout schedule</label>
      <div class="flex flex-wrap items-center gap-3">
        <button
          v-for="option in payoutScheduleOptions"
          :key="option.value"
          type="button"
          class="cursor-pointer rounded-full px-5 py-1.5 text-sm font-medium transition-colors"
          :class="
            data.payoutSchedule === option.value
              ? 'bg-brand-600 text-white'
              : 'bg-gray-800 text-slate-300 hover:bg-gray-800/70'
          "
          @click="data.payoutSchedule = option.value"
        >
          {{ option.label }}
        </button>
      </div>
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
