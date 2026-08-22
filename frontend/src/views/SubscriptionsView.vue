<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhStar, PhUserCircle } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import CancelSubscriptionModal from '@/components/modals/CancelSubscriptionModal.vue'
import { mockSubscriptions, type Subscription } from '@/mocks/subscriptions'

/** $1 = 99 SC, matching the base top-up package (990 SC / $10). */
const COINS_PER_USD = 99

const router = useRouter()

const subscriptions = ref<Subscription[]>(mockSubscriptions.map((sub) => ({ ...sub })))

const tabs = [
  { key: 'active', label: 'Active' },
  { key: 'cancelled', label: 'Cancelled' },
] as const

const activeTab = ref<(typeof tabs)[number]['key']>('active')

const activeSubs = computed(() => subscriptions.value.filter((s) => s.status === 'active'))
const cancelledSubs = computed(() => subscriptions.value.filter((s) => s.status === 'cancelled'))

const visibleSubs = computed(() => (activeTab.value === 'active' ? activeSubs.value : cancelledSubs.value))

const totalCoinsThisMonth = computed(() => activeSubs.value.reduce((sum, s) => sum + s.priceCoins, 0))
const totalUsdThisMonth = computed(() => Math.round(totalCoinsThisMonth.value / COINS_PER_USD))
const nextChargeDate = computed(() => {
  if (!activeSubs.value.length) return null
  return [...activeSubs.value].sort((a, b) => a.renewsOn.localeCompare(b.renewsOn))[0]!.renewsOn
})

function formatShortDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function cycleLengthDays(cycle: Subscription['billingCycle']) {
  return cycle === 'Quarterly' ? 90 : 30
}

const cancelModalOpen = ref(false)
const cancelTargetId = ref<string | null>(null)
const cancelTarget = computed(() => subscriptions.value.find((s) => s.id === cancelTargetId.value) ?? null)

function openCancelModal(subId: string) {
  cancelTargetId.value = subId
  cancelModalOpen.value = true
}

function confirmCancel() {
  const sub = cancelTarget.value
  if (!sub) return
  sub.status = 'cancelled'
}

function resubscribe(sub: Subscription) {
  const renewsOn = new Date()
  renewsOn.setDate(renewsOn.getDate() + cycleLengthDays(sub.billingCycle))
  sub.status = 'active'
  sub.renewsOn = renewsOn.toISOString().slice(0, 10)
}
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] px-4 py-14 md:px-6">
    <div class="mx-auto flex max-w-4/5 flex-col gap-6">
      <div>
        <h1 class="text-2xl font-bold text-white sm:text-3xl">Subscriptions</h1>
        <p class="mt-1 text-slate-400">Manage the Pals you subscribe to and your renewals</p>
      </div>

      <div class="flex items-center gap-2">
        <UButton
          v-for="tab in tabs"
          :key="tab.key"
          :color="activeTab === tab.key ? 'primary' : 'neutral'"
          :variant="activeTab === tab.key ? 'solid' : 'soft'"
          size="sm"
          class="rounded-full"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}<template v-if="tab.key === 'active'"> · {{ activeSubs.length }}</template>
        </UButton>
      </div>

      <div
        v-if="activeTab === 'active' && activeSubs.length"
        class="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-gray-800/70 p-6"
      >
        <div>
          <p class="text-sm text-slate-400">Total this month</p>
          <p class="mt-2 inline-flex items-center gap-2 text-3xl font-bold text-white">
            <img :src="coinIcon" alt="" class="h-7 w-7" />
            {{ totalCoinsThisMonth.toLocaleString() }}
          </p>
        </div>
        <div class="text-right">
          <p class="font-medium text-brand-400">
            {{ activeSubs.length }} active subscription{{ activeSubs.length === 1 ? '' : 's' }} · ≈ ${{
              totalUsdThisMonth
            }}/mo
          </p>
          <p v-if="nextChargeDate" class="mt-1 text-sm text-slate-400">
            Next charge {{ formatShortDate(nextChargeDate) }}
          </p>
        </div>
      </div>

      <UEmpty
        v-if="!visibleSubs.length"
        :title="activeTab === 'active' ? 'No active subscriptions' : 'No cancelled subscriptions'"
        :description="
          activeTab === 'active'
            ? 'Subscribe to your favorite Pals for perks, priority booking, and bonus Squad Coin.'
            : 'Subscriptions you cancel will show up here.'
        "
        class="py-16 text-white"
      >
        <template v-if="activeTab === 'active'" #actions>
          <UButton color="primary" class="rounded-full" @click="router.push('/players')">Find a Pal</UButton>
        </template>
      </UEmpty>

      <div v-else class="flex flex-col gap-4">
        <div
          v-for="sub in visibleSubs"
          :key="sub.id"
          class="flex flex-col gap-4 rounded-xl bg-gray-800/70 p-5 sm:flex-row sm:items-center sm:justify-between"
        >
          <div class="flex items-center gap-3">
            <UAvatar size="lg" class="bg-white/10 text-slate-300 ring-2 ring-brand-500/40">
              <PhUserCircle :size="26" />
            </UAvatar>
            <div>
              <p class="flex items-center gap-1.5 font-semibold text-white">
                {{ sub.palName }}
                <span class="inline-flex items-center gap-1 text-sm font-medium text-amber-400">
                  <PhStar :size="14" weight="fill" />
                  {{ sub.rating }}
                </span>
              </p>
              <p class="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-400">
                <UBadge
                  :color="sub.status === 'active' ? 'primary' : 'neutral'"
                  variant="subtle"
                  size="sm"
                  class="rounded-full"
                >
                  {{ sub.status === 'active' ? sub.billingCycle : 'Cancelled' }}
                </UBadge>
                <span>{{ sub.serviceLabel }}</span>
                <span v-if="sub.status === 'active'">· Renews {{ formatShortDate(sub.renewsOn) }}</span>
                <span v-else>· Access until {{ formatShortDate(sub.renewsOn) }}</span>
              </p>
            </div>
          </div>

          <div class="flex shrink-0 flex-col items-start gap-2 sm:items-end">
            <span class="inline-flex items-center gap-1.5 font-semibold text-white">
              <img :src="coinIcon" alt="" class="h-4 w-4" />
              {{ sub.priceCoins.toLocaleString() }}
              <span class="text-sm font-normal text-slate-400">/mo</span>
            </span>
            <div class="flex items-center gap-2">
              <template v-if="sub.status === 'active'">
                <UPopover :content="{ side: 'bottom', align: 'end', sideOffset: 8 }">
                  <UButton color="neutral" variant="soft" size="sm" class="rounded-full">Manage</UButton>
                  <template #content>
                    <div class="w-64 p-4">
                      <p class="text-sm font-semibold text-white">{{ sub.palName }}</p>
                      <p class="mt-1 text-xs text-slate-400">{{ sub.billingCycle }} · {{ sub.serviceLabel }}</p>
                      <div class="mt-3 flex items-center justify-between rounded-xl bg-gray-900/60 p-3">
                        <span class="text-xs text-slate-400">Renews</span>
                        <span class="text-xs font-medium text-white">{{ formatShortDate(sub.renewsOn) }}</span>
                      </div>
                      <UButton
                        to="/wallet"
                        color="neutral"
                        variant="soft"
                        size="sm"
                        block
                        class="mt-3 rounded-full"
                      >
                        Update payment method
                      </UButton>
                    </div>
                  </template>
                </UPopover>
                <UButton
                  color="neutral"
                  variant="soft"
                  size="sm"
                  class="rounded-full text-red-400"
                  @click="openCancelModal(sub.id)"
                >
                  Cancel
                </UButton>
              </template>
              <UButton v-else color="primary" size="sm" class="rounded-full" @click="resubscribe(sub)">
                Resubscribe
              </UButton>
            </div>
          </div>
        </div>
      </div>

      <CancelSubscriptionModal
        v-model:open="cancelModalOpen"
        :pal-name="cancelTarget?.palName ?? ''"
        :billing-cycle="cancelTarget?.billingCycle ?? ''"
        :price-coins="cancelTarget?.priceCoins ?? 0"
        :access-until="cancelTarget ? formatShortDate(cancelTarget.renewsOn) : ''"
        @confirm="confirmCancel"
      />
    </div>
  </div>
</template>
