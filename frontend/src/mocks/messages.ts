import type { ChatMessage, MessageThread } from '@/stores/messages'
import { mockCurrentUser } from '@/mocks/users'

export const mockThreads: MessageThread[] = [
  {
    id: 't1',
    participantId: 'p1',
    participantDisplayName: 'ShadowStrike',
    lastMessagePreview: "Sure, I'm free at 8PM. What server are you on?",
    updatedAt: '2026-08-16T08:12:00.000Z',
    unreadCount: 2,
  },
  {
    id: 't2',
    participantId: 'p2',
    participantDisplayName: 'VelvetAce',
    lastMessagePreview: 'Booking accepted, see you then!',
    updatedAt: '2026-08-15T20:45:00.000Z',
    unreadCount: 0,
  },
  {
    id: 't3',
    participantId: 'p3',
    participantDisplayName: 'MythicRoamer',
    lastMessagePreview: 'GG! Thanks for the session 🙏',
    updatedAt: '2026-08-10T16:20:00.000Z',
    unreadCount: 1,
  },
]

export const mockMessagesByThread: Record<string, ChatMessage[]> = {
  t1: [
    {
      id: 'm1',
      threadId: 't1',
      senderId: mockCurrentUser.id,
      body: 'Hey! Are you free to duo tonight?',
      createdAt: '2026-08-16T08:05:00.000Z',
    },
    {
      id: 'm2',
      threadId: 't1',
      senderId: 'p1',
      body: "Sure, I'm free at 8PM. What server are you on?",
      createdAt: '2026-08-16T08:12:00.000Z',
    },
  ],
  t2: [
    {
      id: 'm3',
      threadId: 't2',
      senderId: mockCurrentUser.id,
      body: 'Just sent a booking request for tomorrow morning.',
      createdAt: '2026-08-15T20:40:00.000Z',
    },
    {
      id: 'm4',
      threadId: 't2',
      senderId: 'p2',
      body: 'Booking accepted, see you then!',
      createdAt: '2026-08-15T20:45:00.000Z',
    },
  ],
  t3: [
    {
      id: 'm5',
      threadId: 't3',
      senderId: 'p3',
      body: 'GG! Thanks for the session 🙏',
      createdAt: '2026-08-10T16:20:00.000Z',
    },
  ],
}
