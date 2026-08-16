<script setup lang="ts">
import { useRouter } from 'vue-router'
import { PhGameController, PhMagnifyingGlass } from '@phosphor-icons/vue'

const open = defineModel<boolean>('open', { required: true })

const router = useRouter()

function choose(path: string) {
  open.value = false
  router.push(path)
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="What brings you to SquadUp?"
    description="You can always become a Pal later from your account."
  >
    <template #body>
      <div class="grid gap-4 sm:grid-cols-2">
        <button
          type="button"
          class="flex flex-col items-start gap-3 rounded-2xl bg-gray-800 p-5 text-left ring-1 ring-inset ring-gray-700 transition hover:ring-brand-600"
          @click="choose('/players')"
        >
          <PhMagnifyingGlass :size="24" class="text-brand-300" />
          <span class="font-semibold text-white">Just looking for a player</span>
          <span class="text-sm text-slate-400">Browse Pals and book a session.</span>
        </button>

        <button
          type="button"
          class="flex flex-col items-start gap-3 rounded-2xl bg-gray-800 p-5 text-left ring-1 ring-inset ring-gray-700 transition hover:ring-brand-600"
          @click="choose('/become-player')"
        >
          <PhGameController :size="24" class="text-brand-300" />
          <span class="font-semibold text-white">Become a Pal</span>
          <span class="text-sm text-slate-400">Get paid to play with others.</span>
        </button>
      </div>
    </template>
  </UModal>
</template>
