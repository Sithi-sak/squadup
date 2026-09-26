<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from '@nuxt/ui/composables/useToast'
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
import visaLogo from '@/assets/payway/visa.svg'
import mastercardLogo from '@/assets/payway/mastercard.svg'
import unionpayLogo from '@/assets/payway/unionpay.svg'
import jcbLogo from '@/assets/payway/jcb.svg'
import KhqrCard from '@/components/wallet/KhqrCard.vue'
import { closePayWayCheckout, openPayWayCheckout, preloadPayWay } from '@/lib/payway'
import { useAuthStore } from '@/stores/auth'
import { useWalletStore, type WalletActivity } from '@/stores/wallet'
import { coinsToUsd } from '@/utils/coins'



const walletStore = useWalletStore()
const authStore = useAuthStore()
const toast = useToast()
const route = useRoute()

const isPal = computed(() => Boolean(authStore.user?.playerId))

onMounted(() => {
  walletStore.fetchWallet()
  walletStore.fetchTopupPackages()
  preloadPayWay()
})
onBeforeUnmount(() => {
  stopCardPolling()
  closePayWayCheckout()
  stopKhqrPolling()
})

const balance = computed(() => walletStore.balance)
const usdBalance = computed(() => coinsToUsd(balance.value))

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

const toppingUp = ref(false)

// 4.57: card top-ups go through ABA PayWay's own card popup (`lib/payway.ts`), so card details
// never touch SquadUp. The popup charges the card on PayWay's side and closes itself; this page
// polls the backend, which confirms the payment with PayWay before crediting it.
const CARD_POLL_INTERVAL_MS = 2000
let cardTranId: string | null = null
let cardPollTimer: ReturnType<typeof setInterval> | null = null

function stopCardPolling() {
  if (cardPollTimer) {
    clearInterval(cardPollTimer)
    cardPollTimer = null
  }
}

async function onCardTopupPaid() {
  stopCardPolling()
  cardTranId = null
  closePayWayCheckout()
  await walletStore.fetchWallet({ silent: true })
  toast.add({ title: 'Top-up successful', description: 'Squad Coin added to your wallet.', color: 'success' })
}

function onCardTopupFailed() {
  stopCardPolling()
  cardTranId = null
  closePayWayCheckout()
  toast.add({ title: 'Card was declined', description: 'No coins were added. Please try again.', color: 'error' })
}

async function checkCardTopup(tranId: string) {
  const { status: s } = await walletStore.getCardTopupStatus(tranId)
  // A newer attempt (or a finished one) owns the page now; ignore a stale answer.
  if (cardTranId !== tranId) return s
  if (s === 'paid') await onCardTopupPaid()
  else if (s === 'failed') onCardTopupFailed()
  return s
}

/** The customer closed PayWay's popup. One last check covers a payment made just before closing;
 * anything still pending after that is treated as cancelled. */
async function onCardPopupClosed(tranId: string) {
  if (cardTranId !== tranId) return
  stopCardPolling()
  try {
    const s = await checkCardTopup(tranId)
    if (s !== 'pending' || cardTranId !== tranId) return
  } catch {
    // Fall through to the cancelled toast; a payment that did go through is still settled by
    // PayWay's callback.
  }
  cardTranId = null
  toast.add({ title: 'Top-up cancelled', description: 'No charge was made.', color: 'neutral' })
}

async function topUp(packageId: string | null) {
  if (!packageId || toppingUp.value) return

  toppingUp.value = true
  try {
    const checkout = await walletStore.createCardCheckout(packageId)
    cardTranId = checkout.tranId
    await openPayWayCheckout(checkout.form, () => onCardPopupClosed(checkout.tranId))
    stopCardPolling()
    cardPollTimer = setInterval(() => {
      checkCardTopup(checkout.tranId).catch(() => {})
    }, CARD_POLL_INTERVAL_MS)
  } catch (err) {
    cardTranId = null
    toast.add({
      title: "Couldn't open card payment",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    toppingUp.value = false
  }
}

// 4.58: "QR Scan" shows a real ABA KHQR from PayWay (`KhqrCard.vue`, drawn to ABA's QR display
// guideline). The backend settles it on a real payment or, for the demo, after a short timer, so
// this only polls and reacts.
const KHQR_POLL_INTERVAL_MS = 2000
const khqrModalOpen = ref(false)
const khqrQrString = ref('')
const khqrAmount = ref(0)
const khqrCoins = ref(0)
const khqrStatus = ref<'pending' | 'paid' | 'failed' | 'expired'>('pending')
const khqrExpiresAt = ref(0)
const khqrSecondsLeft = ref(0)
let khqrTranId: string | null = null
let khqrPollTimer: ReturnType<typeof setInterval> | null = null
let khqrCountdownTimer: ReturnType<typeof setInterval> | null = null

const khqrCountdown = computed(() => {
  const minutes = Math.floor(khqrSecondsLeft.value / 60)
  const seconds = String(khqrSecondsLeft.value % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
})

function stopKhqrPolling() {
  if (khqrPollTimer) {
    clearInterval(khqrPollTimer)
    khqrPollTimer = null
  }
  if (khqrCountdownTimer) {
    clearInterval(khqrCountdownTimer)
    khqrCountdownTimer = null
  }
}

function tickKhqrCountdown() {
  khqrSecondsLeft.value = Math.max(0, Math.ceil((khqrExpiresAt.value - Date.now()) / 1000))
}

async function pollKhqrStatus() {
  const tranId = khqrTranId
  if (!tranId) return
  const { status: s } = await walletStore.getKhqrTopupStatus(tranId)
  // The modal was closed, or a newer QR replaced this one, while the request was in flight.
  if (khqrTranId !== tranId) return
  khqrStatus.value = s

  if (s === 'paid') {
    stopKhqrPolling()
    khqrTranId = null
    await walletStore.fetchWallet({ silent: true })
    toast.add({ title: 'Top-up successful', description: 'Squad Coin added to your wallet.', color: 'success' })
  } else if (s === 'failed') {
    stopKhqrPolling()
    khqrTranId = null
    toast.add({ title: 'Payment failed', description: 'No coins were added. Please try again.', color: 'error' })
    khqrModalOpen.value = false
  } else if (s === 'expired') {
    stopKhqrPolling()
    khqrTranId = null
  }
}

async function startKhqrTopup(packageId: string | null) {
  if (!packageId || toppingUp.value) return

  toppingUp.value = true
  try {
    const checkout = await walletStore.createKhqrCheckout(packageId)
    khqrTranId = checkout.tranId
    khqrQrString.value = checkout.qrString
    khqrAmount.value = checkout.amountUsd
    khqrCoins.value = checkout.coins
    khqrStatus.value = 'pending'
    khqrExpiresAt.value = new Date(checkout.expiresAt).getTime()
    tickKhqrCountdown()
    khqrModalOpen.value = true

    stopKhqrPolling()
    khqrPollTimer = setInterval(() => {
      pollKhqrStatus().catch(() => {})
    }, KHQR_POLL_INTERVAL_MS)
    khqrCountdownTimer = setInterval(tickKhqrCountdown, 1000)
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

/** Closing the modal while a QR is still unpaid abandons it. A payment that still lands is
 * settled by PayWay's callback. */
function onKhqrModalToggle(open: boolean) {
  if (open) return
  stopKhqrPolling()
  khqrTranId = null
}

function confirmTopUp() {
  const packageId = selectedPackageId.value ?? basePackageId.value
  if (paymentMethod.value === 'khqr') startKhqrTopup(packageId)
  else topUp(packageId)
}

// `?topup=cancelled` isn't a real routable state here (the PayWay card popup never
// redirects away from this page), kept only so an old bookmarked/shared link with the old query param doesn't
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

          <div v-if="paymentMethod === 'card'" class="flex min-w-56 flex-1 flex-wrap items-center gap-x-3 gap-y-1.5">
            <span class="text-sm text-slate-400">You'll enter your card in ABA PayWay's secure form.</span>
            <span class="flex items-center gap-1">
              <img :src="visaLogo" alt="Visa" class="h-4 w-auto" />
              <img :src="mastercardLogo" alt="Mastercard" class="h-4 w-auto" />
              <img :src="unionpayLogo" alt="UnionPay" class="h-4 w-auto" />
              <img :src="jcbLogo" alt="JCB" class="h-4 w-auto" />
            </span>
          </div>
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
      </div>

      <UModal
        v-model:open="khqrModalOpen"
        title="ABA KHQR"
        description="Scan to pay with ABA Mobile or any KHQR banking app"
        :ui="{ content: 'max-w-sm rounded-3xl' }"
        @update:open="onKhqrModalToggle"
      >
        <template #body>
          <div class="flex flex-col items-center gap-4">
            <!-- The guideline's "on Website Popup" backdrop: the display sits on light grey. -->
            <div class="w-full rounded-2xl bg-[#e8e9ec]">
              <KhqrCard
                merchant="SquadUp"
                :amount="khqrAmount"
                :payload="khqrQrString"
                :paid="khqrStatus === 'paid'"
                :expired="khqrStatus === 'expired'"
              />
            </div>
            <div class="flex items-center gap-2 text-sm text-slate-400">
              <template v-if="khqrStatus === 'paid'">
                <PhCheckCircle :size="18" weight="fill" class="text-brand-400" />
                Payment successful. {{ khqrCoins.toLocaleString() }} SC added to your wallet.
              </template>
              <template v-else-if="khqrStatus === 'expired'">
                This QR has expired. Close it and try again.
              </template>
              <template v-else>
                <PhSpinnerGap :size="18" class="animate-spin" />
                Waiting for payment. QR expires in {{ khqrCountdown }}
              </template>
            </div>
            <UButton
              v-if="khqrStatus === 'paid'"
              color="primary"
              class="rounded-full px-8"
              @click="khqrModalOpen = false"
            >
              Done
            </UButton>
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
