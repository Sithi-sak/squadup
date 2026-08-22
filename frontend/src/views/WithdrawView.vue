<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { PhCaretLeft, PhPaypalLogo, PhCheck } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import visaIcon from '@/assets/visa.svg'
import { mockCurrentUser } from '@/mocks/users'
import {
  mockPayoutMethods,
  mockPendingCoins,
  mockWithdrawalHistory,
  mockWithdrawalPlatformFeePct,
} from '@/mocks/wallet'

/** $1 = 99 SC, matching the base top-up package (990 SC / $10). */
const COINS_PER_USD = 99

const router = useRouter()

const availableCoins = computed(() => mockCurrentUser.coinBalance)
const usdAvailable = computed(() => (availableCoins.value / COINS_PER_USD).toFixed(2))

const amount = ref(availableCoins.value)
const selectedMethodId = ref(mockPayoutMethods.find((m) => m.isDefault)?.id ?? mockPayoutMethods[0]!.id)

const feeCoins = computed(() => Math.round((amount.value * mockWithdrawalPlatformFeePct) / 100))
const receiveCoins = computed(() => amount.value - feeCoins.value)
const receiveUsd = computed(() => (receiveCoins.value / COINS_PER_USD).toFixed(2))

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] px-4 py-14 md:px-6">
    <div class="mx-auto flex max-w-4/5 flex-col gap-6">
      <div class="flex items-center gap-4">
        <UButton
          color="neutral"
          variant="soft"
          square
          :ui="{ base: 'rounded-full' }"
          aria-label="Back to wallet"
          @click="router.back()"
        >
          <PhCaretLeft :size="18" weight="bold" />
        </UButton>
        <h1 class="text-2xl font-bold text-white sm:text-3xl">Withdraw</h1>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-6 rounded-xl bg-gray-800/70 p-6 sm:p-8">
        <div>
          <p class="text-sm text-slate-400">Available to withdraw</p>
          <p class="mt-2 inline-flex items-center gap-2 text-4xl font-bold text-white">
            <img :src="coinIcon" alt="" class="h-8 w-8" />
            {{ availableCoins.toLocaleString() }}
          </p>
          <p class="mt-1 text-sm text-slate-400">≈ ${{ usdAvailable }} USD</p>
        </div>
        <p class="text-sm text-white">Pending: {{ mockPendingCoins.toLocaleString() }}</p>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
        <div class="rounded-xl bg-gray-800/70 p-5">
          <h2 class="text-lg font-semibold text-white">Withdraw funds</h2>

          <p class="mt-4 text-sm text-slate-400">Amount</p>
          <div class="mt-2 flex items-center justify-between gap-3 rounded-xl bg-gray-700/40 px-4 py-4">
            <div class="flex items-center gap-2">
              <img :src="coinIcon" alt="" class="h-7 w-7" />
              <UInput
                v-model.number="amount"
                type="number"
                min="0"
                :max="availableCoins"
                variant="none"
                size="xl"
                class="w-32"
                :ui="{ base: 'p-0 text-3xl font-bold text-white' }"
              />
            </div>
            <button
              type="button"
              class="cursor-pointer text-sm font-semibold text-brand-400 hover:text-brand-300"
              @click="amount = availableCoins"
            >
              Max
            </button>
          </div>

          <div class="mt-4 flex flex-col gap-2 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Withdrawal amount</span>
              <span class="font-medium text-white">{{ amount.toLocaleString() }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Platform fee ({{ mockWithdrawalPlatformFeePct }}%)</span>
              <span class="font-medium text-amber-400">− {{ feeCoins.toLocaleString() }}</span>
            </div>
          </div>
          <USeparator class="my-3" />
          <div class="flex items-center justify-between">
            <span class="font-semibold text-white">You'll receive ({{ 100 - mockWithdrawalPlatformFeePct }}%)</span>
            <span class="font-semibold text-brand-400">
              {{ receiveCoins.toLocaleString() }} SC ≈ ${{ receiveUsd }}
            </span>
          </div>

          <p class="mt-6 text-sm text-slate-400">Payout method</p>
          <div class="mt-3 flex flex-col gap-3">
            <button
              v-for="method in mockPayoutMethods"
              :key="method.id"
              type="button"
              class="flex cursor-pointer items-center justify-between gap-3 rounded-xl border bg-gray-700/40 px-4 py-3 text-left transition-colors"
              :class="selectedMethodId === method.id ? 'border-brand-400' : 'border-transparent hover:border-white/10'"
              @click="selectedMethodId = method.id"
            >
              <div class="flex items-center gap-3">
                <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white">
                  <PhPaypalLogo v-if="method.brand === 'paypal'" :size="20" weight="fill" class="text-[#003087]" />
                  <img v-else :src="visaIcon" alt="" class="h-7 w-7" />
                </div>
                <div>
                  <p class="font-medium text-white">{{ method.label }}</p>
                  <p class="text-sm text-slate-400">{{ method.detail }}</p>
                </div>
              </div>
              <span
                class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full"
                :class="selectedMethodId === method.id ? 'bg-brand-500' : 'ring-1 ring-inset ring-white/20'"
              >
                <PhCheck v-if="selectedMethodId === method.id" :size="12" weight="bold" class="text-white" />
              </span>
            </button>
          </div>

          <button
            type="button"
            disabled
            class="mt-3 w-full cursor-not-allowed rounded-xl border border-dashed border-white/15 py-3 text-sm font-medium text-brand-400"
          >
            + Add payout method
          </button>

          <p class="mt-4 text-sm">
            <span class="font-medium text-brand-400">Platform fee: {{ mockWithdrawalPlatformFeePct }}%</span>
            <span class="text-slate-400"> · Arrives in 1-3 business days</span>
          </p>

          <UButton color="primary" size="lg" block class="mt-4 rounded-full" disabled>
            Withdraw ${{ receiveUsd }}
          </UButton>
        </div>

        <div class="rounded-xl bg-gray-800/70 p-5">
          <h2 class="text-lg font-semibold text-white">Withdrawal history</h2>
          <div class="mt-2 flex flex-col divide-y divide-white/5">
            <div v-for="withdrawal in mockWithdrawalHistory" :key="withdrawal.id" class="flex items-center justify-between gap-3 py-3">
              <div>
                <p class="inline-flex items-center gap-1 font-semibold text-white">
                  <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                  {{ withdrawal.coins.toLocaleString() }}
                </p>
                <p class="text-sm text-slate-400">{{ formatDate(withdrawal.date) }} · {{ withdrawal.method }}</p>
              </div>
              <span
                class="shrink-0 text-sm font-medium"
                :class="withdrawal.status === 'paid' ? 'text-brand-400' : 'text-amber-400'"
              >
                {{ withdrawal.status === 'paid' ? 'Paid' : 'In progress' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
