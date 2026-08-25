import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/lib/api'
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

/** Mirrors `NotificationOut` (`routers/notifications.py`). */
export interface AppNotification {
  id: string
  type: NotificationType
  message: string
  createdAt: string
  read: boolean
}

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref<AppNotification[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const sorted = computed(() =>
    [...notifications.value].sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    ),
  )
  const unread = computed(() => sorted.value.filter((n) => !n.read))
  const unreadCount = computed(() => unread.value.length)

  /** Header bell / `/notifications` page (`GET /notifications`). Falls back to
   * `mockNotifications`, same resilience convention as `stores/players.ts`/`bookings.ts`/etc. */
  async function fetchNotifications() {
    loading.value = true
    error.value = null
    try {
      notifications.value = await api.get<AppNotification[]>('/notifications')
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load notifications'
      notifications.value = [...mockNotifications]
    } finally {
      loading.value = false
    }
  }

  /** Real mutations only, no mock fallback - matches `feedStore.toggleLike`'s convention. */
  async function markAllRead() {
    await api.post('/notifications/read-all')
    notifications.value.forEach((n) => {
      n.read = true
    })
  }

  async function markRead(id: string) {
    const notification = notifications.value.find((n) => n.id === id)
    if (!notification) return
    await api.post(`/notifications/${id}/read`)
    notification.read = true
  }

  return {
    notifications: sorted,
    unread,
    unreadCount,
    loading,
    error,
    fetchNotifications,
    markAllRead,
    markRead,
  }
})
