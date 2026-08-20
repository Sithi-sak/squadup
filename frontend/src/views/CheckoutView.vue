<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhCalendarBlank, PhCaretLeft, PhCreditCard } from '@phosphor-icons/vue'
import { CalendarDateTime, getLocalTimeZone, now, toCalendarDate, type CalendarDate } from '@internationalized/date'
import coinIcon from '@/assets/squadup-coin.svg'
import { useBookingsStore, type PaymentMethod } from '@/stores/bookings'
import { mockPlayers } from '@/mocks/players'
import { getPlayerProfile } from '@/mocks/playerProfiles'
import { mockCurrentUser } from '@/mocks/users'

const route = useRoute()
const router = useRouter()
const bookingsStore = useBookingsStore()

const booking = computed(() => bookingsStore.getBooking(String(route.params.bookingId)))
const player = computed(() => mockPlayers.find((p) => p.id === booking.value?.playerId) ?? null)
const profile = computed(() => (player.value ? getPlayerProfile(player.value) : null))
const detail = computed(() => (booking.value ? profile.value?.serviceDetails[booking.value.serviceId] : null))

const paymentMethod = ref<PaymentMethod>('coins')
const startChoice = ref<'now' | 'schedule'>('now')
const scheduledAt = ref<CalendarDateTime>()

const scheduledDate = computed({
  get: (): CalendarDate | undefined => (scheduledAt.value ? toCalendarDate(scheduledAt.value) : undefined),
  set: (value: CalendarDate | undefined) => {
    if (!value) return
    const time = scheduledAt.value ?? now(getLocalTimeZone())
    scheduledAt.value = new CalendarDateTime(value.year, value.month, value.day, time.hour, time.minute)
  },
})

const remainingBalance = computed(() =>
  booking.value ? mockCurrentUser.coinBalance - booking.value.totalCoins : mockCurrentUser.coinBalance,
)

function placeOrder() {
  if (!booking.value) return
  booking.value.paymentMethod = paymentMethod.value
  booking.value.scheduledFor =
    startChoice.value === 'schedule' && scheduledAt.value
      ? scheduledAt.value.toDate(getLocalTimeZone()).toISOString()
      : null
  router.push(`/checkout/${booking.value.id}/confirmation`)
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

  <div v-else class="mx-auto max-w-(--content-max-width) px-4 pt-8 pb-14 md:px-6">
    <button
      type="button"
      class="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-white"
      @click="router.back()"
    >
      <PhCaretLeft :size="14" weight="bold" />
    </button>
    <h1 class="mt-2 text-3xl font-bold text-white">Checkout</h1>

    <div class="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
      <div class="flex flex-col gap-4">
        <div class="rounded-xl bg-gray-800/70 p-5">
          <h2 class="text-lg font-bold text-white">Order summary</h2>
          <div v-if="player" class="mt-3 flex items-center gap-3">
            <div class="h-10 w-10 shrink-0 rounded-full bg-white/10" />
            <div>
              <p class="font-medium text-white">{{ player.displayName }} · {{ detail?.title }}</p>
              <p class="inline-flex items-center gap-1 text-xs text-slate-400">
                ★ {{ detail?.rating ? detail.rating.toFixed(1) : '--' }} · {{ detail?.servedCount.toLocaleString() ?? 0 }} served
              </p>
            </div>
          </div>

          <div class="mt-4 flex flex-col gap-2 border-t border-white/10 pt-4 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-slate-300">{{ booking.serviceTypeLabel }} ×{{ booking.quantity }}</span>
              <span class="inline-flex items-center gap-1 font-medium text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ booking.subtotalCoins }}
              </span>
            </div>
            <div v-for="addon in booking.addons" :key="addon.id" class="flex items-center justify-between">
              <span class="text-slate-300">{{ addon.label }}</span>
              <span class="inline-flex items-center gap-1 font-medium text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ addon.priceCoins }}
              </span>
            </div>
          </div>
        </div>

        <div class="rounded-xl bg-gray-800/70 p-5">
          <h2 class="text-lg font-bold text-white">Payment method</h2>
          <div class="mt-3 flex flex-col gap-3">
            <button
              type="button"
              class="flex items-center justify-between gap-3 rounded-full px-4 py-3 text-left ring-1 ring-inset transition-colors"
              :class="paymentMethod === 'coins' ? 'ring-brand-500 bg-brand-900/20' : 'ring-gray-700 hover:ring-gray-600'"
              @click="paymentMethod = 'coins'"
            >
              <span class="flex items-center gap-3">
                <img :src="coinIcon" alt="" class="h-6 w-6" />
                <span>
                  <span class="block font-medium text-white">Squad Coin balance</span>
                  <span class="block text-xs text-slate-400">{{ mockCurrentUser.coinBalance.toLocaleString() }} SC available</span>
                </span>
              </span>
              <span
                class="flex size-5 shrink-0 items-center justify-center rounded-full ring-1 ring-inset"
                :class="paymentMethod === 'coins' ? 'bg-brand-500 ring-brand-500' : 'ring-slate-500'"
              >
                <span v-if="paymentMethod === 'coins'" class="size-2 rounded-full bg-white" />
              </span>
            </button>

            <p v-if="paymentMethod === 'coins'" class="text-xs font-medium text-brand-400">
              After this order: {{ remainingBalance.toLocaleString() }} SC left
            </p>

            <button
              type="button"
              class="flex items-center justify-between gap-3 rounded-full px-4 py-3 text-left ring-1 ring-inset transition-colors"
              :class="paymentMethod === 'card' ? 'ring-brand-500 bg-brand-900/20' : 'ring-gray-700 hover:ring-gray-600'"
              @click="paymentMethod = 'card'"
            >
              <span class="flex items-center gap-3">
                <PhCreditCard :size="24" class="text-slate-300" />
                <span>
                  <span class="block font-medium text-white">Credit / debit card</span>
                  <span class="block text-xs text-slate-400">Visa, Mastercard, Amex</span>
                </span>
              </span>
              <span
                class="flex size-5 shrink-0 items-center justify-center rounded-full ring-1 ring-inset"
                :class="paymentMethod === 'card' ? 'bg-brand-500 ring-brand-500' : 'ring-slate-500'"
              >
                <span v-if="paymentMethod === 'card'" class="size-2 rounded-full bg-white" />
              </span>
            </button>
          </div>
        </div>

        <div class="rounded-xl bg-gray-800/70 p-5">
          <h2 class="text-lg font-bold text-white">Start time</h2>
          <div class="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <button
              type="button"
              class="rounded-full px-6 py-3 text-left ring-1 ring-inset transition-colors"
              :class="startChoice === 'now' ? 'ring-brand-500 bg-brand-900/20' : 'ring-gray-700 hover:ring-gray-600'"
              @click="startChoice = 'now'"
            >
              <span class="block font-medium text-white">Start now</span>
              <span class="block text-xs text-slate-400">Pal notified instantly</span>
            </button>
            <button
              type="button"
              class="rounded-full px-6 py-3 text-left ring-1 ring-inset transition-colors"
              :class="startChoice === 'schedule' ? 'ring-brand-500 bg-brand-900/20' : 'ring-gray-700 hover:ring-gray-600'"
              @click="startChoice = 'schedule'"
            >
              <span class="block font-medium text-white">Schedule</span>
              <span class="block text-xs text-slate-400">Pick a later time</span>
            </button>
          </div>
          <div v-if="startChoice === 'schedule'" class="mt-3 flex items-center gap-2">
            <UInputDate v-model="scheduledAt" granularity="minute" class="flex-1" />
            <UPopover>
              <UButton color="neutral" variant="soft" square :ui="{ base: 'rounded-full' }" aria-label="Pick a date">
                <PhCalendarBlank :size="16" weight="bold" />
              </UButton>
              <template #content>
                <UCalendar v-model="scheduledDate" class="p-2" />
              </template>
            </UPopover>
          </div>
        </div>
      </div>

      <div class="h-fit rounded-xl bg-gray-800/70 p-5 lg:sticky lg:top-24">
        <h2 class="text-lg font-bold text-white">Summary</h2>
        <div class="mt-3 flex flex-col gap-2 text-sm">
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Subtotal</span>
            <span class="inline-flex items-center gap-1 font-medium text-white">
              <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
              {{ booking.subtotalCoins }}
            </span>
          </div>
          <div v-if="booking.addonsCoins > 0" class="flex items-center justify-between">
            <span class="text-slate-400">Add-ons</span>
            <span class="inline-flex items-center gap-1 font-medium text-white">
              <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
              {{ booking.addonsCoins }}
            </span>
          </div>
          <div v-if="booking.discountCoins > 0" class="flex items-center justify-between text-brand-400">
            <span>Discount</span>
            <span class="inline-flex items-center gap-1">
              <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
              -{{ booking.discountCoins }}
            </span>
          </div>
        </div>

        <div class="mt-3 flex items-center justify-between border-t border-white/10 pt-3">
          <span class="text-lg font-bold text-white">Total</span>
          <span class="inline-flex items-center gap-1 text-lg font-bold text-white">
            <img :src="coinIcon" alt="" class="h-4 w-4" />
            {{ booking.totalCoins }}
          </span>
        </div>

        <UButton color="primary" block size="lg" class="mt-4 rounded-full" @click="placeOrder">Place order</UButton>
        <p class="mt-3 text-center text-xs text-slate-400">
          Coins are deducted when the session starts. By ordering you agree to the Pal Terms.
        </p>

        <p v-if="player" class="mt-4 rounded-full bg-white/5 px-3 py-2 text-center text-xs text-slate-400">
          <span class="mr-1 inline-block h-1.5 w-1.5 rounded-full" :class="player.online ? 'bg-brand-400' : 'bg-slate-500'" />
          {{ player.displayName }} is {{ player.online ? 'online' : 'offline' }} · avg reply {{ detail?.avgResponseTime }}
        </p>
      </div>
    </div>
  </div>
</template>
