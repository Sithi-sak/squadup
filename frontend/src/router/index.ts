import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    /** Full-bleed pages (auth) render without the site header/footer chrome. */
    hideChrome?: boolean
    /** App-shell pages (dashboard, messages) keep the header but drop the marketing footer. */
    hideFooter?: boolean
    /** Redirects to `/login` when nobody's signed in (real Supabase session, not just chrome).
     * Browsing (players, profiles, feed, services) stays public; only account-bound pages are
     * gated. See CHECKPOINT.md 2.5. */
    requiresAuth?: boolean
    /** Which `FeedSidebar` nav item is lit for this page. Read by `FeedShellView`, the shared
     * parent route of every `/feed` page - the sidebar itself never remounts, so the active tab
     * has to come from the route rather than from a prop the child view passes up. */
    feedTab?: 'feed' | 'following' | 'explore' | 'saved' | 'profile'
    /** Shows the sidebar's "Create post" button - set on the feed pages that have no composer
     * of their own. */
    feedCreatePost?: boolean
    /** Redirects to `/home` when someone's already signed in — a live session can't land back
     * on the marketing/landing or auth pages (via link, browser back, or bookmark) until they
     * sign out. */
    guestOnly?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'landing',
      component: () => import('@/views/LandingView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { hideChrome: true, guestOnly: true },
    },
    {
      path: '/signup',
      name: 'signup',
      component: () => import('@/views/SignupView.vue'),
      meta: { hideChrome: true, guestOnly: true },
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('@/views/ForgotPasswordView.vue'),
      meta: { hideChrome: true },
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: () => import('@/views/ResetPasswordView.vue'),
      meta: { hideChrome: true },
    },
    {
      path: '/home',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/services',
      name: 'services',
      component: () => import('@/views/AllServicesView.vue'),
      meta: { hideFooter: true },
    },
    /** Every feed page is a child of one persistent shell (4.21): the sidebar and right rail
     * are mounted by `FeedShellView` and stay put, so navigating between these only swaps the
     * centre column. `/feed/:postId` below is deliberately *not* a child - the single-post page
     * is full-width, with no feed chrome. */
    {
      path: '/feed',
      component: () => import('@/views/FeedShellView.vue'),
      meta: { hideFooter: true },
      children: [
        {
          path: '',
          name: 'feed',
          component: () => import('@/views/FeedView.vue'),
          meta: { feedTab: 'feed' },
        },
        {
          path: 'following',
          name: 'feed-following',
          component: () => import('@/views/FeedFollowingView.vue'),
          meta: { feedTab: 'following', feedCreatePost: true },
        },
        {
          path: 'explore',
          name: 'feed-explore',
          component: () => import('@/views/FeedExploreView.vue'),
          meta: { feedTab: 'explore', feedCreatePost: true },
        },
        {
          path: 'saved',
          name: 'feed-saved',
          component: () => import('@/views/FeedSavedView.vue'),
          meta: { feedTab: 'saved', feedCreatePost: true },
        },
        {
          path: 'me',
          name: 'feed-profile',
          component: () => import('@/views/UserDashboardView.vue'),
          meta: { feedTab: 'profile', requiresAuth: true },
        },
        {
          path: 'u/:id',
          name: 'user-profile',
          component: () => import('@/views/PublicProfileView.vue'),
          meta: { feedTab: 'feed' },
        },
      ],
    },
    {
      path: '/profile/me',
      name: 'my-profile',
      component: () => import('@/views/MyProfileView.vue'),
      meta: { hideFooter: true, requiresAuth: true },
    },
    {
      path: '/feed/:postId',
      name: 'post-detail',
      component: () => import('@/views/PostDetailView.vue'),
      meta: { hideFooter: true },
    },
    {
      path: '/players',
      name: 'players',
      component: () => import('@/views/PlayersView.vue'),
      meta: { hideFooter: true },
    },
    {
      path: '/estars',
      name: 'estars-leaderboard',
      component: () => import('@/views/EstarsLeaderboardView.vue'),
      meta: { hideFooter: true },
    },
    {
      path: '/players/:id',
      name: 'player-profile',
      component: () => import('@/views/PlayerProfileView.vue'),
      meta: { hideFooter: true },
    },
    {
      path: '/players/:id/services/:serviceId',
      name: 'service-detail',
      component: () => import('@/views/ServiceDetailView.vue'),
      meta: { hideFooter: true },
    },
    {
      path: '/become-player',
      name: 'become-player',
      component: () => import('@/views/BecomePlayerView.vue'),
      meta: { hideChrome: true, requiresAuth: true },
    },
    {
      path: '/become-a-pal',
      name: 'become-a-pal',
      component: () => import('@/views/BecomeAPalView.vue'),
    },
    {
      path: '/faq',
      name: 'faq',
      component: () => import('@/views/FaqView.vue'),
    },
    {
      path: '/help',
      name: 'help-center',
      component: () => import('@/views/HelpCenterView.vue'),
    },
    {
      path: '/terms',
      name: 'terms-of-service',
      component: () => import('@/views/TermsOfServiceView.vue'),
    },
    {
      path: '/bookings',
      name: 'my-bookings',
      component: () => import('@/views/MyBookingsView.vue'),
      meta: { requiresAuth: true, hideFooter: true },
    },
    {
      path: '/bookings/:bookingId',
      name: 'order-detail',
      component: () => import('@/views/OrderDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/messages',
      name: 'messages',
      component: () => import('@/views/MessagesView.vue'),
      meta: { hideFooter: true, requiresAuth: true },
    },
    {
      path: '/dashboard/player',
      name: 'player-dashboard',
      component: () => import('@/views/PlayerDashboardView.vue'),
      meta: { hideFooter: true, requiresAuth: true },
    },
    {
      path: '/dashboard/player/orders',
      name: 'player-dashboard-orders',
      component: () => import('@/views/PlayerOrdersView.vue'),
      meta: { hideFooter: true, requiresAuth: true },
    },
    {
      path: '/dashboard/player/services',
      name: 'player-dashboard-services',
      component: () => import('@/views/PlayerServicesView.vue'),
      meta: { hideFooter: true, requiresAuth: true },
    },
    {
      path: '/dashboard/player/services/new',
      name: 'player-dashboard-create-service',
      component: () => import('@/views/CreateServiceView.vue'),
      meta: { hideFooter: true, requiresAuth: true },
    },
    {
      path: '/dashboard/player/earnings',
      name: 'player-dashboard-earnings',
      component: () => import('@/views/PlayerEarningsView.vue'),
      meta: { hideFooter: true, requiresAuth: true },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { hideFooter: true, requiresAuth: true },
    },
    {
      path: '/wallet',
      name: 'wallet',
      component: () => import('@/views/WalletView.vue'),
      meta: { hideFooter: true, requiresAuth: true },
    },
    {
      path: '/wallet/withdraw',
      name: 'wallet-withdraw',
      component: () => import('@/views/WithdrawView.vue'),
      meta: { hideFooter: true, requiresAuth: true },
    },
    {
      path: '/subscriptions',
      name: 'subscriptions',
      component: () => import('@/views/SubscriptionsView.vue'),
      meta: { hideFooter: true, requiresAuth: true },
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('@/views/NotificationsView.vue'),
      meta: { hideFooter: true, requiresAuth: true },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminView.vue'),
      meta: { hideChrome: true },
    },
    {
      path: '/checkout/:bookingId',
      name: 'checkout',
      component: () => import('@/views/CheckoutView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/checkout/:bookingId/confirmation',
      name: 'order-confirmation',
      component: () => import('@/views/OrderConfirmationView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
      meta: { hideFooter: true },
    },
  ],
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth && !to.meta.guestOnly) return true
  const auth = useAuthStore()
  await auth.init()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { path: '/home' }
  }
  return true
})

export default router
