<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  PhBriefcase,
  PhClipboardText,
  PhCurrencyDollar,
  PhEnvelopeSimple,
  PhGearSix,
  PhSquaresFour,
  PhUserCircle,
} from '@phosphor-icons/vue'
import { mockCurrentUser } from '@/mocks/users'
import { useAuthStore } from '@/stores/auth'
import { usePlayersStore } from '@/stores/players'
import { resolveAvatarUrl } from '@/utils/avatar'

defineProps<{
  active: 'dashboard' | 'orders' | 'services' | 'earnings' | 'messages' | 'settings'
}>()

const authStore = useAuthStore()
const playersStore = usePlayersStore()

const online = ref(true)

const displayName = computed(() => authStore.user?.displayName ?? mockCurrentUser.displayName)
const avatarUrl = computed(() =>
  resolveAvatarUrl(authStore.user?.id ?? mockCurrentUser.id, playersStore.mine?.avatarUrl),
)

const navItems = [
  { key: 'dashboard', label: 'Dashboard', to: '/dashboard/player', icon: PhSquaresFour },
  { key: 'orders', label: 'Orders', to: '/dashboard/player/orders', icon: PhClipboardText },
  { key: 'services', label: 'My services', to: '/dashboard/player/services', icon: PhBriefcase },
  { key: 'earnings', label: 'Earnings', to: '/dashboard/player/earnings', icon: PhCurrencyDollar },
  { key: 'messages', label: 'Messages', to: '/messages', icon: PhEnvelopeSimple },
  { key: 'settings', label: 'Settings', to: '/settings', icon: PhGearSix },
] as const
</script>

<template>
  <aside class="flex h-full flex-col justify-between">
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
    </nav>

    <div class="flex flex-col gap-4 border-t border-white/10 pt-4">
      <div class="flex items-center justify-between gap-2">
        <span class="text-sm text-slate-300">You're online</span>
        <USwitch v-model="online" color="primary" />
      </div>
      <div class="flex items-center gap-2.5">
        <UAvatar :src="avatarUrl" size="md" class="bg-white/10 text-slate-300">
          <PhUserCircle :size="22" />
        </UAvatar>
        <div class="min-w-0">
          <p class="truncate text-sm font-semibold text-white">{{ displayName }}</p>
          <p class="text-xs text-slate-400">{{ playersStore.mine?.tier ?? 'Pal' }}</p>
        </div>
      </div>
    </div>
  </aside>
</template>
