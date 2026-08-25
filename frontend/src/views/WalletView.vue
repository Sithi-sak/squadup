<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhArrowUp, PhArrowDown, PhHourglass, PhArrowCounterClockwise, PhProhibit } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import EmptyState from '@/components/common/EmptyState.vue'
import { mockPaymentCards } from '@/mocks/settings'
import { useWalletStore, type WalletActivity } from '@/stores/wallet'

/** $1 = 99 SC, matching the base top-up package (990 SC / $10). */
const COINS_PER_USD = 99

const walletStore = useWalletStore()
const toast = useToast()

onMounted(() => {
  walletStore.fetchWallet()
  walletStore.fetchTopupPackages()
})

const balance = computed(() => walletStore.balance)
const usdBalance = computed(() => (balance.value / COINS_PER_USD).toFixed(2))

const selectedPackageId = ref<string | null>(null)
const basePackageId = computed(
  () => walletStore.topupPackages.find((p) => p.isBaseRate)?.id ?? walletStore.topupPackages[0]?.id ?? null,
)

const cardLabels = mockPaymentCards.map((card) => card.label)
const selectedCardLabel = ref(mockPaymentCards.find((card) => card.isDefault)?.label ?? cardLabels[0])

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

async function topUp(packageId: string | null) {
  if (!packageId || toppingUp.value) return
  toppingUp.value = true
  try {
    await walletStore.topUp(packageId, selectedCardLabel.value)
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

function confirmTopUp() {
  topUp(selectedPackageId.value ?? basePackageId.value)
}
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] px-4 py-14 md:px-6">
    <div v-if="walletStore.loading" class="flex min-h-[60vh] items-center justify-center text-sm text-slate-400">
      Loading wallet...
    </div>

    <div v-else-if="balance === 0" class="flex min-h-[60vh] items-center justify-center">
      <EmptyState
        tone="gold"
        badge="0 SC"
        title="Your wallet is empty"
        description="Top up Squad Coin to book Pals, tip, and send gifts. $10 = 990 SC."
      >
        <template #icon>
          <img :src="coinIcon" alt="" class="h-9 w-9" />
        </template>
        <template #actions>
          <UButton color="primary" class="rounded-full px-6" :loading="toppingUp" @click="topUp(basePackageId)">
            Top up now
          </UButton>
          <UButton color="neutral" variant="soft" class="rounded-full px-6" to="/settings">
            How it works
          </UButton>
        </template>
      </EmptyState>
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
          <UButton color="primary" class="rounded-full px-6">Top Up</UButton>
          <UButton to="/wallet/withdraw" color="neutral" variant="soft" class="rounded-full px-6">
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

      <div class="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-gray-800/70 p-5">
        <div class="flex items-center gap-3">
          <span class="text-sm text-slate-400">Pay with</span>
          <USelect
            v-model="selectedCardLabel"
            :items="cardLabels"
            variant="soft"
            size="md"
            class="w-auto"
            :ui="{ base: 'rounded-full bg-white/5 px-3.5 py-1.5 text-sm ring-white/10 hover:bg-white/10' }"
          />
        </div>
        <UButton
          color="primary"
          class="rounded-full px-6"
          :loading="toppingUp"
          :disabled="!selectedPackageId && !basePackageId"
          @click="confirmTopUp"
        >
          Confirm Top-Up
        </UButton>
      </div>

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
