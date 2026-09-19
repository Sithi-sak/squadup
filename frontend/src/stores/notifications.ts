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
  /** Moderation warning sent from the admin Flagged Players panel (4.40). */
  | 'moderation'

/** Mirrors `NotificationOut` (`routers/notifications.py`). */
export interface AppNotification {
  id: string
  type: NotificationType
  message: string
  createdAt: string
  read: boolean
  /** Set on `type: 'message'` notifications so clicking one can open that conversation. */
  threadId?: string
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

  /** Chat is deliberately kept out of the bell: a new message alerts on the header's messages
   * button instead, and is retired by opening the conversation. Everything else goes to the
   * bell, so the two never double-report the same event. */
  const isChat = (n: AppNotification) => n.type === 'message'

  const alerts = computed(() => sorted.value.filter((n) => !isChat(n)))
  const unread = computed(() => alerts.value.filter((n) => !n.read))
  const unreadCount = computed(() => unread.value.length)

  const messageUnreadCount = computed(
    () => sorted.value.filter((n) => isChat(n) && !n.read).length,
  )

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
    await api.post('/notifications/read-all?exclude_type=message')
    notifications.value.forEach((n) => {
      if (!isChat(n)) n.read = true
    })
  }

  async function markRead(id: string) {
    const notification = notifications.value.find((n) => n.id === id)
    if (!notification) return
    await api.post(`/notifications/${id}/read`)
    notification.read = true
  }

  /** Header dropdown's per-row dismiss. Removes the row locally only once the delete lands, so a
   * failed request leaves the list as the server still has it. */
  async function dismiss(id: string) {
    await api.delete(`/notifications/${id}`)
    notifications.value = notifications.value.filter((n) => n.id !== id)
  }

  /** Header dropdown's "Clear" - drops every notification for the current user. */
  async function clearAll() {
    await api.delete('/notifications?exclude_type=message')
    notifications.value = notifications.value.filter(isChat)
  }

  /** Opening a conversation clears its chat alerts, which is the only way the messages badge
   * comes down (chat rows never appear in the bell for the user to read one by one). */
  async function markThreadRead(threadId: string) {
    const pending = notifications.value.filter(
      (n) => isChat(n) && n.threadId === threadId && !n.read,
    )
    if (pending.length === 0) return
    await api.post(`/notifications/threads/${threadId}/read`)
    pending.forEach((n) => {
      n.read = true
    })
  }

  return {
    /** Bell list - chat excluded, see `isChat`. */
    notifications: alerts,
    unread,
    unreadCount,
    messageUnreadCount,
    loading,
    error,
    fetchNotifications,
    markAllRead,
    markRead,
    markThreadRead,
    dismiss,
    clearAll,
  }
})
