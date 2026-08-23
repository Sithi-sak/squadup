<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { PhMagnifyingGlass, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import DashboardLayout from '@/components/dashboard/DashboardLayout.vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { getBuyer } from '@/mocks/buyers'
import { orderStatusMeta } from '@/utils/orderStatus'
import { useBookingsStore, type Booking, type BookingStatus } from '@/stores/bookings'

const bookingsStore = useBookingsStore()
const toast = useToast()

onMounted(() => {
  bookingsStore.fetchIncoming()
})

const viewing = ref<Booking | null>(null)
const actingOn = ref<string | null>(null)

function buyerName(booking: Booking) {
  return booking.buyerDisplayName ?? getBuyer(booking.userId)?.displayName ?? 'Buyer'
}

async function respond(booking: Booking, action: 'accept' | 'decline' | 'complete') {
  actingOn.value = booking.id
  try {
    if (action === 'accept') await bookingsStore.acceptBooking(booking.id)
    else if (action === 'decline') await bookingsStore.declineBooking(booking.id)
    else await bookingsStore.completeBooking(booking.id)
  } catch (err) {
    toast.add({
      title: 'Could not update order',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    actingOn.value = null
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const filters = [
  { key: 'all', label: 'All' },
  { key: 'accepted', label: 'In progress' },
  { key: 'pending', label: 'Pending' },
  { key: 'completed', label: 'Completed' },
  { key: 'declined', label: 'Cancelled' },
] as const

const activeFilter = ref<(typeof filters)[number]['key']>('all')
const search = ref('')

function matchesFilter(status: BookingStatus) {
  return activeFilter.value === 'all' || status === activeFilter.value
}

function gamesLabel(booking: Booking) {
  return booking.quantity > 1 ? `${booking.quantity} games` : booking.serviceTypeLabel
}

const rows = computed(() => {
  const query = search.value.trim().toLowerCase()
  return [...bookingsStore.incoming]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .filter((booking) => matchesFilter(booking.status))
    .filter((booking) => {
      if (!query) return true
      return (
        buyerName(booking).toLowerCase().includes(query) ||
        booking.serviceTypeLabel.toLowerCase().includes(query) ||
        booking.orderNumber.toLowerCase().includes(query)
      )
    })
})
</script>

<template>
  <DashboardLayout active="orders">
    <div class="flex h-full flex-col gap-5 overflow-y-auto pr-1">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-white sm:text-3xl">Orders</h1>
          <p class="mt-1 text-sm text-slate-400">Track active jobs and review your order history</p>
        </div>
        <UButton color="primary" class="rounded-full" disabled>Export</UButton>
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
          placeholder="Search orders"
          variant="subtle"
          class="w-full rounded-full sm:w-64"
          :ui="{ base: 'rounded-full' }"
        >
          <template #leading>
            <PhMagnifyingGlass :size="16" weight="bold" />
          </template>
        </UInput>
      </div>

      <UEmpty
        v-if="rows.length === 0"
        title="No orders found"
        description="Try a different filter or search term."
        class="py-16 text-white"
      />

      <div v-else class="overflow-hidden rounded-xl bg-gray-800/70">
        <table class="w-full text-left text-sm">
          <thead>
            <tr class="border-b border-white/10 text-slate-400">
              <th class="px-5 py-3 font-medium">Buyer</th>
              <th class="px-5 py-3 font-medium">Games</th>
              <th class="px-5 py-3 font-medium">Amount</th>
              <th class="px-5 py-3 font-medium">Status</th>
              <th class="px-5 py-3"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="booking in rows" :key="booking.id" class="border-b border-white/5 last:border-0">
              <td class="px-5 py-4">
                <div class="flex items-center gap-3">
                  <UAvatar size="md" class="bg-white/10 text-slate-300">
                    <PhUserCircle :size="22" />
                  </UAvatar>
                  <div>
                    <p class="font-semibold text-white">{{ buyerName(booking) }}</p>
                    <p class="text-sm text-slate-400">{{ booking.serviceTypeLabel }}</p>
                  </div>
                </div>
              </td>
              <td class="px-5 py-4 text-slate-300">{{ gamesLabel(booking) }}</td>
              <td class="px-5 py-4">
                <span class="inline-flex items-center gap-1 font-semibold text-white">
                  <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                  {{ booking.totalCoins }}
                </span>
              </td>
              <td class="px-5 py-4 font-medium" :class="orderStatusMeta(booking).class">
                {{ orderStatusMeta(booking).label }}
              </td>
              <td class="px-5 py-4 text-right">
                <div class="flex items-center justify-end gap-3">
                  <template v-if="booking.status === 'pending'">
                    <UButton
                      color="primary"
                      size="xs"
                      class="rounded-full"
                      :loading="actingOn === booking.id"
                      @click="respond(booking, 'accept')"
                    >
                      Accept
                    </UButton>
                    <UButton
                      color="neutral"
                      variant="soft"
                      size="xs"
                      class="rounded-full"
                      :loading="actingOn === booking.id"
                      @click="respond(booking, 'decline')"
                    >
                      Decline
                    </UButton>
                  </template>
                  <UButton
                    v-else-if="booking.status === 'accepted'"
                    color="primary"
                    variant="soft"
                    size="xs"
                    class="rounded-full"
                    :loading="actingOn === booking.id"
                    @click="respond(booking, 'complete')"
                  >
                    Mark complete
                  </UButton>
                  <button
                    type="button"
                    class="cursor-pointer font-medium text-brand-400 hover:text-brand-300"
                    @click="viewing = booking"
                  >
                    View
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <UModal
      :open="!!viewing"
      :title="`Order #${viewing?.orderNumber ?? ''}`"
      @update:open="(value: boolean) => { if (!value) viewing = null }"
    >
      <template #body>
        <div v-if="viewing" class="flex flex-col gap-3 text-sm">
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Buyer</span>
            <span class="font-medium text-white">{{ buyerName(viewing) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Service</span>
            <span class="font-medium text-white">{{ viewing.serviceTypeLabel }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Quantity</span>
            <span class="font-medium text-white">{{ viewing.quantity }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Status</span>
            <span class="font-medium" :class="orderStatusMeta(viewing).class">{{ orderStatusMeta(viewing).label }}</span>
          </div>
          <div v-if="viewing.scheduledFor" class="flex items-center justify-between">
            <span class="text-slate-400">Scheduled for</span>
            <span class="font-medium text-white">{{ formatDate(viewing.scheduledFor) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Placed</span>
            <span class="font-medium text-white">{{ formatDate(viewing.createdAt) }}</span>
          </div>
          <div class="flex items-center justify-between border-t border-white/10 pt-3">
            <span class="font-bold text-white">Total</span>
            <span class="inline-flex items-center gap-1 text-base font-bold text-white">
              <img :src="coinIcon" alt="" class="h-4 w-4" />
              {{ viewing.totalCoins }}
            </span>
          </div>

          <div v-if="viewing.status === 'pending'" class="grid grid-cols-2 gap-3 pt-1">
            <UButton
              color="neutral"
              variant="soft"
              block
              class="rounded-full"
              :loading="actingOn === viewing.id"
              @click="respond(viewing, 'decline'); viewing = null"
            >
              Decline
            </UButton>
            <UButton
              color="primary"
              block
              class="rounded-full"
              :loading="actingOn === viewing.id"
              @click="respond(viewing, 'accept'); viewing = null"
            >
              Accept
            </UButton>
          </div>
          <UButton
            v-else-if="viewing.status === 'accepted'"
            color="primary"
            variant="soft"
            block
            class="rounded-full"
            :loading="actingOn === viewing.id"
            @click="respond(viewing, 'complete'); viewing = null"
          >
            Mark complete
          </UButton>
        </div>
      </template>
    </UModal>
  </DashboardLayout>
</template>
