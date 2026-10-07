<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import DashboardBarChart from '@/components/dashboard/DashboardBarChart.vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { usePlayersStore } from '@/stores/players'
import { useWalletStore } from '@/stores/wallet'

const playersStore = usePlayersStore()
const walletStore = useWalletStore()

onMounted(() => {
  playersStore.fetchEarnings()
  walletStore.fetchWallet()
  walletStore.fetchPayoutMethods()
  walletStore.fetchWithdrawals()
})

const earnings = computed(() => playersStore.earnings)

const overviewPeriods = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
] as const
const overviewPeriod = ref<'weekly' | 'monthly'>('monthly')
const overviewBars = computed(() =>
  (overviewPeriod.value === 'weekly'
    ? (earnings.value?.earningsOverviewWeekly ?? [])
    : (earnings.value?.earningsOverview ?? [])
  ).map((b) => ({ label: b.label, value: b.coins })),
)

const defaultPayoutMethod = computed(
  () => walletStore.payoutMethods.find((m) => m.isDefault) ?? walletStore.payoutMethods[0] ?? null,
)

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}
</script>

<template>
  <div class="flex h-full flex-col gap-5 overflow-y-auto pr-1">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-white sm:text-3xl">Earnings</h1>
        <p class="mt-1 text-sm text-slate-400">Your Squad Coin balance, payouts and history</p>
      </div>
      <UButton color="primary" class="rounded-full" to="/wallet/withdraw">Withdraw</UButton>
    </div>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <div class="rounded-xl bg-gray-800/70 p-5">
        <p class="text-sm text-slate-400">Available balance</p>
        <div class="mt-2 flex items-center justify-between gap-3">
          <p class="inline-flex items-center gap-1.5 text-2xl font-bold text-white">
            <img :src="coinIcon" alt="" class="h-5 w-5" />
            {{ walletStore.balance.toLocaleString() }}
          </p>
          <UButton color="primary" size="sm" class="rounded-full" to="/wallet/withdraw"
            >Withdraw</UButton
          >
        </div>
      </div>
      <div class="rounded-xl bg-gray-800/70 p-5">
        <p class="text-sm text-slate-400">Pending clearance</p>
        <p class="mt-2 inline-flex items-center gap-1.5 text-2xl font-bold text-white">
          <img :src="coinIcon" alt="" class="h-5 w-5" />
          {{ walletStore.pendingClearanceCoins.toLocaleString() }}
        </p>
        <p class="mt-1 text-xs text-slate-400">
          Tied up in orders you've accepted but not completed
        </p>
      </div>
      <div class="rounded-xl bg-gray-800/70 p-5">
        <p class="text-sm text-slate-400">Lifetime earned</p>
        <p class="mt-2 inline-flex items-center gap-1.5 text-2xl font-bold text-white">
          <img :src="coinIcon" alt="" class="h-5 w-5" />
          {{ (earnings?.lifetimeEarnedCoins ?? 0).toLocaleString() }}
        </p>
        <p v-if="earnings?.lifetimeEarnedChangePct != null" class="mt-1 text-xs text-brand-400">
          {{ earnings.lifetimeEarnedChangePct >= 0 ? '+' : ''
          }}{{ earnings.lifetimeEarnedChangePct }}% vs last month
        </p>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
      <div class="rounded-xl bg-gray-800/70 p-5">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="text-lg font-semibold text-white">Earnings overview</h2>
          <div class="flex items-center gap-2">
            <UButton
              v-for="option in overviewPeriods"
              :key="option.value"
              :color="overviewPeriod === option.value ? 'primary' : 'neutral'"
              :variant="overviewPeriod === option.value ? 'solid' : 'soft'"
              size="sm"
              class="rounded-full"
              @click="overviewPeriod = option.value"
            >
              {{ option.label }}
            </UButton>
          </div>
        </div>
        <div class="mt-6 h-48">
          <DashboardBarChart :bars="overviewBars" />
        </div>
      </div>

      <div class="rounded-xl bg-gray-800/70 p-5">
        <h2 class="text-lg font-semibold text-white">Payout method</h2>
        <div
          v-if="defaultPayoutMethod"
          class="mt-3 flex items-center gap-3 rounded-xl bg-gray-700/50 px-4 py-3"
        >
          <img :src="coinIcon" alt="" class="h-6 w-6" />
          <div>
            <p class="font-semibold text-white">{{ defaultPayoutMethod.label }}</p>
            <p class="text-sm text-slate-400">{{ defaultPayoutMethod.detail }}</p>
          </div>
        </div>
        <p v-else class="mt-3 text-sm text-slate-400">No payout method on file yet.</p>
        <UButton
          color="neutral"
          variant="soft"
          block
          class="mt-4 rounded-full"
          to="/settings?tab=payments"
        >
          Change payout settings
        </UButton>
      </div>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Payout history</h2>
      <p v-if="walletStore.withdrawals.length === 0" class="mt-3 text-sm text-slate-400">
        No withdrawals yet.
      </p>
      <div v-else class="mt-3 flex flex-col divide-y divide-white/10">
        <div
          v-for="withdrawal in walletStore.withdrawals"
          :key="withdrawal.id"
          class="flex flex-wrap items-center justify-between gap-3 py-3"
        >
          <div>
            <p class="font-semibold text-white">{{ formatDate(withdrawal.createdAt) }}</p>
            <p class="text-sm text-slate-400">Withdrawal</p>
          </div>
          <div class="flex items-center gap-4">
            <span class="inline-flex items-center gap-1 font-semibold text-white">
              <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
              {{ withdrawal.coins.toLocaleString() }}
            </span>
            <UBadge
              :color="withdrawal.status === 'paid' ? 'primary' : 'warning'"
              variant="solid"
              size="md"
              class="rounded-full"
            >
              {{ withdrawal.status === 'paid' ? 'Paid' : 'In progress' }}
            </UBadge>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
