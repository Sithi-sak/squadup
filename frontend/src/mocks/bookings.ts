import type { Booking } from '@/stores/bookings'
import { mockCurrentUser } from '@/mocks/users'

export const mockBookings: Booking[] = [
  {
    id: 'b1',
    playerId: 'p1',
    userId: mockCurrentUser.id,
    status: 'pending',
    startTime: '2026-08-18T13:00:00.000Z',
    durationMinutes: 60,
    totalPrice: 8,
  },
  {
    id: 'b2',
    playerId: 'p2',
    userId: mockCurrentUser.id,
    status: 'accepted',
    startTime: '2026-08-19T09:30:00.000Z',
    durationMinutes: 120,
    totalPrice: 12,
  },
  {
    id: 'b3',
    playerId: 'p3',
    userId: mockCurrentUser.id,
    status: 'completed',
    startTime: '2026-08-10T15:00:00.000Z',
    durationMinutes: 90,
    totalPrice: 6,
  },
  {
    id: 'b4',
    playerId: 'p6',
    userId: mockCurrentUser.id,
    status: 'declined',
    startTime: '2026-08-12T11:00:00.000Z',
    durationMinutes: 60,
    totalPrice: 10,
  },
  {
    id: 'b5',
    playerId: 'p4',
    userId: mockCurrentUser.id,
    status: 'completed',
    startTime: '2026-08-05T18:00:00.000Z',
    durationMinutes: 60,
    totalPrice: 5,
  },
]
