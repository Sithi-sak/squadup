<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationsStore } from '@/stores/notifications'
import { notificationIcon, formatNotificationTime } from '@/utils/notifications'

const props = defineProps<{ close?: () => void }>()

const router = useRouter()
const store = useNotificationsStore()

const tab = ref<'all' | 'unread'>('all')

const rows = computed(() => {
  const list = tab.value === 'unread' ? store.unread : store.notifications
  return list.slice(0, 6)
})

function goToAll() {
  props.close?.()
  router.push('/notifications')
}
</script>

<template>
  <div class="flex w-80 flex-col sm:w-96">
    <div class="flex items-center justify-between px-4 pt-4">
      <h3 class="text-lg font-bold text-white">Notifications</h3>
      <button
        type="button"
        class="cursor-pointer text-sm font-medium text-brand-400 hover:text-brand-300"
        @click="store.markAllRead()"
      >
        Mark all read
      </button>
    </div>

    <div class="flex items-center gap-2 px-4 pt-3">
      <UButton
        :color="tab === 'all' ? 'primary' : 'neutral'"
        :variant="tab === 'all' ? 'solid' : 'soft'"
        size="xs"
        class="rounded-full"
        @click="tab = 'all'"
      >
        All
      </UButton>
      <UButton
        :color="tab === 'unread' ? 'primary' : 'neutral'"
        :variant="tab === 'unread' ? 'solid' : 'soft'"
        size="xs"
        class="gap-1.5 rounded-full"
        @click="tab = 'unread'"
      >
        Unread
        <span
          v-if="store.unreadCount > 0"
          class="flex h-4 min-w-4 items-center justify-center rounded-full bg-brand-500 px-1 text-[10px] font-semibold text-white"
        >
          {{ store.unreadCount }}
        </span>
      </UButton>
    </div>

    <div class="mt-3 max-h-96 overflow-y-auto border-t border-white/10">
      <p v-if="rows.length === 0" class="px-4 py-8 text-center text-sm text-slate-400">
        You're all caught up.
      </p>
      <button
        v-for="notification in rows"
        :key="notification.id"
        type="button"
        class="flex w-full cursor-pointer items-start gap-3 border-b border-white/5 px-4 py-3 text-left last:border-b-0 hover:bg-white/5"
        @click="store.markRead(notification.id)"
      >
        <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-600">
          <component :is="notificationIcon[notification.type]" :size="18" weight="bold" class="text-white" />
        </span>
        <span class="min-w-0 flex-1">
          <span class="line-clamp-2 block text-sm text-white">{{ notification.message }}</span>
          <span class="mt-0.5 block text-xs text-slate-400">{{ formatNotificationTime(notification.createdAt) }}</span>
        </span>
        <span
          v-if="!notification.read"
          class="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-400"
        />
      </button>
    </div>

    <div class="border-t border-white/10 px-4 py-3">
      <button
        type="button"
        class="w-full cursor-pointer text-center text-sm font-medium text-brand-400 hover:text-brand-300"
        @click="goToAll"
      >
        See all notifications
      </button>
    </div>
  </div>
</template>
