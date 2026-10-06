import { shallowRef, watch } from 'vue'
import { useRoute, useRouter, type RouteLocationNormalizedLoaded } from 'vue-router'

/** The route a shell's nested `<router-view>` should render: the latest one that still belongs
 * to this shell. App.vue's `out-in` transition keeps the old page mounted while it fades, and a
 * kept-alive shell (FeedShellView) stays mounted after that, but the global route already points
 * at the next page. An unpinned nested `<router-view>` would then mount the next page's child a
 * second time inside the leaving shell - e.g. a ghost PlayerOrdersView whose `?booking=` modal
 * stacks on top of the real one. */
export function useShellRoute() {
  const router = useRouter()
  const shellRecord = useRoute().matched[0]
  const shellRoute = shallowRef<RouteLocationNormalizedLoaded>(router.currentRoute.value)

  watch(router.currentRoute, (to) => {
    if (to.matched[0] === shellRecord) shellRoute.value = to
  })

  return shellRoute
}
