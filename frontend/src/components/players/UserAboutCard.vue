<script setup lang="ts">
import { computed } from 'vue'
import { PhCalendarBlank } from '@phosphor-icons/vue'
import type { PublicProfile } from '@/stores/users'
import { usePalChat } from '@/composables/usePalChat'

/** The non-Pal counterpart of `ProfileAboutCard`, for the Feeds tab's left rail. A plain account
 * has no tagline, bio, timezone, languages or price, so this carries the counts, when they
 * joined, and Chat (no Book: there are no services to book). */
const props = defineProps<{
  profile: PublicProfile
  isOwnProfile?: boolean
}>()

const startChat = usePalChat()

const joined = computed(() =>
  new Date(props.profile.joinedAt).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
)

function formatCount(count: number) {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`
}
</script>

<template>
  <div class="flex flex-col gap-4 lg:sticky lg:top-20">
    <div class="rounded-xl bg-gray-800/70 p-5">
      <div class="grid grid-cols-3 divide-x divide-white/10 text-center">
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
          <PhCalendarBlank :size="16" />
          Joined {{ joined }}
        </p>
      </div>
    </div>

    <div v-if="!isOwnProfile && !profile.blocked" class="rounded-xl bg-gray-800/70 p-4">
      <UButton
        color="primary"
        variant="outline"
        block
        size="lg"
        class="rounded-full"
        @click="startChat(profile.id)"
      >
        Chat
      </UButton>
    </div>
  </div>
</template>
