import type { AuthUser } from '@/stores/auth'

/** The mock "logged in" user pages can build against before real auth exists. */
export const mockCurrentUser: AuthUser = {
  id: 'user-1',
  email: 'dara.chan@example.com',
  displayName: 'Dara Chan',
  role: 'user',
  onboardingComplete: true,
  coinBalance: 3240,
}
