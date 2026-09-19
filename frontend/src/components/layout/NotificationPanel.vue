<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { PhX } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { useNotificationsStore, type AppNotification } from '@/stores/notifications'
import { notificationIcon, notificationTone, formatNotificationTime } from '@/utils/notifications'

const props = defineProps<{ close?: () => void }>()

const router = useRouter()
const store = useNotificationsStore()
const toast = useToast()

const tab = ref<'all' | 'unread'>('all')
/** "Clear" wipes the list for good, so the first click only arms the confirm row. */
const confirmingClear = ref(false)
const clearing = ref(false)

const rows = computed(() => {
  const list = tab.value === 'unread' ? store.unread : store.notifications
  return list.slice(0, 6)
})

const hiddenCount = computed(
  () => (tab.value === 'unread' ? store.unread.length : store.notifications.length) - rows.value.length,
)

// Switching tabs mid-confirm would leave a destructive button armed under a different list.
watch(tab, () => {
  confirmingClear.value = false
})

function goToAll() {
  props.close?.()
  router.push('/notifications')
}

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

async function clearAll() {
  clearing.value = true
  try {
    await store.clearAll()
    confirmingClear.value = false
  } catch (err) {
    toast.add({
      title: 'Could not clear notifications',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    clearing.value = false
  }
}

async function dismiss(id: string) {
  try {
    await store.dismiss(id)
  } catch (err) {
    toast.add({
      title: 'Could not remove that notification',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}

async function markRead(id: string) {
  try {
    await store.markRead(id)
  } catch {
    // silent - a stray unread dot on a panel row isn't worth a toast
  }
}

function handleClick(notification: AppNotification) {
  markRead(notification.id)
  if (notification.type === 'message' && notification.threadId) {
    props.close?.()
    router.push({ name: 'messages', query: { thread: notification.threadId } })
  }
}
</script>

<template>
  <div class="flex w-80 flex-col sm:w-96">
    <div class="flex items-center justify-between gap-3 px-4 pt-4">
      <h3 class="flex items-center gap-2 text-lg font-bold text-white">
        Notifications
        <span
          v-if="store.unreadCount > 0"
          class="flex h-5 min-w-5 items-center justify-center rounded-full bg-brand-500 px-1.5 text-[11px] font-semibold text-white"
        >
          {{ store.unreadCount }}
        </span>
      </h3>

      <div v-if="!confirmingClear" class="flex items-center gap-2 text-sm font-medium">
        <button
          type="button"
          class="cursor-pointer text-brand-400 hover:text-brand-300 disabled:cursor-not-allowed disabled:text-slate-500 disabled:hover:text-slate-500"
          :disabled="store.unreadCount === 0"
          @click="markAllRead"
        >
          Mark all read
        </button>
        <span class="text-white/20" aria-hidden="true">|</span>
        <button
          type="button"
          class="cursor-pointer text-slate-400 hover:text-red-300 disabled:cursor-not-allowed disabled:text-slate-600 disabled:hover:text-slate-600"
          :disabled="store.notifications.length === 0"
          @click="confirmingClear = true"
        >
          Clear
        </button>
      </div>

      <div v-else class="flex items-center gap-2 text-sm font-medium">
        <button
          type="button"
          class="cursor-pointer text-slate-400 hover:text-white"
          @click="confirmingClear = false"
        >
          Cancel
        </button>
        <button
          type="button"
          class="cursor-pointer text-red-400 hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="clearing"
          @click="clearAll"
        >
          {{ clearing ? 'Clearing...' : 'Clear all' }}
        </button>
      </div>
    </div>

    <p v-if="confirmingClear" class="px-4 pt-2 text-xs text-slate-400">
      This removes every notification, read or not.
    </p>

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
      <div
        v-if="store.loading && store.notifications.length === 0"
        class="divide-y divide-white/5"
      >
        <div v-for="n in 3" :key="n" class="flex items-start gap-3 px-4 py-3">
          <USkeleton class="h-9 w-9 shrink-0 rounded-full" />
          <div class="min-w-0 flex-1 space-y-2">
            <USkeleton class="h-3.5 w-4/5" />
            <USkeleton class="h-3 w-16" />
          </div>
        </div>
      </div>

      <p v-else-if="rows.length === 0" class="px-4 py-8 text-center text-sm text-slate-400">
        {{ tab === 'unread' ? 'No unread notifications.' : "You're all caught up." }}
      </p>

      <template v-else>
        <div
          v-for="notification in rows"
          :key="notification.id"
          class="group relative border-b border-white/5 last:border-b-0"
          :class="notification.read ? 'hover:bg-white/5' : 'bg-brand-500/[0.07] hover:bg-brand-500/10'"
        >
          <span
            v-if="!notification.read"
            class="absolute inset-y-0 left-0 w-0.5 bg-brand-400"
            aria-hidden="true"
          />
          <button
            type="button"
            class="flex w-full cursor-pointer items-start gap-3 py-3 pr-9 pl-4 text-left"
            @click="handleClick(notification)"
          >
            <span
              class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full"
              :class="notificationTone[notification.type]"
            >
              <component :is="notificationIcon[notification.type]" :size="18" weight="bold" />
            </span>
            <span class="min-w-0 flex-1">
              <span
                class="line-clamp-2 block text-sm"
                :class="notification.read ? 'text-slate-300' : 'font-medium text-white'"
              >
                {{ notification.message }}
              </span>
              <span class="mt-0.5 block text-xs text-slate-400">
                {{ formatNotificationTime(notification.createdAt) }}
              </span>
            </span>
          </button>
          <button
            type="button"
            class="absolute top-3 right-2 cursor-pointer rounded-md p-1 text-slate-500 opacity-0 transition hover:bg-white/10 hover:text-white focus-visible:opacity-100 group-hover:opacity-100"
            :aria-label="`Remove notification: ${notification.message}`"
            @click.stop="dismiss(notification.id)"
          >
            <PhX :size="14" weight="bold" />
          </button>
        </div>
      </template>
    </div>

    <div class="border-t border-white/10 px-4 py-3">
      <button
        type="button"
        class="w-full cursor-pointer text-center text-sm font-medium text-brand-400 hover:text-brand-300"
        @click="goToAll"
      >
        See all notifications{{ hiddenCount > 0 ? ` (${hiddenCount} more)` : '' }}
      </button>
    </div>
  </div>
</template>
