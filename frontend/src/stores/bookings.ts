import { ref } from 'vue'
import { defineStore } from 'pinia'

export type BookingStatus = 'pending' | 'accepted' | 'declined' | 'completed'

export interface Booking {
  id: string
  playerId: string
  userId: string
  status: BookingStatus
  startTime: string
  durationMinutes: number
  totalPrice: number
}

export const useBookingsStore = defineStore('bookings', () => {
  const list = ref<Booking[]>([])
  const current = ref<Booking | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  return { list, current, loading, error }
})
