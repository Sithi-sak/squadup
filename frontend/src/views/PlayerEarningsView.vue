<script setup lang="ts">
import DashboardLayout from '@/components/dashboard/DashboardLayout.vue'
import DashboardBarChart from '@/components/dashboard/DashboardBarChart.vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { mockCurrentUser } from '@/mocks/users'
import { mockPalDashboardStats } from '@/mocks/dashboardStats'

const stats = mockPalDashboardStats

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<template>
  <DashboardLayout active="earnings">
    <div class="flex h-full flex-col gap-5 overflow-y-auto pr-1">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-white sm:text-3xl">Earnings</h1>
          <p class="mt-1 text-sm text-slate-400">Your Squad Coin balance, payouts and history</p>
        </div>
        <UButton color="primary" class="rounded-full" disabled>+ Withdraw</UButton>
      </div>

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div class="rounded-xl bg-gray-800/70 p-5">
          <p class="text-sm text-slate-400">Available balance</p>
          <div class="mt-2 flex items-center justify-between gap-3">
            <p class="inline-flex items-center gap-1.5 text-2xl font-bold text-white">
              <img :src="coinIcon" alt="" class="h-5 w-5" />
              {{ mockCurrentUser.coinBalance.toLocaleString() }}
            </p>
            <UButton color="primary" size="sm" class="rounded-full" disabled>Withdraw</UButton>
          </div>
        </div>
        <div class="rounded-xl bg-gray-800/70 p-5">
          <p class="text-sm text-slate-400">Pending clearance</p>
          <p class="mt-2 inline-flex items-center gap-1.5 text-2xl font-bold text-white">
            <img :src="coinIcon" alt="" class="h-5 w-5" />
            {{ stats.pendingClearanceCoins.toLocaleString() }}
          </p>
          <p class="mt-1 text-xs text-slate-400">Clears in {{ stats.pendingClearanceDays }} days</p>
        </div>
        <div class="rounded-xl bg-gray-800/70 p-5">
          <p class="text-sm text-slate-400">Lifetime earned</p>
          <p class="mt-2 inline-flex items-center gap-1.5 text-2xl font-bold text-white">
            <img :src="coinIcon" alt="" class="h-5 w-5" />
            {{ stats.lifetimeEarnedCoins.toLocaleString() }}
          </p>
          <p class="mt-1 text-xs text-brand-400">+{{ stats.lifetimeEarnedChangePct }}% vs last month</p>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
        <div class="rounded-xl bg-gray-800/70 p-5">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-bold text-white">Earnings overview</h2>
            <span class="text-sm text-slate-400">Last {{ stats.earningsOverview.length }} months</span>
          </div>
          <div class="mt-6 h-48">
            <DashboardBarChart :bars="stats.earningsOverview.map((b) => ({ label: b.month, value: b.coins }))" />
          </div>
        </div>

        <div class="rounded-xl bg-gray-800/70 p-5">
          <h2 class="text-lg font-bold text-white">Payout method</h2>
          <div class="mt-3 flex items-center gap-3 rounded-xl bg-gray-700/50 px-4 py-3">
            <img :src="coinIcon" alt="" class="h-6 w-6" />
            <div>
              <p class="font-semibold text-white">{{ stats.payoutMethod.label }}</p>
              <p class="text-sm text-slate-400">{{ stats.payoutMethod.handle }}</p>
            </div>
          </div>
          <div class="mt-4 flex flex-col gap-2 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Next payout</span>
              <span class="font-medium text-white">{{ formatDate(stats.nextPayoutDate) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Schedule</span>
              <span class="font-medium text-white">{{ stats.payoutSchedule }}</span>
            </div>
          </div>
          <UButton color="neutral" variant="soft" block class="mt-4 rounded-full" disabled>
            Change payout settings
          </UButton>
        </div>
      </div>

      <div class="rounded-xl bg-gray-800/70 p-5">
        <h2 class="text-lg font-bold text-white">Payout history</h2>
        <div class="mt-3 flex flex-col divide-y divide-white/10">
          <div
            v-for="payout in stats.payoutHistory"
            :key="payout.date"
            class="flex flex-wrap items-center justify-between gap-3 py-3"
          >
            <div>
              <p class="font-semibold text-white">{{ formatDate(payout.date) }}</p>
              <p class="text-sm text-slate-400">{{ payout.label }}</p>
            </div>
            <div class="flex items-center gap-4">
              <span class="inline-flex items-center gap-1 font-semibold text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ payout.coins.toLocaleString() }}
              </span>
              <UBadge
                :color="payout.status === 'paid' ? 'primary' : 'warning'"
                variant="soft"
                size="sm"
                class="rounded-full capitalize"
              >
                {{ payout.status }}
              </UBadge>
            </div>
          </div>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>
