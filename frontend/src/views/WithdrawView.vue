<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhCaretLeft, PhBank, PhCheck, PhCreditCard } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import visaIcon from '@/assets/visa.svg'
import mastercardIcon from '@/assets/mastercard.svg'
import { mockWithdrawalPlatformFeePct } from '@/mocks/wallet'
import { useWalletStore, type Withdrawal } from '@/stores/wallet'
import AddPayoutMethodModal from '@/components/modals/AddPayoutMethodModal.vue'
import { coinsToUsd } from '@/utils/coins'



const router = useRouter()
const walletStore = useWalletStore()
const toast = useToast()

/** Coins already spoken for by an undecided payout are still in the balance - the debit lands on
 * approval (4.31) - but they cannot be withdrawn a second time. */
const availableCoins = computed(() =>
  Math.max(0, walletStore.balance - walletStore.pendingClearanceCoins - walletStore.lockedPayoutCoins),
)
const usdAvailable = computed(() => coinsToUsd(availableCoins.value))

const amount = ref(0)
const selectedMethodId = ref<string | null>(null)

onMounted(async () => {
  await Promise.all([walletStore.fetchWallet(), walletStore.fetchPayoutMethods(), walletStore.fetchWithdrawals()])
  amount.value = availableCoins.value
  selectedMethodId.value =
    walletStore.payoutMethods.find((m) => m.isDefault)?.id ?? walletStore.payoutMethods[0]?.id ?? null
})

const feeCoins = computed(() => Math.round((amount.value * mockWithdrawalPlatformFeePct) / 100))
const receiveCoins = computed(() => amount.value - feeCoins.value)
const receiveUsd = computed(() => coinsToUsd(receiveCoins.value))

/** Mirrors the `withdrawal_status` enum (4.28b) - `requested` is a payout waiting on an admin,
 * `in_progress` one they approved that is with the payment provider. */
const withdrawalStatusMeta: Record<Withdrawal['status'], { label: string; class: string }> = {
  requested: { label: 'Awaiting review', class: 'text-amber-400' },
  in_progress: { label: 'In progress', class: 'text-sky-400' },
  paid: { label: 'Paid', class: 'text-brand-400' },
  rejected: { label: 'Declined', class: 'text-red-400' },
}

/** `payout_methods.brand` stores the detected card network (4.32), so the row can show the real
 * scheme mark instead of a Visa glyph on every card. */
function brandIcon(brand: string) {
  if (brand === 'visa') return visaIcon
  if (brand === 'mastercard') return mastercardIcon
  return null
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function methodLabel(payoutMethodId: string | null) {
  return walletStore.payoutMethods.find((m) => m.id === payoutMethodId)?.label ?? 'Withdrawal'
}

const addingMethod = ref(false)

/** A freshly added method comes back as the default when it is the Pal's first one, so select it
 * straight away - otherwise they would add a method and still have nothing chosen. */
function onMethodAdded() {
  selectedMethodId.value =
    walletStore.payoutMethods.find((m) => m.isDefault)?.id ?? walletStore.payoutMethods.at(-1)?.id ?? null
}

const submitting = ref(false)

async function submitWithdrawal() {
  if (submitting.value || amount.value <= 0 || amount.value > availableCoins.value) return
  submitting.value = true
  try {
    await walletStore.requestWithdrawal(amount.value, selectedMethodId.value ?? undefined)
    toast.add({
      title: 'Withdrawal requested',
      description: 'The coins are on hold until an admin approves it.',
      color: 'success',
    })
    amount.value = availableCoins.value
  } catch (err) {
    toast.add({
      title: "Couldn't request withdrawal",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] px-4 py-14 md:px-6">
    <div class="mx-auto flex max-w-4/5 flex-col gap-6">
      <div class="flex items-center gap-4">
        <UButton
          color="neutral"
          variant="soft"
          square
          :ui="{ base: 'rounded-full' }"
          aria-label="Back to wallet"
          @click="router.back()"
        >
          <PhCaretLeft :size="18" weight="bold" />
        </UButton>
        <h1 class="text-2xl font-bold text-white sm:text-3xl">Withdraw</h1>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-6 rounded-xl bg-gray-800/70 p-6 sm:p-8">
        <div>
          <p class="text-sm text-slate-400">Available to withdraw</p>
          <p class="mt-2 inline-flex items-center gap-2 text-4xl font-bold text-white">
            <img :src="coinIcon" alt="" class="h-8 w-8" />
            {{ availableCoins.toLocaleString() }}
          </p>
          <p class="mt-1 text-sm text-slate-400">≈ ${{ usdAvailable }} USD</p>
        </div>
        <div class="flex flex-col gap-1 text-sm">
          <p class="text-white">In escrow: {{ walletStore.pendingClearanceCoins.toLocaleString() }}</p>
          <p v-if="walletStore.lockedPayoutCoins > 0" class="text-amber-400">
            On hold for payout: {{ walletStore.lockedPayoutCoins.toLocaleString() }}
          </p>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
        <div class="rounded-xl bg-gray-800/70 p-5">
          <h2 class="text-lg font-semibold text-white">Withdraw funds</h2>

          <p class="mt-4 text-sm text-slate-400">Amount</p>
          <div class="mt-2 flex items-center justify-between gap-3 rounded-xl bg-gray-700/40 px-4 py-4">
            <div class="flex items-center gap-2">
              <img :src="coinIcon" alt="" class="h-7 w-7" />
              <UInput
                v-model.number="amount"
                type="number"
                min="0"
                :max="availableCoins"
                variant="none"
                size="xl"
                class="w-32"
                :ui="{ base: 'p-0 text-3xl font-bold text-white' }"
              />
            </div>
            <button
              type="button"
              class="cursor-pointer text-sm font-semibold text-brand-400 hover:text-brand-300"
              @click="amount = availableCoins"
            >
              Max
            </button>
          </div>

          <p class="mt-4 text-sm text-slate-400">
            Payouts are reviewed by the SquadUp team first. The coins stay in your wallet on hold
            until it is approved, and you keep {{ 100 - mockWithdrawalPlatformFeePct }}% of every
            withdrawal.
          </p>

          <div class="mt-4 flex flex-col gap-2 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Withdrawal amount</span>
              <span class="font-medium text-white">{{ amount.toLocaleString() }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Platform fee ({{ mockWithdrawalPlatformFeePct }}%)</span>
              <span class="font-medium text-amber-400">− {{ feeCoins.toLocaleString() }}</span>
            </div>
          </div>
          <USeparator class="my-3" />
          <div class="flex items-center justify-between">
            <span class="font-semibold text-white">You'll receive ({{ 100 - mockWithdrawalPlatformFeePct }}%)</span>
            <span class="font-semibold text-brand-400">
              {{ receiveCoins.toLocaleString() }} SC ≈ ${{ receiveUsd }}
            </span>
          </div>

          <p class="mt-6 text-sm text-slate-400">Payout method</p>
          <p v-if="walletStore.payoutMethods.length === 0" class="mt-3 text-sm text-slate-400">
            No payout method on file yet.
          </p>
          <div v-else class="mt-3 flex flex-col gap-3">
            <button
              v-for="method in walletStore.payoutMethods"
              :key="method.id"
              type="button"
              class="flex cursor-pointer items-center justify-between gap-3 rounded-xl border bg-gray-700/40 px-4 py-3 text-left transition-colors"
              :class="selectedMethodId === method.id ? 'border-brand-400' : 'border-transparent hover:border-white/10'"
              @click="selectedMethodId = method.id"
            >
              <div class="flex items-center gap-3">
                <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white">
                  <img v-if="brandIcon(method.brand)" :src="brandIcon(method.brand)!" alt="" class="h-7 w-7" />
                  <PhBank v-else-if="method.brand === 'bank'" :size="20" weight="fill" class="text-gray-800" />
                  <PhCreditCard v-else :size="20" weight="fill" class="text-gray-800" />
                </div>
                <div>
                  <p class="font-medium text-white">{{ method.label }}</p>
                  <p class="text-sm text-slate-400">{{ method.detail }}</p>
                </div>
              </div>
              <span
                class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full"
                :class="selectedMethodId === method.id ? 'bg-brand-500' : 'ring-1 ring-inset ring-white/20'"
              >
                <PhCheck v-if="selectedMethodId === method.id" :size="12" weight="bold" class="text-white" />
              </span>
            </button>
          </div>

          <button
            type="button"
            class="mt-3 w-full cursor-pointer rounded-xl border border-dashed border-white/15 py-3 text-sm font-medium text-brand-400 transition-colors hover:border-brand-400/50 hover:bg-white/5"
            @click="addingMethod = true"
          >
            + Add payout method
          </button>

          <p class="mt-4 text-sm">
            <span class="font-medium text-brand-400">Platform fee: {{ mockWithdrawalPlatformFeePct }}%</span>
            <span class="text-slate-400"> · Arrives in 1-3 business days once approved</span>
          </p>

          <UButton
            color="primary"
            size="lg"
            block
            class="mt-4 rounded-full"
            :loading="submitting"
            :disabled="amount <= 0 || amount > availableCoins || walletStore.payoutMethods.length === 0"
            @click="submitWithdrawal"
          >
            Withdraw ${{ receiveUsd }}
          </UButton>
        </div>

        <div class="rounded-xl bg-gray-800/70 p-5">
          <h2 class="text-lg font-semibold text-white">Withdrawal history</h2>
          <p v-if="walletStore.withdrawals.length === 0" class="mt-2 text-sm text-slate-400">
            No withdrawals yet.
          </p>
          <div v-else class="mt-2 flex flex-col divide-y divide-white/5">
            <div v-for="withdrawal in walletStore.withdrawals" :key="withdrawal.id" class="flex items-center justify-between gap-3 py-3">
              <div>
                <p class="inline-flex items-center gap-1 font-semibold text-white">
                  <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                  {{ withdrawal.coins.toLocaleString() }}
                </p>
                <p class="text-sm text-slate-400">
                  {{ formatDate(withdrawal.createdAt) }} · {{ methodLabel(withdrawal.payoutMethodId) }}
                </p>
                <p v-if="withdrawal.reference" class="font-mono text-xs text-slate-500">
                  {{ withdrawal.reference }}
                </p>
              </div>
              <span class="shrink-0 text-sm font-medium" :class="withdrawalStatusMeta[withdrawal.status].class">
                {{ withdrawalStatusMeta[withdrawal.status].label }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <AddPayoutMethodModal v-model:open="addingMethod" @added="onMethodAdded" />
  </div>
</template>
