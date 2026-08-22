<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhMagnifyingGlass, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import coinIcon from '@/assets/squadup-coin.svg'
import { useBookingsStore, type Booking, type BookingStatus } from '@/stores/bookings'
import { mockPlayers } from '@/mocks/players'
import { getPlayerProfile } from '@/mocks/playerProfiles'
import CancelOrderModal from '@/components/modals/CancelOrderModal.vue'
import LeaveReviewModal from '@/components/modals/LeaveReviewModal.vue'

const router = useRouter()
const bookingsStore = useBookingsStore()
const toast = useToast()

const cancelModalOpen = ref(false)
const cancelTarget = ref<{
  id: string
  orderNumber: string
  palName: string
  serviceTitle: string
  meta: string
  totalCoins: number
} | null>(null)

const reviewModalOpen = ref(false)
const reviewTarget = ref<{ palName: string; meta: string } | null>(null)

function isCancellable(status: BookingStatus) {
  return status === 'pending' || status === 'accepted'
}

function openCancelModal(booking: Booking, palName: string, serviceTitle: string) {
  cancelTarget.value = {
    id: booking.id,
    orderNumber: booking.orderNumber,
    palName,
    serviceTitle,
    meta: `${summaryText(booking)} · ${statusMeta[booking.status].label}`,
    totalCoins: booking.totalCoins,
  }
  cancelModalOpen.value = true
}

function confirmCancel() {
  if (cancelTarget.value) bookingsStore.cancelBooking(cancelTarget.value.id)
  cancelModalOpen.value = false
}

const filters = [
  { key: 'all', label: 'All' },
  { key: 'active', label: 'Active' },
  { key: 'completed', label: 'Completed' },
  { key: 'cancelled', label: 'Cancelled' },
] as const

const activeFilter = ref<(typeof filters)[number]['key']>('all')
const search = ref('')

const statusMeta: Record<BookingStatus, { label: string; class: string }> = {
  pending: { label: 'Pending', class: 'text-brand-400' },
  accepted: { label: 'In progress', class: 'text-amber-400' },
  completed: { label: 'Completed', class: 'text-brand-400' },
  declined: { label: 'Cancelled', class: 'text-red-400' },
}

function matchesFilter(status: BookingStatus) {
  if (activeFilter.value === 'all') return true
  if (activeFilter.value === 'active') return status === 'pending' || status === 'accepted'
  if (activeFilter.value === 'completed') return status === 'completed'
  return status === 'declined'
}

const rows = computed(() => {
  const query = search.value.trim().toLowerCase()
  return [...bookingsStore.list]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .filter((booking) => matchesFilter(booking.status))
    .map((booking) => {
      const player = mockPlayers.find((p) => p.id === booking.playerId) ?? null
      const profile = player ? getPlayerProfile(player) : null
      const detail = profile?.serviceDetails[booking.serviceId] ?? null
      return { booking, player, detail }
    })
    .filter(({ booking, player, detail }) => {
      if (!query) return true
      return (
        player?.displayName.toLowerCase().includes(query) ||
        detail?.title.toLowerCase().includes(query) ||
        booking.orderNumber.toLowerCase().includes(query)
      )
    })
})

function summaryText(booking: Booking) {
  if (booking.status === 'declined') return 'Refunded to wallet'
  const unit = booking.quantity === 1 ? 'game' : 'games'
  let text = `${booking.quantity} ${unit}`
  if (booking.addons.length) {
    text += ` + ${booking.addons.length} add-on${booking.addons.length > 1 ? 's' : ''}`
  }
  if (booking.promoLabel?.includes('%')) text += ` · ${booking.promoLabel}`
  return text
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function primaryActionLabel(booking: Booking) {
  if (booking.status === 'completed') return 'Leave review'
  if (booking.status === 'declined') return 'Reorder'
  return 'View order'
}

function handlePrimaryAction(booking: Booking) {
  if (booking.status === 'completed') {
    const player = mockPlayers.find((p) => p.id === booking.playerId) ?? null
    const detail = player ? getPlayerProfile(player).serviceDetails[booking.serviceId] : null
    reviewTarget.value = {
      palName: player?.displayName ?? 'Pal',
      meta: `${detail?.title ?? booking.serviceTypeLabel} · ${summaryText(booking)} · ${formatDate(booking.createdAt)}`,
    }
    reviewModalOpen.value = true
  } else if (booking.status === 'declined') {
    router.push(`/players/${booking.playerId}/services/${booking.serviceId}`)
  } else {
    router.push(`/bookings/${booking.id}`)
  }
}

function confirmReview() {
  toast.add({
    title: 'Review submitted',
    description: 'Thanks for the feedback!',
    color: 'success',
  })
}
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] px-4 pt-14 pb-14 md:px-6 md:pt-16">
    <div class="mx-auto max-w-(--content-max-width)">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <h1 class="text-3xl font-bold text-white">My orders</h1>
        <UInput
          v-model="search"
          placeholder="Search"
          variant="subtle"
          class="w-full rounded-full sm:w-64"
          :ui="{ base: 'rounded-full' }"
        >
          <template #leading>
            <PhMagnifyingGlass :size="16" weight="bold" />
          </template>
        </UInput>
      </div>

      <div class="mt-5 flex flex-wrap items-center gap-2">
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

      <UEmpty
        v-if="rows.length === 0"
        title="No orders yet"
        description="When you book a Pal, your active and past orders will show up here."
        class="py-16 text-white"
      >
        <template #actions>
          <UButton color="primary" class="rounded-full" @click="router.push('/players')">Find a Pal</UButton>
          <UButton color="neutral" variant="soft" class="rounded-full" @click="router.push('/services')">
            Explore games
          </UButton>
        </template>
      </UEmpty>

      <div v-else class="mt-6 flex flex-col gap-4">
        <div
          v-for="{ booking, player, detail } in rows"
          :key="booking.id"
          class="flex flex-col gap-4 rounded-xl bg-gray-800/70 p-5 sm:flex-row sm:items-center sm:justify-between"
        >
          <div class="flex items-start gap-3">
            <div class="relative shrink-0">
              <UAvatar size="lg" class="bg-white/10 text-slate-300">
                <PhUserCircle :size="26" />
              </UAvatar>
              <span
                v-if="player?.online"
                class="absolute right-0 bottom-0 h-2.5 w-2.5 rounded-full bg-brand-400 ring-2 ring-gray-800"
              />
            </div>
            <div>
              <p class="font-semibold text-white">
                {{ player?.displayName ?? 'Pal' }}
                <span class="font-normal text-slate-400">· {{ detail?.title ?? booking.serviceTypeLabel }}</span>
              </p>
              <p class="text-sm text-slate-400">
                Order #{{ booking.orderNumber }} · {{ formatDate(booking.createdAt) }}
              </p>
              <p class="mt-2 flex flex-wrap items-center gap-1.5 text-sm text-slate-300">
                {{ summaryText(booking) }}
                <img :src="coinIcon" alt="" class="h-4 w-4" />
                <span class="font-semibold text-white">{{ booking.totalCoins }}</span>
              </p>
            </div>
          </div>

          <div class="flex shrink-0 flex-col items-start gap-2 sm:items-end">
            <span class="text-sm font-medium" :class="statusMeta[booking.status].class">
              {{ statusMeta[booking.status].label }}
            </span>
            <div class="flex items-center gap-2">
              <UButton
                v-if="isCancellable(booking.status)"
                color="neutral"
                variant="soft"
                size="sm"
                class="rounded-full text-red-400"
                @click="openCancelModal(booking, player?.displayName ?? 'Pal', detail?.title ?? booking.serviceTypeLabel)"
              >
                Cancel order
              </UButton>
              <UButton
                color="neutral"
                variant="soft"
                size="sm"
                class="rounded-full"
                @click="router.push('/messages')"
              >
                Message
              </UButton>
              <UButton color="primary" size="sm" class="rounded-full" @click="handlePrimaryAction(booking)">
                {{ primaryActionLabel(booking) }}
              </UButton>
            </div>
          </div>
        </div>
      </div>

      <CancelOrderModal
        v-model:open="cancelModalOpen"
        :order-number="cancelTarget?.orderNumber ?? ''"
        :pal-name="cancelTarget?.palName ?? 'Pal'"
        :service-title="cancelTarget?.serviceTitle ?? ''"
        :meta="cancelTarget?.meta ?? ''"
        :total-coins="cancelTarget?.totalCoins ?? 0"
        @confirm="confirmCancel"
      />

      <LeaveReviewModal
        v-model:open="reviewModalOpen"
        :pal-name="reviewTarget?.palName ?? 'Pal'"
        :meta="reviewTarget?.meta ?? ''"
        @submit="confirmReview"
      />
    </div>
  </div>
</template>
