import type { AppNotification } from '@/stores/notifications'

const minutes = (n: number) => n * 60_000
const hours = (n: number) => n * 60 * minutes(1)
const days = (n: number) => n * 24 * hours(1)
const ago = (ms: number) => new Date(Date.now() - ms).toISOString()

export const mockNotifications: AppNotification[] = [
  {
    id: 'n1',
    type: 'booking',
    message: 'Oomfie accepted your booking for Valorant duo. Session at 9:00 PM.',
    createdAt: ago(minutes(2)),
    read: false,
  },
  {
    id: 'n2',
    type: 'message',
    message: 'mochi sent you a message: "ty for the feeding sesh!"',
    createdAt: ago(minutes(12)),
    read: false,
  },
  {
    id: 'n3',
    type: 'review',
    message: 'KaiRuu left you a 5-star review on Valorant duo.',
    createdAt: ago(hours(1)),
    read: true,
  },
  {
    id: 'n4',
    type: 'payout',
    message: 'Payout of 2,916 SC completed to your Squad Coin wallet.',
    createdAt: ago(hours(3)),
    read: true,
  },
  {
    id: 'n5',
    type: 'follow',
    message: 'ZeroTwo started following you.',
    createdAt: ago(days(1)),
    read: true,
  },
  {
    id: 'n6',
    type: 'gift',
    message: 'lunaaa sent you a gift: Crown 👑',
    createdAt: ago(days(1) + hours(2)),
    read: true,
  },
  {
    id: 'n7',
    type: 'service',
    message: 'Your service "Valorant duo" was approved and is now live.',
    createdAt: ago(days(2)),
    read: true,
  },
  {
    id: 'n8',
    type: 'streak',
    message: "You're on a streak! 5 sessions completed this week. Keep it going.",
    createdAt: ago(days(3)),
    read: true,
  },
]
