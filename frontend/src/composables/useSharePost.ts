import { useToast } from '@nuxt/ui/composables/useToast'

/** Permalink for a post - `/feed/{id}` (`post-detail` in the router), which is public: a
 * logged-out visitor opening a shared link gets the post and its comments, since both
 * `GET /feed/posts/{id}` and its comments endpoint take an optional bearer token. */
export function postPermalink(postId: string) {
  return `${window.location.origin}/feed/${postId}`
}

export function useSharePost() {
  const toast = useToast()

  return async function copyPostLink(postId: string) {
    const url = postPermalink(postId)
    try {
      await navigator.clipboard.writeText(url)
      toast.add({ title: 'Link copied', description: 'Anyone with the link can view this post.', color: 'success' })
    } catch {
      toast.add({ title: 'Could not copy link', description: url, color: 'error' })
    }
  }
}
