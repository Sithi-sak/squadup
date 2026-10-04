<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { PhPlus, PhUserCircle, PhX } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import GameSkillsEditor from '@/components/players/GameSkillsEditor.vue'
import { mockCurrentUser } from '@/mocks/users'
import { useAuthStore } from '@/stores/auth'
import { gameSkillsOf, usePlayersStore } from '@/stores/players'
import { resolveAvatarUrl } from '@/utils/avatar'
import {
  isGameSkillComplete,
  toGameSkillDrafts,
  toGameSkills,
  type GameSkillDraft,
} from '@/utils/gameSkills'

/** The Pal's public profile: everything a buyer sees on `/players/{id}`. Name, username, email
 * and region are deliberately not here - they are account-level fields the Account tab owns, and
 * duplicating the name input here left two "Display name" boxes where only one of them saved. */
const emit = defineEmits<{ navigate: [string] }>()

const authStore = useAuthStore()
const playersStore = usePlayersStore()
const toast = useToast()

const avatarUrl = computed(() =>
  resolveAvatarUrl(authStore.user?.id ?? mockCurrentUser.id, playersStore.mine?.avatarUrl),
)
const accountDisplayName = computed(
  () => authStore.user?.displayName ?? mockCurrentUser.displayName,
)
const handle = computed(() => playersStore.mine?.handle ?? authStore.user?.handle ?? '')
const tier = computed(() => playersStore.mine?.tier ?? 'Pal 1')

onMounted(() => {
  if (!playersStore.mine) playersStore.fetchMine()
})

const headline = ref('')
const bio = ref('')
const languages = ref<string[]>([])

/** `mine` is usually still loading on mount, so the form fills in from the fetch rather than
 * from a one-shot read of an empty store. Keyed on these fields only, so saving the Games card
 * (which replaces `mine`) doesn't wipe unsaved edits here. */
watch(
  () => {
    const mine = playersStore.mine
    return mine ? JSON.stringify([mine.tagline, mine.bio, mine.languages]) : null
  },
  () => {
    const mine = playersStore.mine
    if (!mine) return
    headline.value = mine.tagline ?? ''
    bio.value = mine.bio ?? ''
    languages.value = [...mine.languages]
  },
  { immediate: true },
)

const languageOptions = ['English', 'Khmer', 'Vietnamese', 'Chinese', 'Korean', 'Japanese']
const languageMenuItems = computed(() =>
  languageOptions
    .filter((lang) => !languages.value.includes(lang))
    .map((lang) => ({ label: lang, onSelect: () => languages.value.push(lang) })),
)

function removeLanguage(lang: string) {
  languages.value = languages.value.filter((l) => l !== lang)
}

const dirty = computed(() => {
  const mine = playersStore.mine
  if (!mine) return false
  return (
    headline.value !== (mine.tagline ?? '') ||
    bio.value !== (mine.bio ?? '') ||
    languages.value.join('|') !== mine.languages.join('|')
  )
})

const saving = ref(false)

async function saveProfile() {
  saving.value = true
  try {
    await playersStore.updateMine({
      tagline: headline.value,
      bio: bio.value,
      languages: languages.value,
    })
    toast.add({ title: 'Profile saved', color: 'success' })
  } catch (err) {
    toast.add({
      title: "Couldn't save profile",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    saving.value = false
  }
}

// Games & skills (4.65): its own Save, so a half-edited rank never blocks saving the bio above.
const games = ref<string[]>([])
const skills = ref<Record<string, GameSkillDraft>>({})

function resetGames() {
  const mine = playersStore.mine
  if (!mine) return
  const saved = gameSkillsOf(mine)
  games.value = saved.map((s) => s.game)
  skills.value = toGameSkillDrafts(saved)
}
// Same idea as the profile watch above: only a change to the saved games refills this card.
watch(
  () => (playersStore.mine ? JSON.stringify(gameSkillsOf(playersStore.mine)) : null),
  resetGames,
  { immediate: true },
)

const gamesDirty = computed(() => {
  const mine = playersStore.mine
  if (!mine) return false
  return JSON.stringify(toGameSkills(games.value, skills.value)) !== JSON.stringify(gameSkillsOf(mine))
})
const gamesValid = computed(
  () => games.value.length > 0 && games.value.every((game) => isGameSkillComplete(game, skills.value[game])),
)

const savingGames = ref(false)

async function saveGames() {
  savingGames.value = true
  try {
    await playersStore.updateMine({ gameSkills: toGameSkills(games.value, skills.value) })
    toast.add({ title: 'Games saved', color: 'success' })
  } catch (err) {
    toast.add({
      title: "Couldn't save games",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    savingGames.value = false
  }
}

const avatarFileInput = ref<HTMLInputElement | null>(null)
const avatarUploading = ref(false)

function openAvatarPicker() {
  avatarFileInput.value?.click()
}

async function onAvatarSelected(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  ;(event.target as HTMLInputElement).value = ''
  if (!file) return
  avatarUploading.value = true
  try {
    await playersStore.updateAvatar(file)
  } catch (err) {
    toast.add({
      title: 'Could not update photo',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    avatarUploading.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Public profile</h2>
      <p class="mt-1 text-sm text-slate-400">This is what buyers see on your Pal page.</p>

      <div class="mt-4 flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <UAvatar :src="avatarUrl" size="xl" class="bg-white/10 text-slate-300">
            <PhUserCircle :size="28" />
          </UAvatar>
          <div>
            <p class="font-semibold text-white">{{ accountDisplayName }}</p>
            <p class="text-sm text-slate-400">
              {{ tier }}<span v-if="handle"> · {{ handle }}</span>
            </p>
          </div>
        </div>
        <UButton
          color="neutral"
          variant="soft"
          size="md"
          class="rounded-full"
          :loading="avatarUploading"
          @click="openAvatarPicker"
        >
          Change photo
        </UButton>
        <input
          ref="avatarFileInput"
          type="file"
          accept="image/png,image/jpeg,image/webp"
          class="hidden"
          @change="onAvatarSelected"
        />
      </div>

      <p class="mt-3 text-sm text-slate-500">
        Your name and username live in
        <button
          type="button"
          class="cursor-pointer text-brand-400 hover:underline"
          @click="emit('navigate', 'account')"
        >
          Account
        </button>
      </p>

      <div class="mt-6 flex flex-col gap-2">
        <label for="profile-headline" class="text-sm text-slate-300">Headline</label>
        <UInput
          id="profile-headline"
          v-model="headline"
          placeholder="One line buyers see on your card"
          variant="subtle"
          size="lg"
        />
      </div>

      <div class="mt-5 flex flex-col gap-2">
        <label for="profile-bio" class="text-sm text-slate-300">Bio</label>
        <UTextarea
          id="profile-bio"
          v-model="bio"
          placeholder="Your rank, what you play and when you are usually online"
          variant="subtle"
          :rows="3"
        />
      </div>

      <div class="mt-5 flex flex-col gap-2">
        <span class="text-sm text-slate-300">Languages</span>
        <div class="flex flex-wrap items-center gap-2">
          <UBadge
            v-for="lang in languages"
            :key="lang"
            color="primary"
            variant="solid"
            size="lg"
            class="gap-2 rounded-full"
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
          </UBadge>
          <UDropdownMenu v-if="languageMenuItems.length" :items="languageMenuItems">
            <UButton color="neutral" variant="soft" size="sm" class="gap-1 rounded-full">
              <PhPlus :size="14" />
              Add
            </UButton>
          </UDropdownMenu>
        </div>
      </div>

      <div class="mt-5 flex justify-end">
        <UButton
          color="primary"
          class="rounded-full px-6"
          :loading="saving"
          :disabled="!dirty"
          @click="saveProfile"
        >
          Save changes
        </UButton>
      </div>
    </div>

    <div v-if="playersStore.mine" class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Games &amp; skills</h2>
      <p class="mt-1 text-sm text-slate-400">
        The games you play, with your rank and role in each. Shown on your Pal page and browse card.
      </p>

      <div class="mt-5 flex flex-col gap-5">
        <GameSkillsEditor v-model:games="games" v-model:skills="skills" card-class="bg-gray-900/40" />
      </div>

      <p v-if="!games.length" class="mt-3 text-sm text-amber-400">Add at least one game.</p>

      <div class="mt-5 flex justify-end gap-2">
        <UButton
          v-if="gamesDirty"
          color="neutral"
          variant="ghost"
          class="rounded-full px-4"
          :disabled="savingGames"
          @click="resetGames"
        >
          Discard
        </UButton>
        <UButton
          color="primary"
          class="rounded-full px-6"
          :loading="savingGames"
          :disabled="!gamesDirty || !gamesValid"
          @click="saveGames"
        >
          Save games
        </UButton>
      </div>
    </div>
  </div>
</template>
