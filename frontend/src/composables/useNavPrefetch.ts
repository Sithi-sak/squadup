import type { Router } from 'vue-router'
import { useFeedStore } from '@/stores/feed'
import { useEstarsStore } from '@/stores/estars'
import { usePlayersStore } from '@/stores/players'

/** How long a hover has to hold before it counts as intent to navigate, so a quick
 * mouse pass over a nav link doesn't fire a fetch nobody asked for. */
const HOVER_INTENT_DELAY_MS = 120

/** Nav links whose destination view fetches on mount/activate - prefetching their data
 * alongside the route's JS chunk means it's already in flight (or done) by the time the
 * view actually asks for it. Kept in sync with each view's own default fetch call so the
 * prefetch isn't wasted on mismatched params. Links with no store fetch (Games, Become a
 * Pal, Help) only get the chunk prefetch below. */
const dataPrefetchers: Record<string, () => void> = {
  '/home': () => {
    const playersStore = usePlayersStore()
    const estarsStore = useEstarsStore()
    if (!playersStore.list.length) playersStore.fetchList({ limit: 24 })
    if (!estarsStore.leaderboard.length) estarsStore.fetchLeaderboard('week')
    playersStore.fetchGameCounts()
  },
  '/feed': () => {
    useFeedStore().fetchFeed()
  },
  '/estars': () => {
    useEstarsStore().fetchLeaderboard('week')
  },
}

function prefetchChunk(router: Router, to: string) {
  for (const record of router.resolve(to).matched) {
    const component = record.components?.default
    if (typeof component === 'function') (component as () => unknown)()
  }
}

/** Hover/touch/focus-intent prefetching for the top nav's links. Re-invoking a lazy
 * route's `() => import(...)` loader is safe and free once Vite has cached that chunk's
 * promise, so there's nothing to dedup on the JS side - only the data fetches below need
 * a guard, which lives in each store's `loading` check. */
export function useNavPrefetch(router: Router) {
  let hoverTimer: ReturnType<typeof setTimeout> | undefined

  function prefetch(to: string) {
    prefetchChunk(router, to)
    dataPrefetchers[to]?.()
  }

  function onIntentEnter(to: string) {
    clearTimeout(hoverTimer)
    hoverTimer = setTimeout(() => prefetch(to), HOVER_INTENT_DELAY_MS)
  }

  function onIntentLeave() {
    clearTimeout(hoverTimer)
  }

  function onIntentNow(to: string) {
    clearTimeout(hoverTimer)
    prefetch(to)
  }

  return { onIntentEnter, onIntentLeave, onIntentNow }
}
