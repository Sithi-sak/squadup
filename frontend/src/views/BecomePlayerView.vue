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

const router = useRouter()

const currentStep = ref(1)
const progressPct = computed(() => (currentStep.value === 1 ? 8 : (currentStep.value - 1) * 20))

const accountData = ref(createAccountStepData())
const gamesData = ref(createGamesStepData())
const ratesData = ref(createRatesStepData())
const verifyData = ref(createVerifyStepData())
const reviewData = ref(createReviewStepData())
const submitted = ref(false)

function handleStepContinue() {
  currentStep.value = Math.min(currentStep.value + 1, becomePlayerSteps.length)
}

function handleStepBack() {
  currentStep.value = Math.max(currentStep.value - 1, 1)
}

function handleSubmit() {
  console.log('Pal application submitted', {
    account: accountData.value,
    games: gamesData.value,
    rates: ratesData.value,
    verify: verifyData.value,
  })
  submitted.value = true
}
</script>

<template>
  <div class="min-h-screen bg-squadup-dark">
    <header class="border-b border-gray-800 px-6 py-5">
      <div class="mx-auto flex max-w-5xl items-center justify-between">
        <router-link to="/" class="flex items-center gap-2">
          <img :src="brandLogo" alt="SquadUp" class="h-[24px] w-auto" />
          <span class="text-sm text-slate-400">· Pal Application</span>
        </router-link>
        <UButton
          v-if="!submitted"
          color="neutral"
          variant="soft"
          square
          class="rounded-full bg-gray-800 text-white hover:bg-gray-700"
          aria-label="Close"
          @click="router.push('/')"
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
