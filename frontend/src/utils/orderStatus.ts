import type { Booking } from '@/stores/bookings'

export type OrderDisplayStatusKey = 'pending' | 'in-progress' | 'scheduled' | 'completed' | 'cancelled'

export interface OrderDisplayStatus {
  key: OrderDisplayStatusKey
  label: string
  class: string
}

/** Shared Pending/In progress/Scheduled/Completed/Cancelled status label used across the Pal
 * Dashboard's incoming orders widget and full Orders page (`squadup_ui/DASHBOARD.jpg` and
 * `squadup_ui/DASHBOARD/ORDERS.jpg`). "Scheduled" isn't its own `BookingStatus` value, it's an
 * `accepted` booking whose `scheduledFor` is still in the future. */
export function orderStatusMeta(booking: Pick<Booking, 'status' | 'scheduledFor'>): OrderDisplayStatus {
  if (booking.status === 'pending') return { key: 'pending', label: 'Pending', class: 'text-amber-400' }
  if (booking.status === 'completed') return { key: 'completed', label: 'Completed', class: 'text-brand-400' }
  if (booking.status === 'declined') return { key: 'cancelled', label: 'Cancelled', class: 'text-red-400' }
  if (booking.scheduledFor && new Date(booking.scheduledFor).getTime() > Date.now()) {
    return { key: 'scheduled', label: 'Scheduled', class: 'text-sky-400' }
  }
  return { key: 'in-progress', label: 'In progress', class: 'text-brand-400' }
}
