<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { PhClock, PhGlobeHemisphereWest, PhStar } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import type { PlayerProfile, PlayerSummary } from '@/stores/players'
import { usePalChat } from '@/composables/usePalChat'

/** Left rail on the non-Services tabs. The services list only makes sense next to a service
 * detail, but Book/Chat should stay one click away wherever the viewer is, so this card carries
 * the CTA plus the at-a-glance facts the header has no room for. */
const props = defineProps<{
  player: PlayerSummary
  profile: PlayerProfile
  isOwnProfile?: boolean
  /** Viewer has blocked this Pal (4.39) - Chat and Book would 403, so they don't render. */
  blocked?: boolean
}>()

const router = useRouter()
const startChat = usePalChat()

const languages = computed(() => props.player.languages.join(', ') || props.profile.language)

function formatCount(count: number) {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`
}
</script>

<template>
  <div class="flex flex-col gap-4 lg:sticky lg:top-20">
    <div class="rounded-xl bg-gray-800/70 p-5">
      <p v-if="player.tagline" class="text-sm leading-relaxed text-slate-300">{{ player.tagline }}</p>

      <div class="mt-4 grid grid-cols-3 divide-x divide-white/10 border-t border-white/10 pt-4 text-center">
        <div>
          <p class="font-semibold text-white">{{ formatCount(profile.postsCount) }}</p>
          <p class="text-xs text-slate-400">Posts</p>
        </div>
        <div>
          <p class="font-semibold text-white">{{ formatCount(profile.followersCount) }}</p>
          <p class="text-xs text-slate-400">Followers</p>
        </div>
        <div>
          <p class="font-semibold text-white">{{ formatCount(profile.followingCount) }}</p>
          <p class="text-xs text-slate-400">Following</p>
        </div>
      </div>

      <div class="mt-4 flex flex-col gap-2 border-t border-white/10 pt-4 text-sm text-slate-400">
        <p class="inline-flex items-center gap-2">
          <PhClock :size="16" />
          {{ profile.timezone }}
        </p>
        <p class="inline-flex items-center gap-2">
          <PhGlobeHemisphereWest :size="16" />
          {{ languages }}
        </p>
        <p v-if="player.rating" class="inline-flex items-center gap-2">
          <PhStar :size="16" weight="fill" class="text-amber-400" />
          {{ player.rating.toFixed(1) }}
          <span v-if="player.reviewCount">· {{ player.reviewCount.toLocaleString() }} reviews</span>
        </p>
        <p v-if="player.priceCoins" class="inline-flex items-center gap-2">
          <img :src="coinIcon" alt="" class="h-4 w-4" />
          {{ player.priceCoins }}/game
        </p>
      </div>
    </div>

    <div v-if="!isOwnProfile && !blocked" class="rounded-xl bg-gray-800/70 p-4">
      <UButton
        color="primary"
        variant="outline"
        block
        size="lg"
        class="rounded-full"
        @click="startChat(profile.userId ?? player.userId)"
      >
        Chat
      </UButton>
      <UButton
        v-if="profile.services.length"
        color="primary"
        block
        size="lg"
        class="mt-2.5 rounded-full"
        @click="router.push(`/players/${player.id}/services/${profile.highlightedServiceId}`)"
      >
        Book
      </UButton>
    </div>
  </div>
</template>
