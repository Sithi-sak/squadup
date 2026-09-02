<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { PhCoins, PhFlag, PhGameController, PhScales, PhUsersThree } from '@phosphor-icons/vue'
import DashboardBarChart from '@/components/dashboard/DashboardBarChart.vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { useAdminStore } from '@/stores/admin'

defineEmits<{ 'view-all': ['flagged' | 'disputes'] }>()

const adminStore = useAdminStore()

onMounted(() => {
  adminStore.fetchOverview()
  adminStore.fetchFlaggedPlayers()
  adminStore.fetchDisputes()
})

const recentFlagged = computed(() => adminStore.flaggedPlayers.slice(0, 3))
const recentDisputes = computed(() => adminStore.disputes.slice(0, 3))
const openDisputeCount = computed(
  () => adminStore.disputes.filter((d) => d.status === 'open' || d.status === 'investigating').length,
)
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h1 class="text-2xl font-bold text-white sm:text-3xl">Overview</h1>
      <p class="mt-1 text-sm text-slate-400">Platform health, flagged players and open disputes</p>
    </div>

    <div v-if="adminStore.overviewLoading && !adminStore.overview" class="py-16 text-center text-sm text-slate-400">
      Loading overview...
    </div>

    <UEmpty
      v-else-if="adminStore.overviewError"
      title="Couldn't load overview"
      :description="adminStore.overviewError"
      class="py-16 text-white"
    >
      <template #actions>
        <UButton color="primary" class="rounded-full" @click="adminStore.fetchOverview()">Retry</UButton>
      </template>
    </UEmpty>

    <template v-else-if="adminStore.overview">
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <div class="flex flex-col rounded-xl bg-gray-800/70 p-5">
          <p class="inline-flex items-center gap-1.5 text-sm text-slate-400">
            <PhUsersThree :size="16" />
            Total users
          </p>
          <p class="mt-2 text-2xl font-bold text-white">{{ adminStore.overview.totalUsers.toLocaleString() }}</p>
        </div>
        <div class="flex flex-col rounded-xl bg-gray-800/70 p-5">
          <p class="inline-flex items-center gap-1.5 text-sm text-slate-400">
            <PhGameController :size="16" />
            Total Pals
          </p>
          <p class="mt-2 text-2xl font-bold text-white">{{ adminStore.overview.totalPals.toLocaleString() }}</p>
        </div>
        <div class="flex flex-col rounded-xl bg-gray-800/70 p-5">
          <p class="inline-flex items-center gap-1.5 text-sm text-slate-400">
            <PhFlag :size="16" />
            Flagged players
          </p>
          <p class="mt-2 text-2xl font-bold text-white">{{ adminStore.flaggedPlayers.length }}</p>
        </div>
        <div class="flex flex-col rounded-xl bg-gray-800/70 p-5">
          <p class="inline-flex items-center gap-1.5 text-sm text-slate-400">
            <PhScales :size="16" />
            Open disputes
          </p>
          <p class="mt-2 text-2xl font-bold text-white">{{ openDisputeCount }}</p>
        </div>
        <div class="flex flex-col rounded-xl bg-gray-800/70 p-5">
          <p class="inline-flex items-center gap-1.5 text-sm text-slate-400">
            <PhCoins :size="16" />
            Commission earned
          </p>
          <p class="mt-2 inline-flex items-center gap-1.5 text-2xl font-bold text-white">
            <img :src="coinIcon" alt="" class="h-5 w-5" />
            {{ adminStore.overview.totalCommissionCoins.toLocaleString() }}
          </p>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
        <div class="flex flex-col rounded-xl bg-gray-800/70 p-5">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-white">Recently flagged players</h2>
            <button
              type="button"
              class="cursor-pointer text-sm font-medium text-brand-400 hover:text-brand-300"
              @click="$emit('view-all', 'flagged')"
            >
              View all
            </button>
          </div>
          <div class="mt-3 flex flex-col divide-y divide-white/10">
            <p v-if="recentFlagged.length === 0" class="py-3 text-sm text-slate-400">No flagged players yet.</p>
            <div v-for="flag in recentFlagged" :key="flag.id" class="flex items-center justify-between gap-3 py-3">
              <div class="flex items-center gap-3">
                <UAvatar :src="flag.avatarUrl ?? undefined" size="md" class="bg-white/10" />
                <div>
                  <p class="font-semibold text-white">{{ flag.displayName }}</p>
                  <p class="text-sm text-slate-400">{{ flag.reason }}</p>
                </div>
              </div>
              <span class="text-sm text-slate-400">{{ flag.reportCount }} report{{ flag.reportCount > 1 ? 's' : '' }}</span>
            </div>
          </div>
        </div>

        <div class="flex flex-col rounded-xl bg-gray-800/70 p-5">
          <h2 class="text-lg font-semibold text-white">Reports this week</h2>
          <div class="mt-4 h-32">
            <DashboardBarChart :bars="adminStore.overview.reportsThisWeek.map((b) => ({ label: b.day, value: b.count }))" />
          </div>
        </div>
      </div>

      <div class="rounded-xl bg-gray-800/70 p-5">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-white">Recent disputes</h2>
          <button
            type="button"
            class="cursor-pointer text-sm font-medium text-brand-400 hover:text-brand-300"
            @click="$emit('view-all', 'disputes')"
          >
            View all
          </button>
        </div>
        <div class="mt-3 flex flex-col divide-y divide-white/10">
          <p v-if="recentDisputes.length === 0" class="py-3 text-sm text-slate-400">No disputes yet.</p>
          <div v-for="dispute in recentDisputes" :key="dispute.id" class="flex flex-wrap items-center justify-between gap-3 py-3">
            <div>
              <p class="font-semibold text-white">{{ dispute.buyerName }} vs {{ dispute.palName }}</p>
              <p class="text-sm text-slate-400">{{ dispute.reason }} · #{{ dispute.orderNumber }}</p>
            </div>
            <span class="inline-flex items-center gap-1 text-sm font-semibold text-white">
              <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
              {{ dispute.totalCoins }}
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
