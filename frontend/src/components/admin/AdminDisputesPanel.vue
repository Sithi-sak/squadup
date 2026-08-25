<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhMagnifyingGlass } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { useAdminStore } from '@/stores/admin'
import type { AdminDispute, DisputeStatus } from '@/mocks/admin'

const adminStore = useAdminStore()
const toast = useToast()

onMounted(() => {
  adminStore.fetchDisputes()
})

const viewing = ref<AdminDispute | null>(null)
const search = ref('')
const statusUpdating = ref(false)

const filters = [
  { key: 'all', label: 'All' },
  { key: 'open', label: 'Open' },
  { key: 'investigating', label: 'Investigating' },
  { key: 'resolved', label: 'Resolved' },
  { key: 'refunded', label: 'Refunded' },
] as const

const activeFilter = ref<(typeof filters)[number]['key']>('all')

const statusMeta: Record<DisputeStatus, { label: string; class: string }> = {
  open: { label: 'Open', class: 'text-amber-400' },
  investigating: { label: 'Investigating', class: 'text-sky-400' },
  resolved: { label: 'Resolved', class: 'text-brand-400' },
  refunded: { label: 'Refunded', class: 'text-slate-400' },
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const rows = computed(() => {
  const query = search.value.trim().toLowerCase()
  return adminStore.disputes
    .filter((dispute) => activeFilter.value === 'all' || dispute.status === activeFilter.value)
    .filter(
      (dispute) =>
        !query ||
        dispute.buyerName.toLowerCase().includes(query) ||
        dispute.palName.toLowerCase().includes(query) ||
        dispute.orderNumber.toLowerCase().includes(query),
    )
    .sort((a, b) => new Date(b.openedAt).getTime() - new Date(a.openedAt).getTime())
})

async function setStatus(status: DisputeStatus) {
  if (!viewing.value || statusUpdating.value) return
  const id = viewing.value.id
  statusUpdating.value = true
  try {
    const updated = await adminStore.updateDisputeStatus(id, status)
    viewing.value = updated
  } catch (err) {
    toast.add({
      title: "Couldn't update status",
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
      <h1 class="text-2xl font-bold text-white sm:text-3xl">Disputes</h1>
      <p class="mt-1 text-sm text-slate-400">Investigate order disputes and resolve refunds</p>
    </div>

    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap items-center gap-2">
        <UButton
          v-for="filter in filters"
          :key="filter.key"
          :color="activeFilter === filter.key ? 'primary' : 'neutral'"
          :variant="activeFilter === filter.key ? 'solid' : 'soft'"
          size="sm"
          class="rounded-full"
          @click="activeFilter = filter.key"
        >
          {{ filter.label }}
        </UButton>
      </div>
      <UInput
        v-model="search"
        placeholder="Search disputes"
        variant="subtle"
        class="w-full rounded-full sm:w-64"
        :ui="{ base: 'rounded-full' }"
      >
        <template #leading>
          <PhMagnifyingGlass :size="16" weight="bold" />
        </template>
      </UInput>
    </div>

    <div v-if="adminStore.disputesLoading && adminStore.disputes.length === 0" class="py-16 text-center text-sm text-slate-400">
      Loading disputes...
    </div>

    <UEmpty
      v-else-if="adminStore.disputesError"
      title="Couldn't load disputes"
      :description="adminStore.disputesError"
      class="py-16 text-white"
    >
      <template #actions>
        <UButton color="primary" class="rounded-full" @click="adminStore.fetchDisputes()">Retry</UButton>
      </template>
    </UEmpty>

    <UEmpty
      v-else-if="rows.length === 0"
      title="No disputes found"
      description="Try a different filter or search term."
      class="py-16 text-white"
    />

    <div v-else class="overflow-hidden rounded-xl bg-gray-800/70">
      <table class="w-full text-left text-sm">
        <thead>
          <tr class="border-b border-white/10 text-slate-400">
            <th class="px-5 py-3 font-medium">Order</th>
            <th class="px-5 py-3 font-medium">Buyer vs Pal</th>
            <th class="px-5 py-3 font-medium">Amount</th>
            <th class="px-5 py-3 font-medium">Opened</th>
            <th class="px-5 py-3 font-medium">Status</th>
            <th class="px-5 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="dispute in rows" :key="dispute.id" class="border-b border-white/5 last:border-0">
            <td class="px-5 py-4">
              <p class="font-semibold text-white">#{{ dispute.orderNumber }}</p>
              <p class="text-sm text-slate-400">{{ dispute.serviceLabel }}</p>
            </td>
            <td class="px-5 py-4 text-slate-300">{{ dispute.buyerName }} vs {{ dispute.palName }}</td>
            <td class="px-5 py-4">
              <span class="inline-flex items-center gap-1 font-semibold text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ dispute.totalCoins }}
              </span>
            </td>
            <td class="px-5 py-4 text-slate-300">{{ formatDate(dispute.openedAt) }}</td>
            <td class="px-5 py-4 font-medium" :class="statusMeta[dispute.status].class">
              {{ statusMeta[dispute.status].label }}
            </td>
            <td class="px-5 py-4 text-right">
              <button
                type="button"
                class="cursor-pointer font-medium text-brand-400 hover:text-brand-300"
                @click="viewing = dispute"
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
      :title="`Order #${viewing?.orderNumber ?? ''}`"
      :ui="{ content: 'max-w-lg rounded-3xl' }"
      @update:open="(value: boolean) => { if (!value) viewing = null }"
    >
      <template #body>
        <div v-if="viewing" class="flex flex-col gap-4 text-sm">
          <div class="flex items-center justify-between rounded-xl bg-gray-800/70 p-4">
            <div>
              <p class="font-semibold text-white">{{ viewing.buyerName }} vs {{ viewing.palName }}</p>
              <p class="text-slate-400">{{ viewing.serviceLabel }}</p>
            </div>
            <span class="inline-flex items-center gap-1 text-base font-bold text-white">
              <img :src="coinIcon" alt="" class="h-4 w-4" />
              {{ viewing.totalCoins }}
            </span>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-slate-400">Reason</span>
            <span class="font-medium text-white">{{ viewing.reason }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Opened</span>
            <span class="font-medium text-white">{{ formatDate(viewing.openedAt) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Status</span>
            <span class="font-medium" :class="statusMeta[viewing.status].class">{{ statusMeta[viewing.status].label }}</span>
          </div>

          <div class="grid grid-cols-3 gap-3 border-t border-white/10 pt-4">
            <UButton
              color="neutral"
              variant="soft"
              size="sm"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating"
              @click="setStatus('investigating')"
            >
              Investigate
            </UButton>
            <UButton
              color="primary"
              variant="soft"
              size="sm"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating"
              @click="setStatus('resolved')"
            >
              Resolve
            </UButton>
            <UButton
              color="error"
              size="sm"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating"
              @click="setStatus('refunded')"
            >
              Refund buyer
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
