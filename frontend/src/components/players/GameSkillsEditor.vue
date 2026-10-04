<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { PhPlus, PhX } from '@phosphor-icons/vue'
import { competitiveGames } from '@/data/games'
import { gameRankOptions, gameRoleOptions, type GameSkillDraft } from '@/utils/gameSkills'

/** Game chips plus a rank/role card per game (4.64). Shared by Become a Pal's Games step and
 * Settings > Profile (4.65), so both edit `players.game_skills` the same way. */
const props = withDefaults(
  defineProps<{
    /** Classes for each game's rank/role card, so it reads on both page and card backgrounds. */
    cardClass?: string
    fieldUi?: { base: string }
  }>(),
  {
    cardClass: 'bg-gray-800/50',
    fieldUi: () => ({
      base: 'bg-gray-900 px-5 py-3.5 text-sm ring-0 focus-visible:ring-2 focus-visible:ring-brand-600',
    }),
  },
)

const selectedGames = defineModel<string[]>('games', { required: true })
const skills = defineModel<Record<string, GameSkillDraft>>('skills', { required: true })

const gameOptions = competitiveGames.map((game) => game.name)
const remainingGames = computed(() => gameOptions.filter((game) => !selectedGames.value.includes(game)))

const pendingGame = ref<string | undefined>()
watch(pendingGame, (game) => {
  if (!game) return
  addGame(game)
  pendingGame.value = undefined
})

function addGame(game: string) {
  selectedGames.value = [...selectedGames.value, game]
  if (!skills.value[game]) skills.value = { ...skills.value, [game]: { rank: '', role: '' } }
}

function removeGame(game: string) {
  selectedGames.value = selectedGames.value.filter((g) => g !== game)
  skills.value = Object.fromEntries(Object.entries(skills.value).filter(([key]) => key !== game))
}

const pillButtonClass = 'gap-2 rounded-full bg-gray-800 text-white hover:bg-gray-700'
const gamePickerUi = { base: `${pillButtonClass} px-4 py-2` }
</script>

<template>
  <div class="flex flex-col gap-3">
    <label class="text-sm font-medium text-white">Games you play</label>
    <div class="flex flex-wrap items-center gap-3">
      <span
        v-for="game in selectedGames"
        :key="game"
        class="flex items-center gap-2 rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white"
      >
        {{ game }}
        <button type="button" class="cursor-pointer" :aria-label="`Remove ${game}`" @click="removeGame(game)">
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

  <div
    v-for="game in selectedGames"
    :key="game"
    class="flex flex-col gap-3 rounded-2xl p-4"
    :class="props.cardClass"
  >
    <p class="text-sm font-semibold text-white">{{ game }}</p>
    <div v-if="skills[game]" class="grid gap-4 sm:grid-cols-2">
      <div class="flex flex-col gap-2">
        <label :for="`rank-${game}`" class="text-sm font-medium text-slate-300">Highest rank</label>
        <USelect
          v-if="gameRankOptions(game)"
          :id="`rank-${game}`"
          v-model="skills[game].rank"
          :items="gameRankOptions(game) ?? []"
          placeholder="Select your rank"
          variant="subtle"
          size="md"
          class="w-full"
          :ui="props.fieldUi"
        />
        <UInput
          v-else
          :id="`rank-${game}`"
          v-model="skills[game].rank"
          placeholder="Immortal 3"
          variant="subtle"
          size="md"
          :ui="props.fieldUi"
        />
      </div>

      <div class="flex flex-col gap-2">
        <label :for="`role-${game}`" class="text-sm font-medium text-slate-300">
          Role you main<span v-if="!gameRoleOptions(game)" class="text-slate-500"> (optional)</span>
        </label>
        <USelect
          v-if="gameRoleOptions(game)"
          :id="`role-${game}`"
          v-model="skills[game].role"
          :items="gameRoleOptions(game) ?? []"
          placeholder="Select your role"
          variant="subtle"
          size="md"
          class="w-full"
          :ui="props.fieldUi"
        />
        <UInput
          v-else
          :id="`role-${game}`"
          v-model="skills[game].role"
          placeholder="Healer"
          variant="subtle"
          size="md"
          :ui="props.fieldUi"
        />
      </div>
    </div>
  </div>
</template>
