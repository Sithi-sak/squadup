<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhMinus, PhPlus } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { useBookingsStore, type Booking, type BookingAddon } from '@/stores/bookings'
import { mockAddons } from '@/mocks/bookings'
import { mockCurrentUser } from '@/mocks/users'
import type { ServiceTypeOption } from '@/stores/players'

const props = defineProps<{
  playerId: string
  serviceId: string
  palName: string
  palTagline: string
  palRating: number | null
  palServedCount: number
  serviceType: ServiceTypeOption
}>()

const open = defineModel<boolean>('open', { required: true })

const router = useRouter()
const bookingsStore = useBookingsStore()

const quantity = ref(1)
const selectedAddonIds = ref<Set<string>>(new Set(['priority-matchmaking', 'highlights']))
const promoCode = ref('')
const promoCodeMessage = ref('')
const appliedPromoCodePercent = ref(0)

function unitLabel() {
  const unit = props.serviceType.priceUnit.replace(/^\//, '').toLowerCase()
  if (unit.includes('min')) return 'sessions'
  if (unit.endsWith('s')) return unit
  return `${unit}s`
}

function toggleAddon(id: string) {
  if (selectedAddonIds.value.has(id)) selectedAddonIds.value.delete(id)
  else selectedAddonIds.value.add(id)
}

function applyPromoCode() {
  const code = promoCode.value.trim().toUpperCase()
  if (!code) return
  if (code === 'SQUAD10') {
    appliedPromoCodePercent.value = 10
    promoCodeMessage.value = 'Promo code applied: 10% off'
  } else {
    appliedPromoCodePercent.value = 0
    promoCodeMessage.value = 'Invalid promo code'
  }
}

const autoPromoPercent = computed(() => {
  const match = props.serviceType.promoBadge?.match(/(\d+)%/)
  return match ? Number(match[1]) : 0
})

const effectivePromoPercent = computed(() => Math.max(autoPromoPercent.value, appliedPromoCodePercent.value))
const promoLabel = computed(() => {
  if (appliedPromoCodePercent.value > 0) return promoCodeMessage.value
  if (autoPromoPercent.value > 0) return `${props.serviceType.promoBadge} applied`
  return null
})

const selectedAddons = computed<BookingAddon[]>(() =>
  mockAddons.filter((addon) => selectedAddonIds.value.has(addon.id)),
)

const subtotal = computed(() => props.serviceType.priceCoins * quantity.value)
const addonsTotal = computed(() => selectedAddons.value.reduce((sum, addon) => sum + addon.priceCoins, 0))
const discount = computed(() =>
  Math.round(((subtotal.value + addonsTotal.value) * effectivePromoPercent.value) / 100),
)
const total = computed(() => subtotal.value + addonsTotal.value - discount.value)

function generateOrderNumber() {
  return `SQ-${Math.floor(10000 + Math.random() * 90000)}`
}

function continueToCheckout() {
  const booking: Booking = {
    id: `bk-${Date.now()}`,
    orderNumber: generateOrderNumber(),
    playerId: props.playerId,
    serviceId: props.serviceId,
    userId: mockCurrentUser.id,
    status: 'pending',
    serviceTypeLabel: props.serviceType.label,
    priceCoins: props.serviceType.priceCoins,
    priceUnit: props.serviceType.priceUnit,
    quantity: quantity.value,
    addons: selectedAddons.value,
    promoLabel: promoLabel.value,
    subtotalCoins: subtotal.value,
    addonsCoins: addonsTotal.value,
    discountCoins: discount.value,
    totalCoins: total.value,
    paymentMethod: 'coins',
    scheduledFor: null,
    createdAt: new Date().toISOString(),
  }
  bookingsStore.addBooking(booking)
  open.value = false
  router.push(`/checkout/${booking.id}`)
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Book a session"
    :ui="{ content: 'max-w-5xl rounded-2xl', body: 'p-0 sm:p-0 overflow-hidden' }"
  >
    <template #body>
      <div class="grid h-full grid-cols-1 sm:grid-cols-[2fr_1fr]">
        <div class="flex flex-col gap-5 overflow-y-auto p-4 sm:p-6">
          <div class="flex items-center gap-3 rounded-2xl bg-gray-800/70 p-4">
            <div class="h-12 w-12 shrink-0 rounded-full bg-white/10" />
            <div class="min-w-0">
              <p class="truncate font-semibold text-white">{{ palName }}</p>
              <p class="truncate text-sm text-slate-400">
                {{ palTagline }} · ★ {{ palRating ? palRating.toFixed(1) : '--' }} · {{ palServedCount.toLocaleString() }} served
              </p>
            </div>
          </div>

          <div>
            <p class="text-sm font-medium text-slate-300">Service type</p>
            <div class="mt-2 flex items-center justify-between rounded-full bg-gray-800/70 px-4 py-3">
              <span class="text-sm font-medium text-white">{{ serviceType.label }}</span>
              <span class="inline-flex items-center gap-1 text-sm font-semibold text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ serviceType.priceCoins }}{{ serviceType.priceUnit }}
              </span>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <p class="text-sm font-medium text-slate-300">Quantity ({{ unitLabel() }})</p>
            <div class="flex items-center gap-3">
              <UButton
                color="neutral"
                variant="soft"
                square
                size="sm"
                :ui="{ base: 'rounded-full' }"
                :disabled="quantity <= 1"
                aria-label="Decrease quantity"
                @click="quantity = Math.max(1, quantity - 1)"
              >
                <PhMinus :size="14" weight="bold" />
              </UButton>
              <span class="w-4 text-center font-semibold text-white">{{ quantity }}</span>
              <UButton
                color="neutral"
                variant="soft"
                square
                size="sm"
                :ui="{ base: 'rounded-full' }"
                aria-label="Increase quantity"
                @click="quantity += 1"
              >
                <PhPlus :size="14" weight="bold" />
              </UButton>
            </div>
          </div>

          <div>
            <p class="text-sm font-medium text-slate-300">Add-ons</p>
            <div class="mt-2 flex flex-col gap-2">
              <button
                v-for="addon in mockAddons"
                :key="addon.id"
                type="button"
                class="flex items-center justify-between gap-3 rounded-full px-4 py-4 text-left ring-1 ring-inset transition-colors"
                :class="
                  selectedAddonIds.has(addon.id)
                    ? 'bg-brand-900/30 ring-brand-500'
                    : 'bg-gray-800/70 ring-transparent hover:ring-gray-700'
                "
                @click="toggleAddon(addon.id)"
              >
                <span class="inline-flex items-center gap-2 text-sm text-white">
                  <UCheckbox :model-value="selectedAddonIds.has(addon.id)" color="primary" @update:model-value="toggleAddon(addon.id)" @click.stop />
                  {{ addon.label }}
                </span>
                <span class="inline-flex items-center gap-1 text-sm font-medium text-white">
                  <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                  +{{ addon.priceCoins }}
                </span>
              </button>
            </div>
          </div>
        </div>

        <div class="flex h-full flex-col gap-2 border-t border-white/10 p-4 sm:border-t-0 sm:border-l sm:p-6">
          <div class="flex gap-2">
            <UInput v-model="promoCode" placeholder="Enter promo code" class="flex-1" @keyup.enter="applyPromoCode" />
            <UButton :ui="{ base: 'rounded-full '}" color="primary" @click="applyPromoCode">Apply</UButton>
          </div>
          <p v-if="promoLabel" class="text-xs font-medium text-brand-400">{{ promoLabel }}</p>

          <div class="mt-3 flex flex-col gap-2 border-t border-white/10 pt-4 text-sm">
            <div class="flex items-center justify-between text-slate-300">
              <span>Subtotal ({{ quantity }} {{ unitLabel() }})</span>
              <span class="inline-flex items-center gap-1">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ subtotal }}
              </span>
            </div>
            <div v-if="addonsTotal > 0" class="flex items-center justify-between text-slate-300">
              <span>Add-ons</span>
              <span class="inline-flex items-center gap-1">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ addonsTotal }}
              </span>
            </div>
            <div v-if="discount > 0" class="flex items-center justify-between text-brand-400">
              <span>Discount</span>
              <span class="inline-flex items-center gap-1">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                -{{ discount }}
              </span>
            </div>
            <div class="flex items-center justify-between pt-1 text-base font-bold text-white">
              <span>Total</span>
              <span class="inline-flex items-center gap-1">
                <img :src="coinIcon" alt="" class="h-4 w-4" />
                {{ total }}
              </span>
            </div>
          </div>

          <UButton color="primary" block size="lg" class="mt-auto rounded-full" @click="continueToCheckout">
            Continue to checkout
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
