import {
  PhCheck,
  PhChatCircle,
  PhStar,
  PhCurrencyCircleDollar,
  PhPlus,
  PhGameController,
  PhGift,
  PhFire,
  PhWarning,
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
  moderation: PhWarning,
}

/** Icon tint per type, so a wall of notifications is scannable by colour before it is read.
 * Money is green, conversation blue, social violet, and anything the user has to act on
 * (a moderation warning) amber. Full class strings - Tailwind only sees literals. */
export const notificationTone: Record<NotificationType, string> = {
  booking: 'bg-brand-500/15 text-brand-300',
  message: 'bg-sky-500/15 text-sky-300',
  review: 'bg-amber-500/15 text-amber-300',
  payout: 'bg-emerald-500/15 text-emerald-300',
  follow: 'bg-violet-500/15 text-violet-300',
  service: 'bg-indigo-500/15 text-indigo-300',
  gift: 'bg-pink-500/15 text-pink-300',
  streak: 'bg-orange-500/15 text-orange-300',
  moderation: 'bg-red-500/15 text-red-300',
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
