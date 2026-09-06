<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhCheck, PhX } from '@phosphor-icons/vue'
import brandLogo from '@/assets/brand.svg'
import StepAccount from '@/components/become-player/StepAccount.vue'
import StepGames from '@/components/become-player/StepGames.vue'
import StepRates from '@/components/become-player/StepRates.vue'
import StepReview from '@/components/become-player/StepReview.vue'
import StepSuccess from '@/components/become-player/StepSuccess.vue'
import StepVerify from '@/components/become-player/StepVerify.vue'
import {
  becomePlayerSteps,
  createAccountStepData,
  createGamesStepData,
  createRatesStepData,
  createReviewStepData,
  createVerifyStepData,
} from '@/components/become-player/types'
import { usePlayersStore } from '@/stores/players'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const playersStore = usePlayersStore()
const authStore = useAuthStore()

const currentStep = ref(1)
const progressPct = computed(() => (currentStep.value === 1 ? 8 : (currentStep.value - 1) * 20))

/** Step 1 starts from whatever the account already has (a buyer who signed up first and is only
 * now becoming a Pal) rather than blank fields - only a genuinely fresh account (nothing set
 * since signup) sees empty phone/region. Email always comes from the account and stays locked in
 * `StepAccount.vue`; there's no "fresh" case for it since `/become-player` requires auth. */
const accountData = ref({
  ...createAccountStepData(),
  displayName: authStore.user?.displayName ?? '',
  email: authStore.user?.email ?? '',
  phone: authStore.user?.phone ?? '',
  region: authStore.user?.country ?? '',
})
const gamesData = ref(createGamesStepData())
const ratesData = ref(createRatesStepData())
const verifyData = ref(createVerifyStepData())
const reviewData = ref(createReviewStepData())
const submitted = ref(false)
const submitting = ref(false)
const submitError = ref<string | null>(null)

function handleStepContinue() {
  currentStep.value = Math.min(currentStep.value + 1, becomePlayerSteps.length)
}

function handleStepBack() {
  currentStep.value = Math.max(currentStep.value - 1, 1)
}

async function handleSubmit() {
  submitting.value = true
  submitError.value = null

  const formData = new FormData()
  formData.append('display_name', accountData.value.displayName)
  if (gamesData.value.headline) formData.append('tagline', gamesData.value.headline)
  if (accountData.value.timezone) formData.append('timezone', accountData.value.timezone)
  for (const game of gamesData.value.games) formData.append('games', game)
  if (gamesData.value.highestRank) formData.append('rank', gamesData.value.highestRank)
  if (gamesData.value.role) formData.append('role', gamesData.value.role)
  for (const language of gamesData.value.languages) formData.append('languages', language)
  formData.append('payout_schedule', verifyData.value.payoutSchedule)
  formData.append('pricing_model', ratesData.value.pricingModel)
  formData.append(
    'rates',
    JSON.stringify(ratesData.value.rates.map((rate) => ({ game: rate.game, price: rate.price }))),
  )
  formData.append('offer_first_order_free', String(ratesData.value.offerFirstOrderFree))
  if (accountData.value.avatarFile) formData.append('avatar', accountData.value.avatarFile)
  if (verifyData.value.idFrontFile) formData.append('id_front', verifyData.value.idFrontFile)
  if (verifyData.value.idBackFile) formData.append('id_back', verifyData.value.idBackFile)

  try {
    await authStore.updateAccount({
      displayName: accountData.value.displayName,
      phone: accountData.value.phone,
      country: accountData.value.region,
    })
    const profile = await playersStore.createMine(formData)
    if (authStore.user) authStore.user = { ...authStore.user, playerId: profile.id }
    submitted.value = true
  } catch (err) {
    submitError.value = err instanceof Error ? err.message : 'Failed to submit your application'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-squadup-dark">
    <header class="border-b border-gray-800 px-6 py-5">
      <div class="mx-auto flex max-w-5xl items-center justify-between">
        <router-link to="/home" class="flex items-center gap-2">
          <img :src="brandLogo" alt="SquadUp" class="h-6 w-auto" />
          <span class="text-sm text-slate-400">· Pal Application</span>
        </router-link>
        <UButton
          v-if="!submitted"
          color="neutral"
          variant="soft"
          square
          class="rounded-full bg-gray-800 text-white hover:bg-gray-700"
          aria-label="Close"
          @click="router.push('/home')"
        >
          <PhX :size="18" weight="bold" />
        </UButton>
      </div>
    </header>

    <div class="mx-auto max-w-5xl px-6 py-5">
      <StepSuccess v-if="submitted" :display-name="accountData.displayName" :email="accountData.email" />

      <template v-else>
        <div class="mb-5 flex items-center gap-4">
          <div class="h-1.5 flex-1 rounded-full bg-gray-800">
            <div
              class="h-full rounded-full bg-brand-600 transition-[width]"
              :style="{ width: `${progressPct}%` }"
            />
          </div>
          <span class="text-sm text-slate-400">{{ progressPct }}%</span>
        </div>

        <div class="grid grid-cols-1 gap-10 md:grid-cols-[240px_1fr]">
          <nav class="flex flex-row gap-4 overflow-x-auto md:flex-col md:gap-6">
            <button
              v-for="step in becomePlayerSteps"
              :key="step.id"
              type="button"
              class="flex shrink-0 cursor-pointer items-start gap-3 text-left"
              @click="currentStep = step.id"
            >
              <div
                class="flex size-8 shrink-0 items-center justify-center rounded-full border-2 text-sm font-semibold"
                :class="
                  step.id === currentStep
                    ? 'border-brand-600 text-brand-300'
                    : step.id < currentStep
                      ? 'border-brand-600 bg-brand-600 text-white'
                      : 'border-gray-700 text-slate-500'
                "
              >
                <PhCheck v-if="step.id < currentStep" :size="16" weight="bold" />
                <template v-else>{{ step.id }}</template>
              </div>
              <div>
                <p
                  class="text-sm font-semibold"
                  :class="step.id === currentStep ? 'text-white' : 'text-slate-400'"
                >
                  {{ step.title }}
                </p>
                <p class="text-sm text-slate-500">{{ step.subtitle }}</p>
              </div>
            </button>
          </nav>

          <div class="rounded-3xl bg-gray-900/60 p-6 sm:p-8">
            <StepAccount v-if="currentStep === 1" v-model="accountData" @continue="handleStepContinue" />
            <StepGames
              v-else-if="currentStep === 2"
              v-model="gamesData"
              @continue="handleStepContinue"
              @back="handleStepBack"
            />
            <StepRates
              v-else-if="currentStep === 3"
              v-model="ratesData"
              :selected-games="gamesData.games"
              @continue="handleStepContinue"
              @back="handleStepBack"
            />
            <StepVerify
              v-else-if="currentStep === 4"
              v-model="verifyData"
              @continue="handleStepContinue"
              @back="handleStepBack"
            />
            <StepReview
              v-else-if="currentStep === 5"
              v-model="reviewData"
              :account-data="accountData"
              :games-data="gamesData"
              :rates-data="ratesData"
              :verify-data="verifyData"
              :submitting="submitting"
              :submit-error="submitError"
              @submit="handleSubmit"
              @back="handleStepBack"
              @edit="currentStep = $event"
            />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
