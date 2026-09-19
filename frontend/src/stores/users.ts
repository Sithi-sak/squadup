import { ref } from 'vue'
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
  /** True when the viewer is the one who blocked this account, so the profile menu can offer
   * Unblock. The other direction 403s the read instead (4.39). */
  blocked: boolean
}

/** `GET /users/me/blocks` row - the accounts the signed-in user has blocked. */
export interface BlockedUser {
  id: string
  displayName: string | null
  handle: string | null
  avatarUrl: string | null
  blockedAt: string
}

export const useUsersStore = defineStore('users', () => {
  function fetchPublicProfile(userId: string) {
    return api.get<PublicProfile>(`/users/${encodeURIComponent(userId)}/profile`)
  }

  /** Handed off from the `user-profile` route guard (`router/index.ts`) to `PublicProfileView`:
   * the guard already fetches the profile to decide whether to redirect a Pal straight to
   * `/players/{id}` before the Feed shell ever paints, so the view reuses that result instead of
   * fetching it again. Consumed once via `takePrefetchedProfile`, then cleared. */
  const prefetchedProfile = ref<{ userId: string; profile: PublicProfile } | null>(null)

  function takePrefetchedProfile(userId: string): PublicProfile | null {
    if (prefetchedProfile.value?.userId !== userId) return null
    const profile = prefetchedProfile.value.profile
    prefetchedProfile.value = null
    return profile
  }

  /** Blocking (4.39) stops messaging and booking both ways, hides each side's posts from the
   * other's feed, and makes this account's profile unreadable to the person blocked. Only the
   * blocker can lift it, which is why the profile they blocked stays readable to them. */
  function blockUser(userId: string) {
    return api.post<{ blocked: boolean }>(`/users/blocks/${encodeURIComponent(userId)}`)
  }

  function unblockUser(userId: string) {
    return api.delete<{ blocked: boolean }>(`/users/blocks/${encodeURIComponent(userId)}`)
  }

  function fetchMyBlocks() {
    return api.get<BlockedUser[]>('/users/me/blocks')
  }

  return {
    fetchPublicProfile,
    prefetchedProfile,
    takePrefetchedProfile,
    blockUser,
    unblockUser,
    fetchMyBlocks,
  }
})
