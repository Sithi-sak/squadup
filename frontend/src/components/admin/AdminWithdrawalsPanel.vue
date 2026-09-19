<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhMagnifyingGlass } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { useAdminStore } from '@/stores/admin'
import type { AdminWithdrawal, AdminWithdrawalStatus } from '@/mocks/admin'
import { coinsToUsd } from '@/utils/coins'

const adminStore = useAdminStore()
const toast = useToast()

onMounted(() => {
  adminStore.fetchWithdrawals()
})

const viewing = ref<AdminWithdrawal | null>(null)
const search = ref('')
const statusUpdating = ref(false)

const filters = [
  { key: 'requested', label: 'Awaiting review' },
  { key: 'in_progress', label: 'In progress' },
  { key: 'paid', label: 'Paid' },
  { key: 'rejected', label: 'Declined' },
  { key: 'all', label: 'All' },
] as const

const activeFilter = ref<(typeof filters)[number]['key']>('requested')

const statusMeta: Record<AdminWithdrawalStatus, { label: string; class: string }> = {
  requested: { label: 'Awaiting review', class: 'text-amber-400' },
  in_progress: { label: 'In progress', class: 'text-sky-400' },
  paid: { label: 'Paid', class: 'text-brand-400' },
  rejected: { label: 'Declined', class: 'text-red-400' },
}

const usd = coinsToUsd

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const pendingCount = computed(
  () => adminStore.withdrawals.filter((withdrawal) => withdrawal.status === 'requested').length,
)

const rows = computed(() => {
  const query = search.value.trim().toLowerCase()
  return adminStore.withdrawals
    .filter((withdrawal) => activeFilter.value === 'all' || withdrawal.status === activeFilter.value)
    .filter(
      (withdrawal) =>
        !query ||
        withdrawal.displayName.toLowerCase().includes(query) ||
        (withdrawal.reference ?? '').toLowerCase().includes(query) ||
        withdrawal.methodLabel.toLowerCase().includes(query) ||
        (withdrawal.methodDetail ?? '').toLowerCase().includes(query),
    )
    .sort((a, b) => new Date(b.requestedAt).getTime() - new Date(a.requestedAt).getTime())
})

/** A decided payout is final - the backend 409s on a second review, so the buttons go away
 * rather than offering an action that cannot succeed. */
const isDecided = computed(() => viewing.value?.status === 'paid' || viewing.value?.status === 'rejected')

async function setStatus(status: AdminWithdrawalStatus) {
  if (!viewing.value || statusUpdating.value) return
  const id = viewing.value.id
  statusUpdating.value = true
  try {
    const updated = await adminStore.updateWithdrawalStatus(id, status)
    viewing.value = updated
    toast.add({
      title: status === 'rejected' ? 'Payout declined' : 'Payout approved',
      description:
        status === 'rejected'
          ? 'The hold was released, so the coins stay in the Pal wallet.'
          : `${updated.coins.toLocaleString()} SC left the Pal wallet.`,
      color: status === 'rejected' ? 'warning' : 'success',
    })
  } catch (err) {
    toast.add({
      title: "Couldn't update payout",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    statusUpdating.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div>
      <h1 class="text-2xl font-bold text-white sm:text-3xl">Payouts</h1>
      <p class="mt-1 text-sm text-slate-400">
        Approve Pal withdrawal requests. Every payout is an 80/20 split: the Pal keeps 80%, SquadUp
        keeps 20%. The coins sit on hold until you approve, and leave the Pal's wallet at that
        moment.
      </p>
    </div>

    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap items-center gap-2">
        <UButton
          v-for="filter in filters"
          :key="filter.key"
          :color="activeFilter === filter.key ? 'primary' : 'neutral'"
          :variant="activeFilter === filter.key ? 'solid' : 'soft'"
          size="md"
          class="rounded-full"
          @click="activeFilter = filter.key"
        >
          {{ filter.label }}
          <span v-if="filter.key === 'requested' && pendingCount > 0" class="font-semibold">
            ({{ pendingCount }})
          </span>
        </UButton>
      </div>
      <UInput
        v-model="search"
        placeholder="Search payouts or reference"
        variant="subtle"
        class="w-full rounded-full sm:w-64"
        :ui="{ base: 'rounded-full' }"
      >
        <template #leading>
          <PhMagnifyingGlass :size="16" weight="bold" />
        </template>
      </UInput>
    </div>

    <div
      v-if="adminStore.withdrawalsLoading && adminStore.withdrawals.length === 0"
      class="py-16 text-center text-sm text-slate-400"
    >
      Loading payouts...
    </div>

    <UEmpty
      v-else-if="adminStore.withdrawalsError"
      title="Couldn't load payouts"
      :description="adminStore.withdrawalsError"
      class="py-16 text-white"
    >
      <template #actions>
        <UButton color="primary" class="rounded-full" @click="adminStore.fetchWithdrawals()">Retry</UButton>
      </template>
    </UEmpty>

    <UEmpty
      v-else-if="rows.length === 0"
      title="No payout requests"
      description="Try a different filter or search term."
      class="py-16 text-white"
    />

    <div v-else class="overflow-hidden rounded-xl bg-gray-800/70">
      <table class="w-full text-left text-sm">
        <thead>
          <tr class="border-b border-white/10 text-slate-400">
            <th class="px-5 py-3 font-medium">Pal</th>
            <th class="px-5 py-3 font-medium">Requested</th>
            <th class="px-5 py-3 font-medium">SquadUp (20%)</th>
            <th class="px-5 py-3 font-medium">Pal receives (80%)</th>
            <th class="px-5 py-3 font-medium">Method</th>
            <th class="px-5 py-3 font-medium">Status</th>
            <th class="px-5 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="withdrawal in rows" :key="withdrawal.id" class="border-b border-white/5 last:border-0">
            <td class="px-5 py-4">
              <div class="flex items-center gap-2.5">
                <UAvatar :src="withdrawal.avatarUrl ?? undefined" :alt="withdrawal.displayName" size="sm" />
                <div>
                  <p class="font-semibold text-white">{{ withdrawal.displayName }}</p>
                  <p class="text-md text-slate-400">{{ formatDate(withdrawal.requestedAt) }}</p>
                  <p v-if="withdrawal.reference" class="font-mono text-sm text-slate-500">
                    {{ withdrawal.reference }}
                  </p>
                </div>
              </div>
            </td>
            <td class="px-5 py-4">
              <span class="inline-flex items-center gap-1 font-semibold text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ withdrawal.coins.toLocaleString() }}
              </span>
            </td>
            <td class="px-5 py-4 text-amber-400">{{ withdrawal.feeCoins.toLocaleString() }}</td>
            <td class="px-5 py-4">
              <p class="font-semibold text-brand-400">{{ withdrawal.payoutCoins.toLocaleString() }}</p>
              <p class="text-sm text-slate-400">≈ ${{ usd(withdrawal.payoutCoins) }}</p>
            </td>
            <td class="px-5 py-4 text-slate-300">
              <p>{{ withdrawal.methodLabel }}</p>
              <p v-if="withdrawal.methodDetail" class="text-sm text-slate-400">{{ withdrawal.methodDetail }}</p>
            </td>
            <td class="px-5 py-4 font-medium" :class="statusMeta[withdrawal.status].class">
              {{ statusMeta[withdrawal.status].label }}
            </td>
            <td class="px-5 py-4 text-right">
              <button
                type="button"
                class="cursor-pointer font-medium text-brand-400 hover:text-brand-300"
                @click="viewing = withdrawal"
              >
                Review
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <UModal
      :open="!!viewing"
      :title="viewing?.reference ?? 'Payout request'"
      :ui="{ content: 'max-w-lg rounded-3xl' }"
      @update:open="(value: boolean) => { if (!value) viewing = null }"
    >
      <template #body>
        <div v-if="viewing" class="flex flex-col gap-4 text-sm">
          <div class="flex items-center justify-between rounded-xl bg-gray-800/70 p-4">
            <div class="flex items-center gap-3">
              <UAvatar :src="viewing.avatarUrl ?? undefined" :alt="viewing.displayName" size="md" />
              <div>
                <p class="font-semibold text-white">{{ viewing.displayName }}</p>
                <p class="text-slate-400">{{ viewing.methodLabel }} {{ viewing.methodDetail ?? '' }}</p>
              </div>
            </div>
            <span class="inline-flex items-center gap-1 text-base font-bold text-white">
              <img :src="coinIcon" alt="" class="h-4 w-4" />
              {{ viewing.coins.toLocaleString() }}
            </span>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-slate-400">Requested</span>
            <span class="font-medium text-white">{{ formatDate(viewing.requestedAt) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">SquadUp fee (20%)</span>
            <span class="font-medium text-amber-400">{{ viewing.feeCoins.toLocaleString() }} SC</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Pal receives (80%)</span>
            <span class="font-medium text-brand-400">
              {{ viewing.payoutCoins.toLocaleString() }} SC ≈ ${{ usd(viewing.payoutCoins) }}
            </span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Status</span>
            <span class="font-medium" :class="statusMeta[viewing.status].class">
              {{ statusMeta[viewing.status].label }}
            </span>
          </div>
          <div v-if="viewing.reviewedAt" class="flex items-center justify-between">
            <span class="text-slate-400">Reviewed</span>
            <span class="font-medium text-white">{{ formatDate(viewing.reviewedAt) }}</span>
          </div>

          <p v-if="isDecided" class="border-t border-white/10 pt-4 text-slate-400">
            This payout has already been reviewed.
          </p>
          <div v-else class="flex flex-col gap-3 border-t border-white/10 pt-4">
            <p v-if="viewing.status === 'requested'" class="text-sm text-slate-500">
              Approving debits {{ viewing.coins.toLocaleString() }} SC from
              {{ viewing.displayName }}'s wallet. Declining releases the hold and takes nothing.
            </p>
            <div class="grid grid-cols-3 gap-3">
            <UButton
              color="neutral"
              variant="soft"
              size="md"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating || viewing.status === 'in_progress'"
              @click="setStatus('in_progress')"
            >
              Processing
            </UButton>
            <UButton
              color="primary"
              size="md"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating"
              @click="setStatus('paid')"
            >
              Approve
            </UButton>
            <UButton
              color="error"
              variant="soft"
              size="md"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating"
              @click="setStatus('rejected')"
            >
              Decline
              </UButton>
            </div>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
