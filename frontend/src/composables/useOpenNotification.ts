import { useRouter } from 'vue-router'
import { useNotificationsStore, type AppNotification } from '@/stores/notifications'

/** Row click in the header dropdown and on `/notifications` (4.69c): marks it read and, for a
 * booking notification, opens the order. The Pal lands on their Orders page with that order's
 * modal open, the buyer on Order Detail. `bookingRole` comes from the backend, so this does no
 * network work before navigating, same as `usePalChat`. Returns whether it navigated, so the
 * dropdown knows to close. */
export function useOpenNotification() {
  const router = useRouter()
  const store = useNotificationsStore()

  return function openNotification(notification: AppNotification): boolean {
    if (!notification.read) {
      // Silent - a stray unread dot isn't worth a toast.
      store.markRead(notification.id).catch(() => {})
    }
    const { bookingId, bookingRole } = notification
    if (!bookingId || !bookingRole) return false
    if (bookingRole === 'pal') {
      router.push({ path: '/dashboard/player/orders', query: { booking: bookingId } })
    } else {
      router.push(`/bookings/${bookingId}`)
    }
    return true
  }
}
