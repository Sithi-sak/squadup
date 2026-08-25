<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { useNotificationsStore } from '@/stores/notifications'
import { notificationIcon, formatNotificationTime, isNotificationToday } from '@/utils/notifications'

const store = useNotificationsStore()
const toast = useToast()

const tab = ref<'all' | 'unread'>('all')

const filtered = computed(() => (tab.value === 'unread' ? store.unread : store.notifications))
const today = computed(() => filtered.value.filter((n) => isNotificationToday(n.createdAt)))
const earlier = computed(() => filtered.value.filter((n) => !isNotificationToday(n.createdAt)))

onMounted(() => {
  store.fetchNotifications()
})

async function markAllRead() {
  try {
    await store.markAllRead()
  } catch (err) {
    toast.add({
      title: 'Could not mark all as read',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] px-4 pt-14 pb-14 md:px-6 md:pt-16">
    <div class="mx-auto max-w-2xl">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <h1 class="text-3xl font-bold text-white">Notifications</h1>
        <button
          type="button"
          class="cursor-pointer text-sm font-medium text-brand-400 hover:text-brand-300"
          @click="markAllRead"
        >
          Mark all read
        </button>
      </div>

      <div class="mt-5 flex flex-wrap items-center gap-2">
        <UButton
          :color="tab === 'all' ? 'primary' : 'neutral'"
          :variant="tab === 'all' ? 'solid' : 'soft'"
          size="sm"
          class="rounded-full"
          @click="tab = 'all'"
        >
          All
        </UButton>
        <UButton
          :color="tab === 'unread' ? 'primary' : 'neutral'"
          :variant="tab === 'unread' ? 'solid' : 'soft'"
          size="sm"
          class="gap-1.5 rounded-full"
          @click="tab = 'unread'"
        >
          Unread{{ store.unreadCount > 0 ? ` · ${store.unreadCount}` : '' }}
        </UButton>
      </div>

      <p v-if="store.loading" class="mt-10 text-center text-sm text-slate-400">Loading notifications...</p>

      <UEmpty
        v-else-if="filtered.length === 0"
        title="No notifications"
        description="You're all caught up. New activity will show up here."
        class="py-16 text-white"
      />

      <div v-else class="mt-6 overflow-hidden rounded-xl bg-gray-800/70">
        <template v-if="today.length > 0">
          <p class="px-5 pt-4 pb-2 text-sm font-medium text-slate-400">Today</p>
          <div
            v-for="notification in today"
            :key="notification.id"
            class="flex items-start gap-3 border-b border-white/5 px-5 py-4 last:border-b-0 hover:bg-white/5"
          >
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-600">
              <component :is="notificationIcon[notification.type]" :size="20" weight="bold" class="text-white" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="text-white">{{ notification.message }}</p>
              <p class="mt-0.5 text-sm text-slate-400">{{ formatNotificationTime(notification.createdAt) }}</p>
            </div>
            <span v-if="!notification.read" class="mt-2 h-2.5 w-2.5 shrink-0 rounded-full bg-brand-400" />
          </div>
        </template>

        <template v-if="earlier.length > 0">
          <p class="px-5 pt-4 pb-2 text-sm font-medium text-slate-400">Earlier</p>
          <div
            v-for="notification in earlier"
            :key="notification.id"
            class="flex items-start gap-3 border-b border-white/5 px-5 py-4 last:border-b-0 hover:bg-white/5"
          >
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-600">
              <component :is="notificationIcon[notification.type]" :size="20" weight="bold" class="text-white" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="text-white">{{ notification.message }}</p>
              <p class="mt-0.5 text-sm text-slate-400">{{ formatNotificationTime(notification.createdAt) }}</p>
            </div>
            <span v-if="!notification.read" class="mt-2 h-2.5 w-2.5 shrink-0 rounded-full bg-brand-400" />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
