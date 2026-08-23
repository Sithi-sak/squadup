<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhCheck } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { useBookingsStore } from '@/stores/bookings'
import { mockPlayers } from '@/mocks/players'
import { getPlayerProfile } from '@/mocks/playerProfiles'

const route = useRoute()
const router = useRouter()
const bookingsStore = useBookingsStore()

const booking = computed(() => bookingsStore.getBooking(String(route.params.bookingId)))
const player = computed(() => mockPlayers.find((p) => p.id === booking.value?.playerId) ?? null)
const profile = computed(() => (player.value ? getPlayerProfile(player.value) : null))
const detail = computed(() => (booking.value ? profile.value?.serviceDetails[booking.value.serviceId] : null))

const palName = computed(() => booking.value?.playerDisplayName ?? player.value?.displayName ?? 'your Pal')
const serviceTitle = computed(() => booking.value?.serviceName ?? detail.value?.title ?? booking.value?.serviceTypeLabel)

const placedAt = computed(() => {
  if (!booking.value) return ''
  return new Date(booking.value.createdAt).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
})
</script>

<template>
  <div v-if="!booking" class="flex min-h-[60vh] items-center justify-center px-4 py-16">
    <UEmpty title="This order could not be found" description="It may have expired. Browse Pals to start a new booking.">
      <template #actions>
        <UButton color="primary" class="rounded-full" @click="router.push('/players')">Browse Players</UButton>
      </template>
    </UEmpty>
  </div>

  <div v-else class="mx-auto flex max-w-lg flex-col items-center px-4 py-16 text-center">
    <div class="flex size-16 items-center justify-center rounded-full bg-brand-500">
      <PhCheck :size="32" weight="bold" class="text-white" />
    </div>
    <h1 class="mt-6 text-3xl font-bold text-white">Order placed!</h1>
    <p class="mt-2 text-sm text-slate-400">
      Your request was sent to {{ palName }}. You can start chatting now, coins are only deducted when
      the session begins.
    </p>

    <div class="mt-6 w-full rounded-xl bg-gray-800/70 p-5 text-left">
      <div class="flex items-center justify-between">
        <span class="text-lg font-bold text-white">Order #{{ booking.orderNumber }}</span>
        <span class="text-sm font-medium text-amber-400 capitalize">{{ booking.status }}</span>
      </div>

      <div class="mt-4 flex flex-col gap-2 border-t border-white/10 pt-4 text-sm">
        <div class="flex items-center justify-between">
          <span class="text-slate-400">Pal</span>
          <span class="font-medium text-white">{{ palName }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-slate-400">Service</span>
          <span class="font-medium text-white">{{ serviceTitle }} · {{ booking.serviceTypeLabel }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-slate-400">Quantity</span>
          <span class="font-medium text-white">{{ booking.quantity }}</span>
        </div>
        <div v-if="booking.addons.length" class="flex items-center justify-between">
          <span class="text-slate-400">Add-ons</span>
          <span class="font-medium text-white">{{ booking.addons.map((a) => a.label).join(', ') }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-slate-400">Date</span>
          <span class="font-medium text-white">{{ placedAt }}</span>
        </div>
      </div>

      <div class="mt-3 flex items-center justify-between border-t border-white/10 pt-3">
        <span class="text-base font-bold text-white">Total to be paid</span>
        <span class="inline-flex items-center gap-1 text-lg font-bold text-white">
          <img :src="coinIcon" alt="" class="h-4 w-4" />
          {{ booking.totalCoins }}
        </span>
      </div>
    </div>

    <div class="mt-6 flex w-full gap-3">
      <UButton color="primary" block size="lg" class="rounded-full" @click="router.push('/messages')">
        Message your Pal
      </UButton>
      <UButton color="neutral" variant="soft" block size="lg" class="rounded-full" @click="router.push('/bookings')">
        View order
      </UButton>
    </div>
    <p class="mt-4 text-xs text-slate-400">A receipt was emailed to you. Manage in Wallet → History.</p>
  </div>
</template>
