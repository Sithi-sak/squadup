<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { PhBookmarkSimple, PhCompass, PhHouse, PhPlus, PhUserCircle, PhUsersThree } from '@phosphor-icons/vue'
import { mockCurrentUser } from '@/mocks/users'
import { useAuthStore } from '@/stores/auth'
import { usePlayersStore } from '@/stores/players'
import CreatePostModal from '@/components/modals/CreatePostModal.vue'
import { resolveAvatarUrl } from '@/utils/avatar'

defineProps<{
  active: 'feed' | 'following' | 'explore' | 'saved'
  showCreatePost?: boolean
}>()

const authStore = useAuthStore()
const playersStore = usePlayersStore()

onMounted(() => {
  playersStore.fetchMine()
})

const displayName = computed(() => authStore.user?.displayName ?? mockCurrentUser.displayName)
const email = computed(() => authStore.user?.email ?? mockCurrentUser.email)
const myPlayerProfile = computed(() => playersStore.mine)
const avatarUrl = computed(() =>
  resolveAvatarUrl(authStore.user?.id ?? mockCurrentUser.id, myPlayerProfile.value?.avatarUrl),
)

/** Posts/Followers/Following (3.18): a Pal's counts come from `myPlayerProfile`, a plain buyer's
 * from their own `users` row via `authStore` - either way every signed-in account has real
 * counts now, not just a Pal. */
const stats = computed(() => {
  if (myPlayerProfile.value) return myPlayerProfile.value
  if (!authStore.user) return null
  return {
    postsCount: authStore.user.postsCount,
    followersCount: authStore.user.followersCount,
    followingCount: authStore.user.followingCount,
  }
})

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
      <UAvatar :src="avatarUrl" size="3xl" class="bg-white/10 text-slate-300">
        <PhUserCircle :size="40" />
      </UAvatar>
      <p class="mt-3 text-lg font-semibold text-white">{{ displayName }}</p>
      <template v-if="myPlayerProfile">
        <p class="text-sm text-slate-400">{{ myPlayerProfile.handle }}</p>
        <UBadge color="primary" variant="soft" size="sm" class="mt-2 rounded-full text-xs text-brand-500">
          {{ myPlayerProfile.tier }}
        </UBadge>
      </template>
      <p v-else class="text-sm text-slate-400">{{ email }}</p>

      <div v-if="stats" class="mt-4 grid w-full grid-cols-3 divide-x divide-white/10 border-t border-white/10 pt-4">
        <div>
          <p class="font-semibold text-white">{{ formatCount(stats.postsCount) }}</p>
          <p class="text-xs text-slate-400">Posts</p>
        </div>
        <div>
          <p class="font-semibold text-white">{{ formatCount(stats.followersCount) }}</p>
          <p class="text-xs text-slate-400">Followers</p>
        </div>
        <div>
          <p class="font-semibold text-white">{{ formatCount(stats.followingCount) }}</p>
          <p class="text-xs text-slate-400">Following</p>
        </div>
      </div>
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
