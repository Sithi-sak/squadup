import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/lib/api'
import { mockBookings, mockIncomingBookings } from '@/mocks/bookings'

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
  /** Denormalized display fields the backend joins in (`GET /bookings/...`) so list/detail
   * views don't need a separate per-row player fetch. Absent on the static mock fixtures, which
   * views fall back to `mocks/players.ts` lookups for. */
  playerDisplayName?: string
  playerAvatarUrl?: string | null
  serviceId: string
  serviceName?: string
  userId: string
  buyerDisplayName?: string
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
  /** Whether a review already exists for this booking (`POST /reviews` is one-per-booking) -
   * gates My Bookings' "Leave review" action. Absent on the static mock fixtures, which fall
   * back to `false` (never reviewed). */
  hasReview?: boolean
}

export interface ReviewPayload {
  rating: number
  text: string
}

/** A "Book a session" selection that hasn't been submitted yet - kept client-side only until
 * Checkout's "Place order" posts it, so an abandoned checkout never creates a real `pending`
 * row (see CHECKPOINT.md's Booking flow note). */
export interface BookingDraft {
  playerId: string
  /** Carried along so Checkout/Order Confirmation can render the Pal's name/service title
   * without a `mocks/players.ts` lookup, which only knows the seed Pals (`p1`..`p8`), not real
   * ones fetched via `GET /players` (3.2). */
  playerDisplayName: string
  serviceId: string
  serviceName: string
  serviceTypeLabel: string
  priceCoins: number
  priceUnit: string
  quantity: number
  addons: BookingAddon[]
  promoLabel: string | null
  subtotalCoins: number
  addonsCoins: number
  discountCoins: number
  totalCoins: number
}

export interface CancelPayload {
  reason: string
  refundOption: 'full' | 'partial' | 'none'
  refundCoins: number
  note: string
}

export interface DisputePayload {
  reason: string
  outcome: 'full' | 'partial' | 'reporting'
  note: string
}

export const useBookingsStore = defineStore('bookings', () => {
  const draft = ref<BookingDraft | null>(null)
  const current = ref<Booking | null>(null)

  const list = ref<Booking[]>([])
  const listLoading = ref(false)
  const listError = ref<string | null>(null)

  const incoming = ref<Booking[]>([])
  const incomingLoading = ref(false)
  const incomingError = ref<string | null>(null)

  function startDraft(payload: BookingDraft) {
    draft.value = payload
  }

  function replaceInPlace(booking: Booking) {
    for (const arr of [list.value, incoming.value]) {
      const index = arr.findIndex((b) => b.id === booking.id)
      if (index !== -1) arr[index] = booking
    }
    if (current.value?.id === booking.id) current.value = booking
  }

  function getBooking(id: string) {
    return (
      list.value.find((b) => b.id === id) ??
      incoming.value.find((b) => b.id === id) ??
      (current.value?.id === id ? current.value : null)
    )
  }

  /** My Bookings (buyer side). Falls back to `mockBookings` if the request fails (signed out,
   * network error, backend down) rather than showing a broken page. */
  async function fetchList() {
    listLoading.value = true
    listError.value = null
    try {
      list.value = await api.get<Booking[]>('/bookings/mine')
    } catch (err) {
      listError.value = err instanceof Error ? err.message : 'Failed to load orders'
      list.value = [...mockBookings]
    } finally {
      listLoading.value = false
    }
  }

  /** Pal Dashboard / Orders (Pal side). Same fallback behavior as `fetchList`. */
  async function fetchIncoming() {
    incomingLoading.value = true
    incomingError.value = null
    try {
      incoming.value = await api.get<Booking[]>('/bookings/incoming')
    } catch (err) {
      incomingError.value = err instanceof Error ? err.message : 'Failed to load orders'
      incoming.value = [...mockIncomingBookings]
    } finally {
      incomingLoading.value = false
    }
  }

  /** Order Detail direct/deep-link fallback when the booking isn't already in `list`/`incoming`
   * (e.g. a page refresh before either list was fetched). */
  async function fetchBooking(id: string) {
    current.value = await api.get<Booking>(`/bookings/${id}`)
    return current.value
  }

  /** Checkout's "Place order" - the point where a draft actually becomes a submitted booking. */
  async function placeOrder(payload: { paymentMethod: PaymentMethod; scheduledFor: string | null }) {
    if (!draft.value) throw new Error('No booking draft to submit')
    const booking = await api.post<Booking>('/bookings', { ...draft.value, ...payload })
    list.value.unshift(booking)
    current.value = booking
    draft.value = null
    return booking
  }

  async function acceptBooking(id: string) {
    const booking = await api.post<Booking>(`/bookings/${id}/accept`)
    replaceInPlace(booking)
    return booking
  }

  async function declineBooking(id: string) {
    const booking = await api.post<Booking>(`/bookings/${id}/decline`)
    replaceInPlace(booking)
    return booking
  }

  async function completeBooking(id: string) {
    const booking = await api.post<Booking>(`/bookings/${id}/complete`)
    replaceInPlace(booking)
    return booking
  }

  async function cancelBooking(id: string, payload: CancelPayload) {
    const booking = await api.post<Booking>(`/bookings/${id}/cancel`, payload)
    replaceInPlace(booking)
    return booking
  }

  async function reportIssue(id: string, payload: DisputePayload) {
    await api.post(`/bookings/${id}/dispute`, payload)
  }

  /** My Bookings' `LeaveReviewModal` submit (`POST /reviews`). `highlights`/`tipCoins` the modal
   * collects stay UI-only for now - see `routers/reviews.py`'s docstring. Patches `hasReview`
   * onto the local booking rather than refetching, same as the other action methods. */
  async function submitReview(bookingId: string, payload: ReviewPayload) {
    await api.post(`/reviews`, { bookingId, ...payload })
    const booking = getBooking(bookingId)
    if (booking) replaceInPlace({ ...booking, hasReview: true })
  }

  return {
    draft,
    current,
    list,
    listLoading,
    listError,
    incoming,
    incomingLoading,
    incomingError,
    startDraft,
    getBooking,
    fetchList,
    fetchIncoming,
    fetchBooking,
    placeOrder,
    acceptBooking,
    declineBooking,
    completeBooking,
    cancelBooking,
    reportIssue,
    submitReview,
  }
})
