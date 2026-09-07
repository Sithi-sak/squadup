<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from '@nuxt/ui/composables/useToast'
import type { Stripe, StripeCardElement, StripeElements } from '@stripe/stripe-js'
import QRCode from 'qrcode'
import {
  PhArrowUp,
  PhArrowDown,
  PhHourglass,
  PhArrowCounterClockwise,
  PhProhibit,
  PhCreditCard,
  PhCaretDown,
  PhQrCode,
  PhSpinnerGap,
  PhCheckCircle,
} from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import KhqrCard from '@/components/wallet/KhqrCard.vue'
import { stripePromise } from '@/lib/stripe'
import { useAuthStore } from '@/stores/auth'
import { useWalletStore, type WalletActivity } from '@/stores/wallet'

/** $1 = 99 SC, matching the base top-up package (990 SC / $10). */
const COINS_PER_USD = 99

const walletStore = useWalletStore()
const authStore = useAuthStore()
const toast = useToast()
const route = useRoute()

const isPal = computed(() => Boolean(authStore.user?.playerId))

onMounted(() => {
  walletStore.fetchWallet()
  walletStore.fetchTopupPackages()
  loadStripe()
})
onBeforeUnmount(() => {
  cardElement?.unmount()
  stopKhqrPolling()
})

const balance = computed(() => walletStore.balance)
const usdBalance = computed(() => (balance.value / COINS_PER_USD).toFixed(2))

const paymentSectionRef = ref<HTMLDivElement | null>(null)
function scrollToPayment() {
  paymentSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

// 4.4a: "QR Scan" simulates a KHQR-style "Scan to Pay" flow (see `startKhqrTopup` below) rather
// than a real Bakong integration, which is out of scope for this project.
const paymentMethod = ref<'card' | 'khqr'>('card')
const paymentMethodItems = [
  [
    { label: 'Card', onSelect: () => (paymentMethod.value = 'card') },
    { label: 'QR Scan', onSelect: () => (paymentMethod.value = 'khqr') },
  ],
]
const paymentMethodLabel = computed(() => (paymentMethod.value === 'card' ? 'Card' : 'QR Scan'))
const paymentMethodIcon = computed(() => (paymentMethod.value === 'card' ? PhCreditCard : PhQrCode))

const selectedPackageId = ref<string | null>(null)
const basePackageId = computed(
  () => walletStore.topupPackages.find((p) => p.isBaseRate)?.id ?? walletStore.topupPackages[0]?.id ?? null,
)

function activityIcon(activity: WalletActivity) {
  if (activity.status === 'blocked') return PhProhibit
  if (activity.kind === 'topup') return PhArrowUp
  if (activity.kind === 'refund') return PhArrowCounterClockwise
  if (activity.kind === 'payout') return PhArrowDown
  return PhHourglass
}
function activityIconClass(activity: WalletActivity) {
  if (activity.status === 'blocked') return 'text-red-400'
  if (activity.kind === 'topup' || activity.kind === 'refund') return 'text-brand-400'
  return 'text-amber-400'
}

function formatDateTime(iso: string) {
  const date = new Date(iso)
  const day = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  const time = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
  return `${day} · ${time}`
}

// Stripe Elements card form (same mount pattern as PawMart's CheckoutView) - a card number/
// expiry/CVC field embedded directly on this page, since Wallet Top-up confirms the charge
// client-side rather than redirecting to a Stripe-hosted page.
const cardElementRef = ref<HTMLDivElement | null>(null)
const cardError = ref<string | null>(null)
const cardComplete = ref(false)
const stripeLoadFailed = ref(false)
let stripe: Stripe | null = null
let elements: StripeElements | null = null
let cardElement: StripeCardElement | null = null

async function loadStripe() {
  stripe = await stripePromise
  stripeLoadFailed.value = !stripe
  mountCardElementIfReady()
}

// `cardElementRef` and `stripe` become ready independently and in either order - the wallet's
// own `/wallet/me` fetch (toggling `walletStore.loading`, which the card form's `v-else` is
// gated on) races the Stripe.js script load, so a one-shot mount attempt right after `onMounted`
// can run while the div hasn't rendered yet and silently never retry. Re-running this on both
// triggers (below) makes the mount order-independent.
function mountCardElementIfReady() {
  if (cardElement || !stripe || !cardElementRef.value) return

  elements ??= stripe.elements()
  cardElement = elements.create('card', {
    hidePostalCode: true,
    style: {
      base: { color: '#dcdcdc', '::placeholder': { color: '#707070' } },
    },
  })
  cardElement.on('change', (event) => {
    cardError.value = event.error?.message ?? null
    cardComplete.value = event.complete
  })
  cardElement.mount(cardElementRef.value)
}

watch(cardElementRef, mountCardElementIfReady)

const toppingUp = ref(false)

async function topUp(packageId: string | null) {
  if (!packageId || toppingUp.value) return
  if (!stripe || !cardElement) {
    toast.add({ title: 'Payment form is not ready yet', description: 'Please try again.', color: 'error' })
    return
  }
  if (!cardComplete.value) {
    toast.add({ title: 'Enter your card details', description: 'Fill in the card form to continue.', color: 'error' })
    return
  }

  toppingUp.value = true
  try {
    const { clientSecret, paymentIntentId } = await walletStore.createTopupPaymentIntent(packageId)
    const { paymentIntent, error } = await stripe.confirmCardPayment(clientSecret, {
      payment_method: { card: cardElement },
    })
    if (error || paymentIntent?.status !== 'succeeded') {
      toast.add({ title: 'Card was declined', description: error?.message ?? 'Please try again.', color: 'error' })
      return
    }

    await walletStore.confirmTopup(packageId, paymentIntentId)
    cardElement.clear()
    toast.add({ title: 'Top-up successful', description: 'Squad Coin added to your wallet.', color: 'success' })
  } catch (err) {
    toast.add({
      title: "Couldn't complete top-up",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    toppingUp.value = false
  }
}

// 4.4: simulated KHQR "Scan to Pay" - the QR encodes a fake session reference (no real Bakong
// call), and the backend auto-confirms it a few seconds after creation, standing in for a judge
// actually scanning it with a banking app. Polling (not a websocket) matches how a real KHQR
// checkout waits on a bank webhook, just against our own fake session status instead.
const khqrModalOpen = ref(false)
const khqrQrDataUrl = ref<string | null>(null)
const khqrAmount = ref(0)
const khqrStatus = ref<'pending' | 'confirmed' | 'completed' | 'expired'>('pending')
let khqrSessionId: string | null = null
let khqrPollTimer: ReturnType<typeof setInterval> | null = null

function stopKhqrPolling() {
  if (khqrPollTimer) {
    clearInterval(khqrPollTimer)
    khqrPollTimer = null
  }
}

async function pollKhqrStatus() {
  if (!khqrSessionId) return
  const { status: s } = await walletStore.getKhqrStatus(khqrSessionId)
  khqrStatus.value = s

  if (s === 'confirmed') {
    stopKhqrPolling()
    try {
      await walletStore.completeKhqrTopup(khqrSessionId)
      khqrStatus.value = 'completed'
      toast.add({ title: 'Top-up successful', description: 'Squad Coin added to your wallet.', color: 'success' })
      setTimeout(() => (khqrModalOpen.value = false), 1200)
    } catch (err) {
      toast.add({
        title: "Couldn't complete top-up",
        description: err instanceof Error ? err.message : 'Please try again.',
        color: 'error',
      })
      khqrModalOpen.value = false
    }
  } else if (s === 'expired') {
    stopKhqrPolling()
    toast.add({ title: 'QR code expired', description: 'Please try again.', color: 'error' })
    khqrModalOpen.value = false
  }
}

async function startKhqrTopup(packageId: string | null) {
  if (!packageId || toppingUp.value) return

  toppingUp.value = true
  try {
    const session = await walletStore.createKhqrSession(packageId)
    khqrSessionId = session.sessionId
    khqrAmount.value = session.amountUsd
    khqrStatus.value = 'pending'
    // `errorCorrectionLevel: 'L'` (least redundancy) plus the backend's short payload keep this
    // at the QR spec's lowest version - fewer, bigger modules ("blockier") rather than the dense
    // fine-grained grid a longer/higher-redundancy payload would force at the same pixel size.
    khqrQrDataUrl.value = await QRCode.toDataURL(session.qrPayload, {
      margin: 1,
      width: 300,
      errorCorrectionLevel: 'L',
    })
    khqrModalOpen.value = true

    stopKhqrPolling()
    khqrPollTimer = setInterval(pollKhqrStatus, 1000)
  } catch (err) {
    toast.add({
      title: "Couldn't start QR payment",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    toppingUp.value = false
  }
}

function confirmTopUp() {
  const packageId = selectedPackageId.value ?? basePackageId.value
  if (paymentMethod.value === 'khqr') startKhqrTopup(packageId)
  else topUp(packageId)
}

// `?topup=cancelled` isn't a real routable state here (there's no redirect anymore, the card
// form is inline), kept only so an old bookmarked/shared link with the old query param doesn't
// dead-end silently.
if (route.query.topup === 'cancelled') {
  toast.add({ title: 'Top-up cancelled', description: 'No charge was made.', color: 'neutral' })
}
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] px-4 py-14 md:px-6">
    <div v-if="walletStore.loading" class="mx-auto flex max-w-4/5 flex-col gap-6">
      <USkeleton class="h-8 w-56" />

      <div class="flex flex-wrap items-center justify-between gap-6 rounded-xl bg-gray-800/70 p-6 sm:p-8">
        <div class="flex flex-col gap-2">
          <USkeleton class="h-4 w-20" />
          <USkeleton class="h-9 w-32" />
          <USkeleton class="h-3 w-16" />
        </div>
        <div class="flex items-center gap-2">
          <USkeleton class="h-9 w-24 rounded-full" />
          <USkeleton class="h-9 w-24 rounded-full" />
        </div>
      </div>

      <div>
        <USkeleton class="h-5 w-40" />
        <div class="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <USkeleton v-for="n in 4" :key="n" class="h-20 rounded-xl" />
        </div>
      </div>

      <USkeleton class="h-16 rounded-xl" />

      <div class="rounded-xl bg-gray-800/70 p-5">
        <USkeleton class="h-5 w-32" />
        <div class="mt-3 flex flex-col divide-y divide-white/5">
          <div v-for="n in 3" :key="n" class="flex items-center gap-3 py-3.5">
            <USkeleton class="h-5 w-5 shrink-0 rounded-full" />
            <div class="flex-1 space-y-1.5">
              <USkeleton class="h-4 w-32" />
              <USkeleton class="h-3 w-20" />
            </div>
            <USkeleton class="h-4 w-12" />
          </div>
        </div>
      </div>
    </div>

    <div v-else class="mx-auto flex max-w-4/5 flex-col gap-6">
      <h1 class="text-2xl font-bold text-white sm:text-3xl">Squadcoin Wallet</h1>

      <div class="flex flex-wrap items-center justify-between gap-6 rounded-xl bg-gray-800/70 p-6 sm:p-8">
        <div>
          <p class="text-sm text-slate-400">Your balance</p>
          <p class="mt-2 inline-flex items-center gap-2 text-4xl font-bold text-white">
            <img :src="coinIcon" alt="" class="h-8 w-8" />
            {{ balance.toLocaleString() }}
          </p>
          <p class="mt-1 text-sm text-slate-400">≈ ${{ usdBalance }} USD</p>
        </div>
        <div class="flex items-center gap-2">
          <UButton color="primary" class="rounded-full px-6" @click="scrollToPayment"> Top Up </UButton>
          <UButton v-if="isPal" to="/wallet/withdraw" color="neutral" variant="soft" class="rounded-full px-6">
            Withdraw
          </UButton>
        </div>
      </div>

      <div>
        <h2 class="text-lg font-semibold text-white">Top up Squad Coins</h2>
        <div class="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <button
            v-for="pkg in walletStore.topupPackages"
            :key="pkg.id"
            type="button"
            class="cursor-pointer rounded-xl border bg-gray-800/70 p-5 text-left transition-colors"
            :class="
              (selectedPackageId ?? basePackageId) === pkg.id
                ? 'border-brand-400'
                : 'border-transparent hover:border-white/10'
            "
            @click="selectedPackageId = pkg.id"
          >
            <div class="flex items-center justify-between gap-3">
              <span class="inline-flex items-center gap-1.5 text-lg font-bold text-white">
                <img :src="coinIcon" alt="" class="h-5 w-5" />
                {{ pkg.coins.toLocaleString() }}
              </span>
              <span class="text-sm text-slate-400">${{ pkg.priceUsd }}</span>
            </div>
            <p v-if="pkg.isBaseRate" class="mt-2 text-xs font-medium text-brand-400">Base rate</p>
            <p v-else-if="pkg.bonusCoins" class="mt-2 text-xs font-medium text-brand-400">
              +{{ pkg.bonusCoins.toLocaleString() }} bonus
            </p>
          </button>
        </div>
      </div>

      <div ref="paymentSectionRef" class="rounded-xl bg-gray-800/70 p-5">
        <div class="flex flex-wrap items-center gap-3">
          <span class="text-sm text-slate-400">Pay with</span>

          <UDropdownMenu :items="paymentMethodItems">
            <button
              type="button"
              class="flex items-center gap-1.5 rounded-full bg-white/5 px-3.5 py-1.5 text-sm font-medium text-white ring-1 ring-inset ring-white/10 hover:bg-white/10"
            >
              <component :is="paymentMethodIcon" :size="16" />
              {{ paymentMethodLabel }}
              <PhCaretDown :size="12" class="text-slate-400" />
            </button>
          </UDropdownMenu>

          <template v-if="paymentMethod === 'card'">
            <p v-if="stripeLoadFailed" class="text-xs text-red-400">
              Couldn't load the payment form. Check your connection and reload the page.
            </p>
            <div v-else ref="cardElementRef" class="min-w-56 flex-1 rounded-full bg-white/5 px-4 py-2 ring-1 ring-inset ring-white/10" />
          </template>
          <p v-else class="min-w-56 flex-1 text-sm text-slate-400">
            You'll scan a QR code to confirm this payment on the next step.
          </p>

          <UButton
            color="primary"
            class="ml-auto rounded-full px-6"
            :loading="toppingUp"
            :disabled="!selectedPackageId && !basePackageId"
            @click="confirmTopUp"
          >
            Confirm Top-Up
          </UButton>
        </div>
        <p v-if="paymentMethod === 'card' && cardError" class="mt-2 text-xs text-red-400">{{ cardError }}</p>
      </div>

      <UModal v-model:open="khqrModalOpen" title="Scan to Pay" description="KHQR" :ui="{ content: 'max-w-sm rounded-3xl' }">
        <template #body>
          <div class="flex flex-col items-center gap-4 py-2">
            <KhqrCard :amount-usd="khqrAmount" :qr-data-url="khqrQrDataUrl" />
            <div class="flex items-center gap-2 text-sm text-slate-400">
              <template v-if="khqrStatus === 'completed'">
                <PhCheckCircle :size="18" weight="fill" class="text-brand-400" />
                Payment successful
              </template>
              <template v-else>
                <PhSpinnerGap :size="18" class="animate-spin" />
                {{ khqrStatus === 'confirmed' ? 'Confirming payment…' : 'Waiting for confirmation on your banking app…' }}
              </template>
            </div>
          </div>
        </template>
      </UModal>

      <div class="rounded-xl bg-gray-800/70 p-5">
        <h2 class="text-lg font-semibold text-white">Recent activity</h2>
        <p v-if="walletStore.activity.length === 0" class="mt-2 text-sm text-slate-400">No activity yet.</p>
        <div v-else class="mt-2 flex flex-col divide-y divide-white/5">
          <div v-for="activity in walletStore.activity" :key="activity.id" class="flex items-center gap-3 py-3.5">
            <component
              :is="activityIcon(activity)"
              :size="20"
              weight="bold"
              :class="activityIconClass(activity)"
              class="shrink-0"
            />
            <div class="min-w-0 flex-1">
              <p class="font-medium text-white">
                {{ activity.label }}<template v-if="activity.detail"> · {{ activity.detail }}</template>
              </p>
              <p class="text-sm text-slate-400">{{ formatDateTime(activity.createdAt) }}</p>
            </div>
            <span
              class="inline-flex shrink-0 items-center gap-1 font-semibold"
              :class="activity.coins >= 0 ? 'text-brand-400' : 'text-red-400'"
            >
              <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
              {{ activity.coins >= 0 ? '+' : '' }}{{ activity.coins.toLocaleString() }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
