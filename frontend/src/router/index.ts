import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    /** Full-bleed pages (auth) render without the site header/footer chrome. */
    hideChrome?: boolean
    /** Post-login pages get the signed-in header (search, wallet, avatar menu) instead of the public one. */
    authenticated?: boolean
    /** App-shell pages (dashboard, messages) keep the header but drop the marketing footer. */
    hideFooter?: boolean
    /** Redirects to `/login` when nobody's signed in (real Supabase session, not just chrome).
     * Browsing (players, profiles, feed, services) stays public; only account-bound pages are
     * gated. See CHECKPOINT.md 2.5. */
    requiresAuth?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'landing', component: () => import('@/views/LandingView.vue') },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { hideChrome: true },
    },
    {
      path: '/signup',
      name: 'signup',
      component: () => import('@/views/SignupView.vue'),
      meta: { hideChrome: true },
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
      meta: { authenticated: true, requiresAuth: true },
    },
    {
      path: '/services',
      name: 'services',
      component: () => import('@/views/AllServicesView.vue'),
      meta: { authenticated: true },
    },
    {
      path: '/feed',
      name: 'feed',
      component: () => import('@/views/FeedView.vue'),
      meta: { authenticated: true },
    },
    {
      path: '/feed/following',
      name: 'feed-following',
      component: () => import('@/views/FeedFollowingView.vue'),
      meta: { authenticated: true },
    },
    {
      path: '/feed/explore',
      name: 'feed-explore',
      component: () => import('@/views/FeedExploreView.vue'),
      meta: { authenticated: true },
    },
    {
      path: '/feed/saved',
      name: 'feed-saved',
      component: () => import('@/views/FeedSavedView.vue'),
      meta: { authenticated: true },
    },
    {
      path: '/feed/:postId',
      name: 'post-detail',
      component: () => import('@/views/PostDetailView.vue'),
      meta: { authenticated: true },
    },
    {
      path: '/players',
      name: 'players',
      component: () => import('@/views/PlayersView.vue'),
      meta: { authenticated: true },
    },
    {
      path: '/estars',
      name: 'estars-leaderboard',
      component: () => import('@/views/EstarsLeaderboardView.vue'),
      meta: { authenticated: true, hideFooter: true },
    },
    {
      path: '/players/:id',
      name: 'player-profile',
      component: () => import('@/views/PlayerProfileView.vue'),
      meta: { authenticated: true },
    },
    {
      path: '/players/:id/services/:serviceId',
      name: 'service-detail',
      component: () => import('@/views/ServiceDetailView.vue'),
      meta: { authenticated: true },
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
      meta: { authenticated: true, requiresAuth: true },
    },
    {
      path: '/bookings/:bookingId',
      name: 'order-detail',
      component: () => import('@/views/OrderDetailView.vue'),
      meta: { authenticated: true, requiresAuth: true },
    },
    {
      path: '/messages',
      name: 'messages',
      component: () => import('@/views/MessagesView.vue'),
      meta: { authenticated: true, hideFooter: true, requiresAuth: true },
    },
    {
      path: '/dashboard/player',
      name: 'player-dashboard',
      component: () => import('@/views/PlayerDashboardView.vue'),
      meta: { authenticated: true, hideFooter: true, requiresAuth: true },
    },
    {
      path: '/dashboard/player/orders',
      name: 'player-dashboard-orders',
      component: () => import('@/views/PlayerOrdersView.vue'),
      meta: { authenticated: true, hideFooter: true, requiresAuth: true },
    },
    {
      path: '/dashboard/player/services',
      name: 'player-dashboard-services',
      component: () => import('@/views/PlayerServicesView.vue'),
      meta: { authenticated: true, hideFooter: true, requiresAuth: true },
    },
    {
      path: '/dashboard/player/services/new',
      name: 'player-dashboard-create-service',
      component: () => import('@/views/CreateServiceView.vue'),
      meta: { authenticated: true, hideFooter: true, requiresAuth: true },
    },
    {
      path: '/dashboard/player/earnings',
      name: 'player-dashboard-earnings',
      component: () => import('@/views/PlayerEarningsView.vue'),
      meta: { authenticated: true, hideFooter: true, requiresAuth: true },
    },
    {
      path: '/dashboard/user',
      name: 'user-dashboard',
      component: () => import('@/views/UserDashboardView.vue'),
      meta: { authenticated: true, hideFooter: true, requiresAuth: true },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { authenticated: true, hideFooter: true, requiresAuth: true },
    },
    {
      path: '/wallet',
      name: 'wallet',
      component: () => import('@/views/WalletView.vue'),
      meta: { authenticated: true, hideFooter: true, requiresAuth: true },
    },
    {
      path: '/wallet/withdraw',
      name: 'wallet-withdraw',
      component: () => import('@/views/WithdrawView.vue'),
      meta: { authenticated: true, hideFooter: true, requiresAuth: true },
    },
    {
      path: '/subscriptions',
      name: 'subscriptions',
      component: () => import('@/views/SubscriptionsView.vue'),
      meta: { authenticated: true, hideFooter: true, requiresAuth: true },
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('@/views/NotificationsView.vue'),
      meta: { authenticated: true, hideFooter: true, requiresAuth: true },
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
      meta: { authenticated: true, hideFooter: true },
    },
  ],
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true
  const auth = useAuthStore()
  await auth.init()
  if (auth.isAuthenticated) return true
  return { path: '/login', query: { redirect: to.fullPath } }
})

export default router
