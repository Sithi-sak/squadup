<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhCaretLeft, PhCheck, PhLock, PhStar, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import coinIcon from '@/assets/squadup-coin.svg'
import { useBookingsStore, type Booking, type BookingStatus, type CancelPayload, type DisputePayload } from '@/stores/bookings'
import { useMessagesStore } from '@/stores/messages'
import { mockPlayers } from '@/mocks/players'
import { getPlayerProfile } from '@/mocks/playerProfiles'
import { getMockBooking } from '@/mocks/bookings'
import { orderStatusMeta, type OrderDisplayStatusKey } from '@/utils/orderStatus'
import CancelOrderModal from '@/components/modals/CancelOrderModal.vue'
import RefundModal from '@/components/modals/RefundModal.vue'
import { resolveAvatarUrl } from '@/utils/avatar'

const route = useRoute()
const router = useRouter()
const bookingsStore = useBookingsStore()
const messagesStore = useMessagesStore()
const toast = useToast()

const booking = ref<Booking | null>(null)

/** Prefers whatever's already in the store (populated by My Bookings / Pal Orders), falling
 * back to `GET /bookings/{id}` for a direct/deep link, then to the static mock fixtures if
 * that fails (signed out, network error) - same resilience pattern as the rest of Phase 3. */
async function loadBooking() {
  const id = String(route.params.bookingId)
  const existing = bookingsStore.getBooking(id)
  if (existing) {
    booking.value = existing
    return
  }
  try {
    booking.value = await bookingsStore.fetchBooking(id)
  } catch {
    booking.value = getMockBooking(id)
  }
}

onMounted(loadBooking)
watch(() => route.params.bookingId, loadBooking)

const player = computed(() => mockPlayers.find((p) => p.id === booking.value?.playerId) ?? null)
const profile = computed(() => (player.value ? getPlayerProfile(player.value) : null))
const detail = computed(() => (booking.value ? profile.value?.serviceDetails[booking.value.serviceId] : null))

const palName = computed(() => booking.value?.playerDisplayName ?? player.value?.displayName ?? 'Pal')
const palAvatarUrl = computed(() =>
  resolveAvatarUrl(booking.value?.playerId ?? palName.value, booking.value?.playerAvatarUrl ?? player.value?.avatarUrl),
)
const serviceTitle = computed(() => booking.value?.serviceName ?? detail.value?.title ?? booking.value?.serviceTypeLabel ?? '')

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}
function formatDateTime(iso: string) {
  return `${formatDate(iso)} · ${formatTime(iso)}`
}
function formatScheduled(iso: string | null) {
  if (!iso) return 'Start now'
  const date = new Date(iso)
  const isToday = date.toDateString() === new Date().toDateString()
  return `${isToday ? 'Today' : formatDate(iso)} · ${formatTime(iso)}`
}

const status = computed(() => (booking.value ? orderStatusMeta(booking.value) : null))

const statusBadgeStyles: Record<OrderDisplayStatusKey, string> = {
  pending: 'bg-amber-500/10 text-amber-400',
  scheduled: 'bg-sky-500/10 text-sky-400',
  'in-progress': 'bg-brand-500/10 text-brand-400',
  completed: 'bg-brand-500/10 text-brand-400',
  cancelled: 'bg-red-500/10 text-red-400',
}

type StepState = 'done' | 'active' | 'pending' | 'cancelled'
interface TimelineStep {
  label: string
  state: StepState
  sublabel: string
}

const timelineSteps = computed<TimelineStep[]>(() => {
  const b = booking.value
  if (!b) return []

  if (b.status === 'declined') {
    return [
      { label: 'Order placed', state: 'done', sublabel: formatDateTime(b.createdAt) },
      { label: 'Order cancelled', state: 'cancelled', sublabel: 'Refunded to wallet' },
    ]
  }

  const accepted = b.status === 'accepted' || b.status === 'completed'
  const completed = b.status === 'completed'
  const sessionStarted = accepted && (!b.scheduledFor || new Date(b.scheduledFor).getTime() <= Date.now())

  return [
    { label: 'Order placed', state: 'done', sublabel: formatDateTime(b.createdAt) },
    { label: 'Pal accepted', state: accepted ? 'done' : 'pending', sublabel: accepted ? 'Confirmed' : 'Awaiting response' },
    {
      label: 'In session',
      state: completed ? 'done' : sessionStarted ? 'active' : 'pending',
      sublabel: completed
        ? 'Finished'
        : sessionStarted
          ? 'In progress'
          : b.scheduledFor
            ? `Starts ${formatScheduled(b.scheduledFor)}`
            : 'Pending',
    },
    { label: 'Completed', state: completed ? 'done' : 'pending', sublabel: completed ? 'Done' : 'Pending' },
  ]
})

function isCancellable(bookingStatus: BookingStatus) {
  return bookingStatus === 'pending' || bookingStatus === 'accepted'
}

const cancelModalOpen = ref(false)
const refundModalOpen = ref(false)

async function confirmCancel(payload: CancelPayload) {
  if (!booking.value) return
  try {
    booking.value = await bookingsStore.cancelBooking(booking.value.id, payload)
  } catch (err) {
    toast.add({
      title: 'Could not cancel order',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    cancelModalOpen.value = false
  }
}

async function handleMessage() {
  const participantId = booking.value?.playerUserId
  if (!participantId) {
    toast.add({ title: "Can't message this Pal yet", color: 'error' })
    return
  }
  try {
    await messagesStore.startThread(participantId)
    router.push('/messages')
  } catch (err) {
    toast.add({
      title: "Couldn't start chat",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}

async function confirmRefundRequest(payload: DisputePayload) {
  if (!booking.value) return
  try {
    await bookingsStore.reportIssue(booking.value.id, payload)
    toast.add({
      title: 'Request submitted',
      description: "We'll get back to you within 24 hours.",
      color: 'success',
    })
  } catch (err) {
    toast.add({
      title: 'Could not submit request',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}
</script>

<template>
  <div v-if="!booking" class="flex min-h-[60vh] items-center justify-center px-4 py-16">
    <UEmpty title="This order could not be found" description="It may have expired. Browse Pals to start a new booking.">
      <template #actions>
        <UButton color="primary" class="rounded-full" @click="router.push('/players')">Browse Players</UButton>
      </template>
    </UEmpty>
  </div>

  <div v-else class="mx-auto max-w-4/5 px-4 pt-8 pb-14 md:px-6">
    <button
      type="button"
      class="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-white"
      @click="router.push('/bookings')"
    >
      <PhCaretLeft :size="14" weight="bold" />
      Order history
    </button>

    <div class="mt-3 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-3xl font-bold text-white">Order #{{ booking.orderNumber }}</h1>
        <p class="mt-1 text-sm text-slate-400">Placed {{ formatDateTime(booking.createdAt) }}</p>
      </div>
      <span
        v-if="status"
        class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium"
        :class="statusBadgeStyles[status.key]"
      >
        <span class="size-1.5 rounded-full bg-current" />
        {{ status.label }}
      </span>
    </div>

    <div class="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
      <div class="flex flex-col gap-4">
        <div class="rounded-xl bg-gray-800/70 p-5">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <UAvatar :src="palAvatarUrl" size="lg" class="bg-white/10 text-slate-300">
                <PhUserCircle :size="26" />
              </UAvatar>
              <div>
                <p class="inline-flex items-center gap-1.5 font-semibold text-white">
                  {{ palName }}
                  <span v-if="player?.rating" class="inline-flex items-center gap-1 text-sm font-normal text-amber-400">
                    <PhStar :size="12" weight="fill" />
                    {{ player.rating.toFixed(1) }}
                  </span>
                </p>
                <p class="text-sm text-slate-400">
                  <template v-if="player?.games?.[0]">{{ player.games[0] }} · </template>{{ serviceTitle }}
                </p>
              </div>
            </div>
            <UButton color="neutral" variant="soft" size="sm" class="rounded-full" @click="handleMessage">
              Message
            </UButton>
          </div>

          <div class="mt-4 flex flex-col divide-y divide-white/10 border-t border-white/10 text-sm">
            <div class="flex items-center justify-between py-3">
              <span class="text-slate-400">Service type</span>
              <span class="font-medium text-white">{{ serviceTitle }}</span>
            </div>
            <div class="flex items-center justify-between py-3">
              <span class="text-slate-400">Games</span>
              <span class="font-medium text-white">{{ booking.quantity }} game{{ booking.quantity === 1 ? '' : 's' }}</span>
            </div>
            <div class="flex items-center justify-between py-3">
              <span class="text-slate-400">Scheduled</span>
              <span class="font-medium text-white">{{ formatScheduled(booking.scheduledFor) }}</span>
            </div>
            <div class="flex items-center justify-between py-3">
              <span class="text-slate-400">Platform</span>
              <span class="font-medium text-white">SquadUp</span>
            </div>
          </div>
        </div>

        <div class="rounded-xl bg-gray-800/70 p-5">
          <h2 class="text-lg font-bold text-white">Order status</h2>
          <div class="mt-4 flex flex-col">
            <div v-for="(step, index) in timelineSteps" :key="step.label" class="flex gap-4">
              <div class="flex flex-col items-center">
                <span
                  v-if="step.state === 'done'"
                  class="flex size-6 shrink-0 items-center justify-center rounded-full bg-brand-600"
                >
                  <PhCheck :size="14" weight="bold" class="text-white" />
                </span>
                <span
                  v-else
                  class="flex size-6 shrink-0 items-center justify-center rounded-full border-2"
                  :class="{
                    'border-brand-500': step.state === 'active',
                    'border-gray-700': step.state === 'pending',
                    'border-red-500': step.state === 'cancelled',
                  }"
                >
                  <span
                    class="size-2 rounded-full"
                    :class="{
                      'bg-brand-400': step.state === 'active',
                      'bg-gray-600': step.state === 'pending',
                      'bg-red-500': step.state === 'cancelled',
                    }"
                  />
                </span>
                <span
                  v-if="index < timelineSteps.length - 1"
                  class="my-1 w-0.5 flex-1"
                  :class="step.state === 'done' ? 'bg-brand-600' : 'bg-gray-700'"
                />
              </div>
              <div class="pb-6">
                <p class="font-semibold text-white">{{ step.label }}</p>
                <p class="text-sm text-slate-400">{{ step.sublabel }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-3">
        <div class="rounded-xl bg-gray-800/70 p-5">
          <h2 class="text-lg font-bold text-white">Payment</h2>
          <div class="mt-3 flex flex-col gap-2 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Subtotal</span>
              <span class="inline-flex items-center gap-1 font-medium text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ booking.subtotalCoins }}
              </span>
            </div>
            <div v-if="booking.promoLabel" class="flex items-center justify-between">
              <span class="text-slate-400">{{ booking.promoLabel }}</span>
              <span class="text-slate-300">− {{ booking.discountCoins }} SC</span>
            </div>
          </div>

          <div class="mt-3 flex items-center justify-between border-t border-white/10 pt-3">
            <span class="text-base font-bold text-white">Total paid</span>
            <span class="inline-flex items-center gap-1 text-lg font-bold text-brand-400">
              <img :src="coinIcon" alt="" class="h-4 w-4" />
              {{ booking.totalCoins }}
            </span>
          </div>

          <div class="mt-4 flex items-start gap-2 rounded-lg bg-brand-500/10 p-3 text-xs text-brand-300">
            <PhLock :size="16" weight="fill" class="mt-0.5 shrink-0" />
            <span>Held in escrow, released to the Pal when the order completes.</span>
          </div>
        </div>

        <UButton color="primary" block size="lg" class="rounded-full" @click="handleMessage">
          Message {{ palName }}
        </UButton>
        <UButton color="neutral" variant="soft" block size="lg" class="rounded-full" @click="refundModalOpen = true">
          Report an issue
        </UButton>
        <button
          v-if="isCancellable(booking.status)"
          type="button"
          class="cursor-pointer py-1 text-sm font-medium text-red-400 hover:text-red-300"
          @click="cancelModalOpen = true"
        >
          Cancel order
        </button>
      </div>
    </div>

    <CancelOrderModal
      v-model:open="cancelModalOpen"
      :order-number="booking.orderNumber"
      :pal-name="palName"
      :service-title="serviceTitle"
      :meta="`${booking.quantity} ${booking.quantity === 1 ? 'game' : 'games'} · ${status?.label ?? ''}`"
      :total-coins="booking.totalCoins"
      @confirm="confirmCancel"
    />

    <RefundModal
      v-model:open="refundModalOpen"
      :order-number="booking.orderNumber"
      :pal-name="palName"
      :service-title="serviceTitle"
      :meta="`${booking.quantity} ${booking.quantity === 1 ? 'game' : 'games'} · ${status?.label ?? ''}`"
      :total-coins="booking.totalCoins"
      @confirm="confirmRefundRequest"
    />
  </div>
</template>
