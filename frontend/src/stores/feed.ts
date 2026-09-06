import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/lib/api'
import type { FeedComment as MockFeedComment, FeedPost as MockFeedPost, SavedItem as MockSavedItem } from '@/mocks/feed'
import { mockFeedPosts, mockFollowingPosts, mockPostComments, mockSavedItems } from '@/mocks/feed'

export interface FeedPost {
  id: string
  authorId: string
  author: string
  handle: string | null
  tier: string | null
  avatarUrl: string | null
  online: boolean
  text: string | null
  hasImage: boolean
  category: string
  likes: number
  comments: number
  liked: boolean
  following: boolean
  createdAt: string
}

export interface FeedComment {
  id: string
  postId: string
  authorId: string
  author: string
  parentCommentId: string | null
  text: string
  likes: number
  liked: boolean
  isCreator: boolean
  createdAt: string
  replies: FeedComment[]
}

/** Mirrors `SavedItemOut` (`routers/feed.py`) - a flat shape carrying both post and service
 * fields, only the ones matching `kind` are populated. */
export interface FeedSavedItem {
  id: string
  kind: 'post' | 'service'
  createdAt: string
  postId?: string | null
  author?: string | null
  handle?: string | null
  tier?: string | null
  text?: string | null
  hasImage?: boolean | null
  likes?: number | null
  comments?: number | null
  serviceId?: string | null
  name?: string | null
  by?: string | null
  category?: string | null
  priceCoins?: number | null
  priceUnit?: string | null
  promoLabel?: string | null
}

export interface CreatePostPayload {
  text?: string
  imageUrl?: string
  category?: string
}

/** Fallback fixtures (`mocks/feed.ts`) predate this store and don't carry `authorId`/`liked`/
 * `createdAt` (the mocks use a display-only `timeAgo` string) - these fill in reasonable
 * stand-ins rather than reshaping the mock file itself, same "adapt at the boundary" approach
 * `stores/players.ts`'s `playerProfileFromDetail` uses in the other direction. */
function feedPostFromMock(post: MockFeedPost): FeedPost {
  return {
    id: post.id,
    authorId: post.id,
    author: post.author,
    handle: post.handle,
    tier: post.tier,
    avatarUrl: null,
    online: post.online,
    text: post.text,
    hasImage: post.hasImage,
    category: post.category,
    likes: post.likes,
    comments: post.comments,
    liked: false,
    following: post.following,
    createdAt: new Date().toISOString(),
  }
}

function feedCommentFromMock(postId: string, comment: MockFeedComment): FeedComment {
  return {
    id: comment.id,
    postId,
    authorId: comment.id,
    author: comment.author,
    parentCommentId: null,
    text: comment.text,
    likes: comment.likes,
    liked: false,
    isCreator: comment.isCreator ?? false,
    createdAt: new Date().toISOString(),
    replies: (comment.replies ?? []).map((reply) => feedCommentFromMock(postId, reply)),
  }
}

function savedItemFromMock(item: MockSavedItem): FeedSavedItem {
  if (item.kind === 'post') {
    return {
      id: item.id,
      kind: 'post',
      createdAt: new Date().toISOString(),
      postId: item.id,
      author: item.author,
      handle: item.handle,
      tier: item.tier,
      text: item.text,
      hasImage: item.hasImage,
      likes: item.likes,
      comments: item.comments,
    }
  }
  return {
    id: item.id,
    kind: 'service',
    createdAt: new Date().toISOString(),
    serviceId: item.id,
    name: item.name,
    by: item.by,
    category: item.category,
    priceCoins: item.priceCoins,
    priceUnit: item.priceUnit,
    promoLabel: item.promoLabel,
  }
}

export const useFeedStore = defineStore('feed', () => {
  const posts = ref<FeedPost[]>([])
  const postsLoading = ref(false)
  const postsError = ref<string | null>(null)

  const following = ref<FeedPost[]>([])
  const followingLoading = ref(false)
  const followingError = ref<string | null>(null)

  const saved = ref<FeedSavedItem[]>([])
  const savedLoading = ref(false)
  const savedError = ref<string | null>(null)

  const current = ref<FeedPost | null>(null)

  const commentsByPost = ref<Record<string, FeedComment[]>>({})
  const commentsLoading = ref(false)
  const commentsError = ref<string | null>(null)

  function patchPost(updated: FeedPost) {
    for (const list of [posts.value, following.value]) {
      const index = list.findIndex((p) => p.id === updated.id)
      if (index !== -1) list[index] = updated
    }
    if (current.value?.id === updated.id) current.value = updated
  }

  function applyFollow(authorId: string, isFollowing: boolean) {
    for (const list of [posts.value, following.value]) {
      for (const post of list) {
        if (post.authorId === authorId) post.following = isFollowing
      }
    }
    if (current.value?.authorId === authorId) current.value.following = isFollowing
  }

  function bumpCommentCount(postId: string, delta: number) {
    for (const list of [posts.value, following.value]) {
      const post = list.find((p) => p.id === postId)
      if (post) post.comments += delta
    }
    if (current.value?.id === postId) current.value.comments += delta
  }

  function findCommentTree(postId: string, commentId: string): FeedComment | undefined {
    function search(comments: FeedComment[]): FeedComment | undefined {
      for (const comment of comments) {
        if (comment.id === commentId) return comment
        const found = search(comment.replies)
        if (found) return found
      }
      return undefined
    }
    return search(commentsByPost.value[postId] ?? [])
  }

  /** Feed (`/feed`). Falls back to `mockFeedPosts` if the request fails (signed out, network
   * error, backend down), same resilience convention as 3.1j/3.2d/3.4c/3.5d. */
  async function fetchFeed() {
    postsLoading.value = true
    postsError.value = null
    try {
      posts.value = await api.get<FeedPost[]>('/feed')
    } catch (err) {
      postsError.value = err instanceof Error ? err.message : 'Failed to load feed'
      posts.value = mockFeedPosts.map(feedPostFromMock)
    } finally {
      postsLoading.value = false
    }
  }

  /** Following (`/feed/following`). Same fallback behavior as `fetchFeed`. */
  async function fetchFollowing() {
    followingLoading.value = true
    followingError.value = null
    try {
      following.value = await api.get<FeedPost[]>('/feed/following')
    } catch (err) {
      followingError.value = err instanceof Error ? err.message : 'Failed to load following feed'
      following.value = mockFollowingPosts.map(feedPostFromMock)
    } finally {
      followingLoading.value = false
    }
  }

  /** Post Detail's direct/deep-link fetch, mirroring `bookingsStore.fetchBooking`. */
  async function fetchPost(id: string) {
    current.value = await api.get<FeedPost>(`/feed/posts/${id}`)
    return current.value
  }

  /** Prefers an already-loaded post (from `fetchFeed`/`fetchFollowing`) over a network round-trip,
   * mirroring `bookingsStore.getBooking`. */
  function getPost(id: string): FeedPost | undefined {
    return posts.value.find((p) => p.id === id) ?? following.value.find((p) => p.id === id)
  }

  /** Feed composer (`CreatePostModal.vue`). */
  async function createPost(payload: CreatePostPayload) {
    const post = await api.post<FeedPost>('/feed/posts', payload)
    posts.value.unshift(post)
    return post
  }

  async function toggleLike(post: FeedPost) {
    const updated = post.liked
      ? await api.delete<FeedPost>(`/feed/posts/${post.id}/like`)
      : await api.post<FeedPost>(`/feed/posts/${post.id}/like`)
    patchPost(updated)
    return updated
  }

  async function toggleFollow(authorId: string, currentlyFollowing: boolean) {
    const result = currentlyFollowing
      ? await api.delete<{ followedId: string; following: boolean; followersCount: number }>(
          `/feed/follows/${authorId}`,
        )
      : await api.post<{ followedId: string; following: boolean; followersCount: number }>(
          `/feed/follows/${authorId}`,
        )
    applyFollow(authorId, result.following)
    return result
  }

  /** Post Detail / a post's comment thread. Falls back to `mockPostComments`. */
  async function fetchComments(postId: string) {
    commentsLoading.value = true
    commentsError.value = null
    try {
      commentsByPost.value[postId] = await api.get<FeedComment[]>(`/feed/posts/${postId}/comments`)
    } catch (err) {
      commentsError.value = err instanceof Error ? err.message : 'Failed to load comments'
      commentsByPost.value[postId] = (mockPostComments[postId] ?? []).map((c) => feedCommentFromMock(postId, c))
    } finally {
      commentsLoading.value = false
    }
  }

  async function postComment(postId: string, text: string, parentCommentId?: string | null) {
    const comment = await api.post<FeedComment>(`/feed/posts/${postId}/comments`, {
      text,
      parentCommentId: parentCommentId ?? null,
    })
    const list = (commentsByPost.value[postId] ??= [])
    if (parentCommentId) {
      const parent = findCommentTree(postId, parentCommentId)
      if (parent) parent.replies.push(comment)
      else list.push(comment)
    } else {
      list.push(comment)
    }
    bumpCommentCount(postId, 1)
    return comment
  }

  /** Comment like/unlike - not in 3.8d's literal action list but the backend already exposes it
   * (3.8a's `POST/DELETE /feed/comments/{id}/like`) and `FeedCommentItem.vue` already has a like
   * button, so it's wired here alongside `toggleLike` for the same reason. */
  async function toggleCommentLike(postId: string, comment: FeedComment) {
    const updated = comment.liked
      ? await api.delete<FeedComment>(`/feed/comments/${comment.id}/like`)
      : await api.post<FeedComment>(`/feed/comments/${comment.id}/like`)
    const list = commentsByPost.value[postId]
    if (list) {
      const top = list.find((c) => c.id === updated.id)
      if (top) Object.assign(top, updated, { replies: top.replies })
      else {
        const existing = findCommentTree(postId, updated.id)
        if (existing) Object.assign(existing, updated, { replies: existing.replies })
      }
    }
    return updated
  }

  /** Saved (`/feed/saved`). Requires a bearer token - falls back to `mockSavedItems`. */
  async function fetchSaved() {
    savedLoading.value = true
    savedError.value = null
    try {
      saved.value = await api.get<FeedSavedItem[]>('/feed/saved')
    } catch (err) {
      savedError.value = err instanceof Error ? err.message : 'Failed to load saved items'
      saved.value = mockSavedItems.map(savedItemFromMock)
    } finally {
      savedLoading.value = false
    }
  }

  function findSaved(kind: 'post' | 'service', id: string) {
    return saved.value.find((item) =>
      kind === 'post' ? item.kind === 'post' && item.postId === id : item.kind === 'service' && item.serviceId === id,
    )
  }

  /** Toggles a post or service's saved state (`FeedPostCard`'s bookmark action, `FeedSavedView`'s
   * "Unsave" button, and Service Detail's save-to-Wish-style bookmark). Finds the existing saved
   * row first since the backend keys deletes on the `saved_items` row id, not the post/service id. */
  async function toggleSaved(kind: 'post' | 'service', id: string) {
    const existing = findSaved(kind, id)
    if (existing) {
      await api.delete(`/feed/saved/${existing.id}`)
      saved.value = saved.value.filter((item) => item.id !== existing.id)
      return null
    }
    const created = await api.post<FeedSavedItem>('/feed/saved', {
      kind,
      postId: kind === 'post' ? id : undefined,
      serviceId: kind === 'service' ? id : undefined,
    })
    saved.value.unshift(created)
    return created
  }

  return {
    posts,
    postsLoading,
    postsError,
    following,
    followingLoading,
    followingError,
    saved,
    savedLoading,
    savedError,
    current,
    commentsByPost,
    commentsLoading,
    commentsError,
    fetchFeed,
    fetchFollowing,
    fetchPost,
    getPost,
    createPost,
    toggleLike,
    toggleFollow,
    fetchComments,
    postComment,
    toggleCommentLike,
    fetchSaved,
    toggleSaved,
    findSaved,
  }
})
