import type { AuthUser } from '@/stores/auth'

/** The mock "logged in" user pages can build against before real auth exists. */
export const mockCurrentUser: AuthUser = {
  id: 'user-1',
  email: 'dara.chan@example.com',
  displayName: 'Dara Chan',
  handle: '@dara.chan',
  phone: null,
  country: null,
  role: 'user',
  playerId: 'self',
  onboardingComplete: true,
  coinBalance: 3240,
  postsCount: 0,
  followersCount: 0,
  followingCount: 0,
}
