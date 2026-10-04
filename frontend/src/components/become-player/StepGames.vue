<script setup lang="ts">
import { computed } from 'vue'
import { PhPlus, PhX } from '@phosphor-icons/vue'
import GameSkillsEditor from '@/components/players/GameSkillsEditor.vue'
import { isGameSkillComplete } from '@/utils/gameSkills'
import type { GamesStepData } from './types'

const data = defineModel<GamesStepData>({ required: true })

const emit = defineEmits<{ continue: []; back: [] }>()

const languageOptions = ['English', 'Khmer', 'Vietnamese', 'Chinese', 'Korean', 'Japanese']

const remainingLanguages = computed(() =>
  languageOptions.filter((lang) => !data.value.languages.includes(lang)),
)
const languageMenuItems = computed(() =>
  remainingLanguages.value.map((lang) => ({ label: lang, onSelect: () => addLanguage(lang) })),
)

function addLanguage(lang: string) {
  data.value.languages.push(lang)
}

function removeLanguage(lang: string) {
  data.value.languages = data.value.languages.filter((l) => l !== lang)
}

const canSubmit = computed(
  () =>
    data.value.games.length > 0 &&
    data.value.games.every((game) => isGameSkillComplete(game, data.value.skills[game])) &&
    data.value.languages.length > 0,
)

const fieldUi = {
  base: 'bg-gray-900 px-5 py-3.5 text-sm ring-0 focus-visible:ring-2 focus-visible:ring-brand-600',
}

const pillButtonClass = 'gap-2 rounded-full bg-gray-800 text-white hover:bg-gray-700'
</script>

<template>
  <h2 class="text-2xl font-semibold text-white sm:text-3xl">Your games &amp; skills</h2>
  <p class="mt-2 text-slate-400">
    Tell players what you play and how good you are. You can add more later.
  </p>

  <form class="mt-8 flex flex-col gap-6" @submit.prevent="canSubmit && emit('continue')">
    <GameSkillsEditor v-model:games="data.games" v-model:skills="data.skills" />

    <div class="flex flex-col gap-3">
      <label class="text-sm font-medium text-white">Languages</label>
      <div class="flex flex-wrap items-center gap-3">
        <span
          v-for="lang in data.languages"
          :key="lang"
          class="flex items-center gap-2 rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white"
        >
          {{ lang }}
          <button
            type="button"
            class="cursor-pointer"
            :aria-label="`Remove ${lang}`"
            @click="removeLanguage(lang)"
          >
            <PhX :size="14" weight="bold" />
          </button>
        </span>

        <UDropdownMenu v-if="remainingLanguages.length" :items="languageMenuItems">
          <UButton color="neutral" variant="soft" :class="pillButtonClass">
            <PhPlus :size="16" />
            Add
          </UButton>
        </UDropdownMenu>
      </div>
    </div>

    <div class="flex flex-col gap-2">
      <label for="headline" class="text-sm font-medium text-white">Your headline</label>
      <UInput
        id="headline"
        v-model="data.headline"
        placeholder="e.g. Immortal duo who actually carries — never battle alone"
        variant="subtle"
        size="md"
        :ui="fieldUi"
      />
    </div>

    <USeparator />

    <div class="flex justify-between">
      <UButton
        type="button"
        color="neutral"
        variant="soft"
        class="rounded-full bg-gray-800 px-8 py-2 text-base text-white hover:bg-gray-700"
        @click="emit('back')"
      >
        Back
      </UButton>
      <UButton
        type="submit"
        color="primary"
        :disabled="!canSubmit"
        class="rounded-full px-8 py-2 text-base"
      >
        Continue
      </UButton>
    </div>
  </form>
</template>
