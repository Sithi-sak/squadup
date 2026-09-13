<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { PhUserCircle } from '@phosphor-icons/vue'
import { usePlayersStore, type PlayerSummary } from '@/stores/players'
import { useFeedStore } from '@/stores/feed'
import { resolveAvatarUrl } from '@/utils/avatar'

const playersStore = usePlayersStore()
const feedStore = useFeedStore()

onMounted(() => {
  playersStore.fetchSuggested()
})

function subtitleFor(pal: PlayerSummary): string {
  const game = pal.games[0]
  if (game && pal.rating) return `${game} · ${pal.rating.toFixed(1)}`
  return game ?? 'New Pal'
}

const following = ref(new Set<string>())

async function follow(pal: PlayerSummary) {
  if (!pal.userId || following.value.has(pal.id)) return
  following.value.add(pal.id)
  try {
    await feedStore.toggleFollow(pal.userId, false)
    playersStore.suggested = playersStore.suggested.filter((p) => p.id !== pal.id)
  } finally {
    following.value.delete(pal.id)
  }
}
</script>

<template>
  <div v-if="playersStore.suggestedLoading && !playersStore.suggested.length" class="rounded-xl bg-gray-800/70 p-5">
    <div class="flex items-center justify-between">
      <USkeleton class="h-5 w-32" />
      <USkeleton class="h-4 w-12" />
    </div>
    <div class="mt-4 flex flex-col gap-4">
      <div v-for="n in 4" :key="n" class="flex items-center gap-3">
        <USkeleton class="h-10 w-10 shrink-0 rounded-full" />
        <div class="min-w-0 flex-1 space-y-1.5">
          <USkeleton class="h-3.5 w-24" />
          <USkeleton class="h-3 w-16" />
        </div>
        <USkeleton class="h-6 w-16 shrink-0 rounded-full" />
      </div>
    </div>
  </div>

  <div v-else-if="playersStore.suggested.length" class="rounded-xl bg-gray-800/50 p-5">
    <div class="flex items-center justify-between">
      <h3 class="font-semibold text-white">Suggested Pals</h3>
      <router-link to="/players" class="text-sm text-brand-400 hover:text-brand-300">See all</router-link>
    </div>
    <div class="mt-4 flex flex-col gap-4">
      <div v-for="pal in playersStore.suggested" :key="pal.id" class="flex items-center gap-3">
        <router-link :to="`/players/${pal.id}`" class="flex min-w-0 flex-1 items-center gap-3">
          <UAvatar
            :src="resolveAvatarUrl(pal.id, pal.avatarUrl)"
            size="lg"
            class="shrink-0 bg-white/10 text-slate-300"
          >
            <PhUserCircle :size="20" />
          </UAvatar>
          <div class="min-w-0 flex-1">
            <p class="truncate text-md font-medium text-white">{{ pal.displayName }}</p>
            <p class="truncate text-sm text-slate-400">{{ subtitleFor(pal) }}</p>
          </div>
        </router-link>
        <UButton
          color="primary"
          size="sm"
          class="shrink-0 rounded-full"
          :loading="following.has(pal.id)"
          @click="follow(pal)"
        >
          Follow
        </UButton>
      </div>
    </div>
  </div>
</template>
