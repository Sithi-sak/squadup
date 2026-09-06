<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { PhPlus, PhX } from '@phosphor-icons/vue'
import { competitiveGames, games } from '@/data/games'
import type { GamesStepData } from './types'

const data = defineModel<GamesStepData>({ required: true })

const emit = defineEmits<{ continue: []; back: [] }>()

const gameOptions = competitiveGames.map((game) => game.name)

const languageOptions = ['English', 'Khmer', 'Vietnamese', 'Chinese', 'Korean', 'Japanese']

const remainingGames = computed(() => gameOptions.filter((game) => !data.value.games.includes(game)))
const remainingLanguages = computed(() =>
  languageOptions.filter((lang) => !data.value.languages.includes(lang)),
)

const pendingGame = ref<string | null>(null)
watch(pendingGame, (game) => {
  if (!game) return
  addGame(game)
  pendingGame.value = null
})

// Drive the "Highest rank" and "Role" fields off the first selected game with a known
// rank/role ladder, since the form only tracks a single rank and role across all of a Pal's games.
const rankOptions = computed(() => {
  for (const game of data.value.games) {
    const ranks = games.find((g) => g.name === game)?.ranks
    if (ranks) return ranks
  }
  return null
})
const roleOptions = computed(() => {
  for (const game of data.value.games) {
    const roles = games.find((g) => g.name === game)?.roles
    if (roles) return roles
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
const gamePickerUi = { base: `${pillButtonClass} px-4 py-2` }
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

        <USelectMenu
          v-if="remainingGames.length"
          v-model="pendingGame"
          :items="remainingGames"
          placeholder="Add a game"
          variant="none"
          :ui="gamePickerUi"
        >
          <template #default>
            <span class="flex items-center gap-2">
              <PhPlus :size="16" />
              Add game
            </span>
          </template>
        </USelectMenu>
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
      <USelect
        v-if="roleOptions"
        id="role"
        v-model="data.role"
        :items="roleOptions"
        placeholder="Select your role"
        variant="subtle"
        size="md"
        class="w-full"
        :ui="fieldUi"
      />
      <UInput
        v-else
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
