<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhStar, PhTrendUp, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import DashboardLayout from '@/components/dashboard/DashboardLayout.vue'
import DashboardBarChart from '@/components/dashboard/DashboardBarChart.vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { mockCurrentUser } from '@/mocks/users'
import { mockPalDashboardStats } from '@/mocks/dashboardStats'
import { getBuyer } from '@/mocks/buyers'
import { orderStatusMeta } from '@/utils/orderStatus'
import { useBookingsStore, type Booking } from '@/stores/bookings'

const router = useRouter()
const bookingsStore = useBookingsStore()
const toast = useToast()
const stats = mockPalDashboardStats

onMounted(() => {
  bookingsStore.fetchIncoming()
})

const actingOn = ref<string | null>(null)

const today = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })

const activeOrders = computed(() =>
  [...bookingsStore.incoming]
    .filter((b) => b.status === 'pending' || b.status === 'accepted')
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()),
)

const waitingCount = computed(() => activeOrders.value.filter((b) => b.status === 'pending').length)

const upcomingSchedule = computed(() =>
  activeOrders.value
    .filter((b) => b.scheduledFor)
    .sort((a, b) => new Date(a.scheduledFor!).getTime() - new Date(b.scheduledFor!).getTime()),
)

const topServices = computed(() => {
  const totals = new Map<string, { name: string; coins: number }>()
  for (const booking of bookingsStore.incoming) {
    if (booking.status === 'declined') continue
    const entry = totals.get(booking.serviceId) ?? { name: booking.serviceName ?? booking.serviceTypeLabel, coins: 0 }
    entry.coins += booking.totalCoins
    totals.set(booking.serviceId, entry)
  }
  return [...totals.entries()]
    .map(([serviceId, { name, coins }]) => ({ serviceId, name, coins }))
    .sort((a, b) => b.coins - a.coins)
})

function buyerName(booking: Booking) {
  return booking.buyerDisplayName ?? getBuyer(booking.userId)?.displayName ?? 'Buyer'
}

async function respond(booking: Booking, action: 'accept' | 'decline') {
  actingOn.value = booking.id
  try {
    if (action === 'accept') await bookingsStore.acceptBooking(booking.id)
    else await bookingsStore.declineBooking(booking.id)
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

function formatScheduled(iso: string) {
  return new Date(iso).toLocaleString('en-US', { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}
</script>

<template>
  <DashboardLayout active="dashboard">
    <div class="flex h-full flex-col gap-6 overflow-y-auto pr-1">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-white sm:text-3xl">
            Welcome back, {{ (mockCurrentUser.displayName ?? 'Pal').split(' ')[0] }} 👋
          </h1>
          <p class="mt-1 text-sm text-slate-400">
            {{ today }}
            <span v-if="waitingCount"> · {{ waitingCount }} new order{{ waitingCount > 1 ? 's' : '' }} waiting</span>
          </p>
        </div>
        <UButton color="primary" class="rounded-full" @click="router.push('/dashboard/player/services/new')">
          New Service
        </UButton>
      </div>

      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div class="flex flex-col rounded-xl bg-gray-800/70 p-5">
          <p class="text-sm text-slate-400">This month</p>
          <p class="mt-2 flex items-center gap-1.5 text-2xl font-bold text-white">
            <img :src="coinIcon" alt="" class="h-5 w-5" />
            {{ mockCurrentUser.coinBalance.toLocaleString() }}
          </p>
          <p class="mt-auto inline-flex items-center gap-1 pt-1 text-xs text-brand-400">
            <PhTrendUp :size="14" weight="bold" />
            {{ stats.coinsThisMonthChangePct }}% · ~${{ stats.usdEquivalentThisMonth.toFixed(2) }}
          </p>
        </div>
        <div class="flex flex-col rounded-xl bg-gray-800/70 p-5">
          <p class="text-sm text-slate-400">Orders completed</p>
          <p class="mt-2 text-2xl font-bold text-white">{{ stats.ordersCompleted }}</p>
          <p class="mt-auto inline-flex items-center gap-1 pt-1 text-xs text-brand-400">
            <PhTrendUp :size="14" weight="bold" />
            {{ stats.ordersCompletedThisWeek }} this week
          </p>
        </div>
        <div class="flex flex-col rounded-xl bg-gray-800/70 p-5">
          <p class="text-sm text-slate-400">Avg rating</p>
          <p class="mt-2 inline-flex items-center gap-1.5 text-2xl font-bold text-white">
            <PhStar :size="20" weight="fill" class="text-amber-400" />
            {{ stats.avgRating.toFixed(1) }}
          </p>
          <p class="mt-auto pt-1 text-xs text-slate-400">From {{ stats.reviewCount }} reviews</p>
        </div>
        <div class="flex flex-col rounded-xl bg-gray-800/70 p-5">
          <p class="text-sm text-slate-400">Response rate</p>
          <p class="mt-2 text-2xl font-bold text-white">{{ stats.responseRatePct }}%</p>
          <p class="mt-auto pt-1 text-xs text-slate-400">Avg {{ stats.avgResponseTime }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
        <div class="rounded-xl bg-gray-800/70 p-5">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-white">Incoming orders</h2>
            <button
              type="button"
              class="cursor-pointer text-sm font-medium text-brand-400 hover:text-brand-300"
              @click="router.push('/dashboard/player/orders')"
            >
              View all
            </button>
          </div>

          <UEmpty
            v-if="activeOrders.length === 0"
            title="No incoming orders"
            description="New orders from buyers will show up here."
            class="py-10 text-white"
          />

          <div v-else class="mt-3 flex flex-col divide-y divide-white/10">
            <div
              v-for="booking in activeOrders"
              :key="booking.id"
              class="flex flex-wrap items-center justify-between gap-3 py-3"
            >
              <div class="flex items-center gap-3">
                <UAvatar size="md" class="bg-white/10 text-slate-300">
                  <PhUserCircle :size="22" />
                </UAvatar>
                <div>
                  <p class="font-semibold text-white">{{ buyerName(booking) }}</p>
                  <p class="text-sm text-slate-400">
                    {{ booking.serviceTypeLabel }}
                    <span v-if="booking.quantity > 1"> · {{ booking.quantity }} games</span>
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <span class="inline-flex items-center gap-1 text-sm font-semibold text-white">
                  <img :src="coinIcon" alt="" class="h-4 w-4" />
                  {{ booking.totalCoins }}
                </span>
                <template v-if="booking.status === 'pending'">
                  <UButton
                    color="primary"
                    size="sm"
                    class="rounded-full"
                    :loading="actingOn === booking.id"
                    @click="respond(booking, 'accept')"
                  >
                    Accept
                  </UButton>
                  <UButton
                    color="neutral"
                    variant="soft"
                    size="sm"
                    class="rounded-full"
                    :loading="actingOn === booking.id"
                    @click="respond(booking, 'decline')"
                  >
                    Decline
                  </UButton>
                </template>
                <span v-else class="text-sm font-medium" :class="orderStatusMeta(booking).class">
                  {{ orderStatusMeta(booking).label }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-4">
          <div class="rounded-xl bg-gray-800/70 p-5">
            <h2 class="text-lg font-semibold text-white">Earnings this week</h2>
            <div class="mt-4 h-32">
              <DashboardBarChart :bars="stats.earningsThisWeek.map((b) => ({ label: b.day, value: b.coins }))" />
            </div>
          </div>

          <div class="rounded-xl bg-gray-800/70 p-5">
            <h2 class="text-lg font-semibold text-white">Top services</h2>
            <div class="mt-3 flex flex-col gap-3">
              <div v-for="service in topServices" :key="service.serviceId" class="flex items-center justify-between text-sm">
                <span class="text-slate-300">{{ service.name }}</span>
                <span class="inline-flex items-center gap-1 font-semibold text-white">
                  <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                  {{ service.coins.toLocaleString() }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-xl bg-gray-800/70 p-5">
        <h2 class="text-lg font-semibold text-white">Upcoming Schedule</h2>
        <UEmpty
          v-if="upcomingSchedule.length === 0"
          title="No upcoming sessions"
          description="Scheduled orders will show up here."
          class="py-8 text-white"
        />
        <div v-else class="mt-3 flex flex-col divide-y divide-white/10">
          <div
            v-for="booking in upcomingSchedule"
            :key="booking.id"
            class="flex flex-wrap items-center justify-between gap-3 py-3"
          >
            <div>
              <p class="font-semibold text-white">{{ buyerName(booking) }}</p>
              <p class="text-sm text-slate-400">{{ booking.serviceTypeLabel }}</p>
            </div>
            <span class="text-sm text-slate-300">{{ formatScheduled(booking.scheduledFor!) }}</span>
          </div>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>
