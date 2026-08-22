<script setup lang="ts">
import { computed, ref } from 'vue'
import { PhBookmarkSimple, PhCompass, PhHouse, PhPlus, PhUserCircle, PhUsersThree } from '@phosphor-icons/vue'
import { mockCurrentUser } from '@/mocks/users'
import { mockPlayerProfiles } from '@/mocks/playerProfiles'
import CreatePostModal from '@/components/modals/CreatePostModal.vue'

defineProps<{
  active: 'feed' | 'following' | 'explore' | 'saved'
  showCreatePost?: boolean
}>()

const myPlayerProfile = computed(() =>
  mockCurrentUser.playerId ? (mockPlayerProfiles[mockCurrentUser.playerId] ?? null) : null,
)

const navItems = [
  { key: 'feed', label: 'Feed', to: '/feed', icon: PhHouse },
  { key: 'following', label: 'Following', to: '/feed/following', icon: PhUsersThree },
  { key: 'explore', label: 'Explore', to: '/feed/explore', icon: PhCompass },
  { key: 'saved', label: 'Saved', to: '/feed/saved', icon: PhBookmarkSimple },
] as const

const createPostOpen = ref(false)

function formatCount(count: number) {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`
}
</script>

<template>
  <aside class="flex flex-col gap-5 rounded-xl bg-gray-800/70 p-5">
    <div class="flex flex-col items-center text-center">
      <UAvatar size="3xl" class="bg-white/10 text-slate-300">
        <PhUserCircle :size="40" />
      </UAvatar>
      <p class="mt-3 text-lg font-semibold text-white">{{ mockCurrentUser.displayName }}</p>
      <template v-if="myPlayerProfile">
        <p class="text-sm text-slate-400">{{ myPlayerProfile.handle }}</p>
        <UBadge color="primary" variant="soft" size="sm" class="mt-2 rounded-full text-xs text-brand-500">
          {{ myPlayerProfile.tier }}
        </UBadge>

        <div class="mt-4 grid w-full grid-cols-3 divide-x divide-white/10 border-t border-white/10 pt-4">
          <div>
            <p class="font-semibold text-white">{{ formatCount(myPlayerProfile.postsCount) }}</p>
            <p class="text-xs text-slate-400">Posts</p>
          </div>
          <div>
            <p class="font-semibold text-white">{{ formatCount(myPlayerProfile.followersCount) }}</p>
            <p class="text-xs text-slate-400">Followers</p>
          </div>
          <div>
            <p class="font-semibold text-white">{{ formatCount(myPlayerProfile.followingCount) }}</p>
            <p class="text-xs text-slate-400">Following</p>
          </div>
        </div>
      </template>
      <p v-else class="text-sm text-slate-400">{{ mockCurrentUser.email }}</p>
    </div>

    <nav class="flex flex-col gap-1">
      <router-link
        v-for="item in navItems"
        :key="item.key"
        :to="item.to"
        class="flex items-center gap-3 rounded-full px-3 py-2.5 text-sm transition-colors"
        :class="
          active === item.key
            ? 'bg-brand-600/15 text-brand-400'
            : 'text-slate-300 hover:bg-white/5 hover:text-white'
        "
      >
        <component :is="item.icon" :size="20" :weight="active === item.key ? 'fill' : 'regular'" />
        {{ item.label }}
      </router-link>
      <router-link
        :to="myPlayerProfile ? '/dashboard/player' : '/dashboard/user'"
        class="flex items-center gap-3 rounded-full px-3 py-2.5 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
      >
        <PhUserCircle :size="20" />
        Your profile
      </router-link>
    </nav>

    <UButton v-if="showCreatePost" color="primary" block class="rounded-full" @click="createPostOpen = true">
      <PhPlus :size="16" weight="bold" />
      Create post
    </UButton>

    <CreatePostModal v-model:open="createPostOpen" />
  </aside>
</template>
