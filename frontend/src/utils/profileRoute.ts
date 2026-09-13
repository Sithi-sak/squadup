import type { RouteLocationRaw } from 'vue-router'

/**
 * Where clicking a user's avatar/name should go: their own posts jump to "Your profile", a
 * Pal's to their full `/players/{id}` page, everyone else to a plain public profile.
 */
export function profileRouteFor(
  userId: string | null | undefined,
  currentUserId: string | null | undefined,
  playerId?: string | null,
): RouteLocationRaw | null {
  if (!userId) return null
  if (userId === currentUserId) return { name: 'feed-profile' }
  if (playerId) return { name: 'player-profile', params: { id: playerId } }
  return { name: 'user-profile', params: { id: userId } }
}
