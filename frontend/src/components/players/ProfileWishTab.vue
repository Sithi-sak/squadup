<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { PhHeart } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import type { WishItem } from '@/stores/players'

/** `mockToggle` gates the heart button's interactivity: `wish_items.saved` is Pal-authored state
 * with no per-viewer mutation for a DB-backed profile (3.8b's decision), so it only stays
 * clickable against the authored mock fixtures, which predate that decision and have no backing
 * endpoint to call anyway. */
const props = defineProps<{ playerId: string; wish: WishItem[]; mockToggle?: boolean }>()

const router = useRouter()

const saved = reactive<Record<string, boolean>>(
  Object.fromEntries(props.wish.map((item) => [item.id, item.saved])),
)

function toggleSaved(id: string) {
  if (!props.mockToggle) return
  saved[id] = !saved[id]
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-xl font-bold text-white">Wish · {{ wish.length }} saved</h2>
      <span class="rounded-full bg-white/5 px-3.5 py-1.5 text-sm text-slate-400">Recently added</span>
    </div>

    <p v-if="wish.length === 0" class="py-10 text-center text-sm text-slate-400">No wishes saved yet.</p>

    <div v-else class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div v-for="item in wish" :key="item.id" class="overflow-hidden rounded-xl bg-gray-800/70">
        <div class="relative aspect-video w-full bg-white/5">
          <button
            type="button"
            class="absolute top-3 right-3 flex size-8 items-center justify-center rounded-full bg-squadup-dark/60 text-white"
            :class="!mockToggle && 'cursor-default'"
            :aria-label="saved[item.id] ? 'Remove from wishlist' : 'Add to wishlist'"
            @click="toggleSaved(item.id)"
          >
            <PhHeart :size="16" :weight="saved[item.id] ? 'fill' : 'regular'" :class="saved[item.id] && 'text-red-400'" />
          </button>
        </div>
        <div class="flex items-center justify-between gap-3 p-4">
          <div class="min-w-0">
            <p class="truncate font-semibold text-white">{{ item.title }}</p>
            <p class="text-sm text-slate-400">{{ [item.game, item.type].filter(Boolean).join(' · ') }}</p>
          </div>
          <div class="flex shrink-0 items-center gap-3">
            <span class="inline-flex items-center gap-1 text-sm font-semibold text-white">
              <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
              {{ item.priceCoins }}
            </span>
            <UButton
              v-if="item.serviceId"
              color="primary"
              size="sm"
              class="rounded-full"
              @click="router.push(`/players/${playerId}/services/${item.serviceId}`)"
            >
              Book
            </UButton>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
