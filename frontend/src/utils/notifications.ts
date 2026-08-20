import {
  PhCheck,
  PhChatCircle,
  PhStar,
  PhCurrencyCircleDollar,
  PhPlus,
  PhGameController,
  PhGift,
  PhFire,
} from '@phosphor-icons/vue'
import type { NotificationType } from '@/stores/notifications'

export const notificationIcon: Record<NotificationType, typeof PhCheck> = {
  booking: PhCheck,
  message: PhChatCircle,
  review: PhStar,
  payout: PhCurrencyCircleDollar,
  follow: PhPlus,
  service: PhGameController,
  gift: PhGift,
  streak: PhFire,
}

/** Matches the design's "2m ago" / "1h ago" short form, falling back to "Yesterday" and
 * "N days ago" for older items (`squadup_ui/NOTIFICATION PANEL.jpg`, `squadup_ui/s2/NOTIFICATIONS.jpg`). */
export function formatNotificationTime(iso: string) {
  const minutes = Math.floor((Date.now() - new Date(iso).getTime()) / 60_000)
  if (minutes < 1) return 'now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'Yesterday'
  return `${days} days ago`
}

export function isNotificationToday(iso: string) {
  return Date.now() - new Date(iso).getTime() < 24 * 60 * 60_000
}
