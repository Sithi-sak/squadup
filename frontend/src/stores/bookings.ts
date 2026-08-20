import { ref } from 'vue'
import { defineStore } from 'pinia'
import { mockBookings } from '@/mocks/bookings'

export type BookingStatus = 'pending' | 'accepted' | 'declined' | 'completed'
export type PaymentMethod = 'coins' | 'card'

export interface BookingAddon {
  id: string
  label: string
  priceCoins: number
}

export interface Booking {
  id: string
  /** Human-facing order number shown on Checkout / Order Confirmation, e.g. "SQ-84213". */
  orderNumber: string
  playerId: string
  serviceId: string
  userId: string
  status: BookingStatus
  serviceTypeLabel: string
  /** Coin price per unit (per game/hour/session, matching `priceUnit`). */
  priceCoins: number
  priceUnit: string
  quantity: number
  addons: BookingAddon[]
  promoLabel: string | null
  subtotalCoins: number
  addonsCoins: number
  discountCoins: number
  totalCoins: number
  paymentMethod: PaymentMethod
  /** `null` means "start now"; otherwise an ISO timestamp for a scheduled start. */
  scheduledFor: string | null
  createdAt: string
}

export const useBookingsStore = defineStore('bookings', () => {
  const list = ref<Booking[]>([...mockBookings])
  const current = ref<Booking | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  function addBooking(booking: Booking) {
    list.value.unshift(booking)
    current.value = booking
  }

  function getBooking(id: string) {
    return list.value.find((b) => b.id === id) ?? null
  }

  function cancelBooking(id: string) {
    const booking = list.value.find((b) => b.id === id)
    if (booking) booking.status = 'declined'
  }

  return { list, current, loading, error, addBooking, getBooking, cancelBooking }
})
