import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { mockNotifications } from '@/mocks/notifications'

export type NotificationType =
  | 'booking'
  | 'message'
  | 'review'
  | 'payout'
  | 'follow'
  | 'service'
  | 'gift'
  | 'streak'

export interface AppNotification {
  id: string
  type: NotificationType
  message: string
  createdAt: string
  read: boolean
}

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref<AppNotification[]>([...mockNotifications])

  const sorted = computed(() =>
    [...notifications.value].sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    ),
  )
  const unread = computed(() => sorted.value.filter((n) => !n.read))
  const unreadCount = computed(() => unread.value.length)

  function markAllRead() {
    notifications.value.forEach((n) => {
      n.read = true
    })
  }

  function markRead(id: string) {
    const notification = notifications.value.find((n) => n.id === id)
    if (notification) notification.read = true
  }

  return { notifications: sorted, unread, unreadCount, markAllRead, markRead }
})
