<script setup lang="ts">
import { computed } from 'vue'
import { PhPlus, PhX } from '@phosphor-icons/vue'
import { games } from '@/data/games'
import type { GamesStepData } from './types'

const data = defineModel<GamesStepData>({ required: true })

const emit = defineEmits<{ continue: []; back: [] }>()

const gameOptions = [
  'Valorant',
  'League of Legends',
  'Mobile Legends: Bang Bang',
  'Dota 2',
  'Counter-Strike 2',
  'Overwatch 2',
  'Apex Legends',
  'PUBG Mobile',
  'Free Fire',
  'Honor of Kings',
]

const languageOptions = ['English', 'Khmer', 'Vietnamese', 'Chinese', 'Korean', 'Japanese']

const remainingGames = computed(() => gameOptions.filter((game) => !data.value.games.includes(game)))
const remainingLanguages = computed(() =>
  languageOptions.filter((lang) => !data.value.languages.includes(lang)),
)

const gameMenuItems = computed(() =>
  remainingGames.value.map((game) => ({ label: game, onSelect: () => addGame(game) })),
)

// Drive the "Highest rank" field off the first selected game with a known rank ladder,
// since the form only tracks a single rank across all of a Pal's games.
const rankOptions = computed(() => {
  for (const game of data.value.games) {
    const ranks = games.find((g) => g.name === game)?.ranks
    if (ranks) return ranks
  }
  return null
})
const languageMenuItems = computed(() =>
  remainingLanguages.value.map((lang) => ({ label: lang, onSelect: () => addLanguage(lang) })),
)

function addGame(game: string) {
  data.value.games.push(game)
}

function removeGame(game: string) {
  data.value.games = data.value.games.filter((g) => g !== game)
}

function addLanguage(lang: string) {
  data.value.languages.push(lang)
}

function removeLanguage(lang: string) {
  data.value.languages = data.value.languages.filter((l) => l !== lang)
}

const canSubmit = computed(
  () =>
    data.value.games.length > 0 &&
    data.value.highestRank.trim().length > 0 &&
    data.value.role.trim().length > 0 &&
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
    <div class="flex flex-col gap-3">
      <label class="text-sm font-medium text-white">Games you play</label>
      <div class="flex flex-wrap items-center gap-3">
        <span
          v-for="game in data.games"
          :key="game"
          class="flex items-center gap-2 rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white"
        >
          {{ game }}
          <button
            type="button"
            class="cursor-pointer"
            :aria-label="`Remove ${game}`"
            @click="removeGame(game)"
          >
            <PhX :size="14" weight="bold" />
          </button>
        </span>

        <UDropdownMenu v-if="remainingGames.length" :items="gameMenuItems">
          <UButton color="neutral" variant="soft" :class="pillButtonClass">
            <PhPlus :size="16" />
            Add game
          </UButton>
        </UDropdownMenu>
      </div>
    </div>

    <div class="flex flex-col gap-2">
      <label for="highestRank" class="text-sm font-medium text-white">Highest rank</label>
      <USelect
        v-if="rankOptions"
        id="highestRank"
        v-model="data.highestRank"
        :items="rankOptions"
        placeholder="Select your rank"
        variant="subtle"
        size="md"
        class="w-full"
        :ui="fieldUi"
      />
      <UInput
        v-else
        id="highestRank"
        v-model="data.highestRank"
        placeholder="Immortal 3"
        variant="subtle"
        size="md"
        :ui="fieldUi"
      />
    </div>

    <div class="flex flex-col gap-2">
      <label for="role" class="text-sm font-medium text-white">Roles you main</label>
      <UInput
        id="role"
        v-model="data.role"
        placeholder="Healer"
        variant="subtle"
        size="md"
        :ui="fieldUi"
      />
    </div>

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
