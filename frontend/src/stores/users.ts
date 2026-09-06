import { defineStore } from 'pinia'
import { api } from '@/lib/api'

/** `GET /users/{id}/profile` response shape (backend's `PublicProfileOut`) - any signed-in or
 * anonymous viewer can look up any account this way, unlike `/users/me`. */
export interface PublicProfile {
  id: string
  displayName: string | null
  handle: string | null
  avatarUrl: string | null
  online: boolean
  /** Non-null only when this account has also become a Pal - callers route to
   * `/players/{playerId}` instead of the plain profile page when this is set. */
  playerId: string | null
  tier: string | null
  postsCount: number
  followersCount: number
  followingCount: number
  following: boolean
}

export const useUsersStore = defineStore('users', () => {
  function fetchPublicProfile(userId: string) {
    return api.get<PublicProfile>(`/users/${encodeURIComponent(userId)}/profile`)
  }

  return { fetchPublicProfile }
})
