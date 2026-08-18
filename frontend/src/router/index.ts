import { createRouter, createWebHistory } from 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    /** Full-bleed pages (auth) render without the site header/footer chrome. */
    hideChrome?: boolean
    /** Post-login pages get the signed-in header (search, wallet, avatar menu) instead of the public one. */
    authenticated?: boolean
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
      meta: { authenticated: true },
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
      path: '/players',
      name: 'players',
      component: () => import('@/views/PlayersView.vue'),
      meta: { authenticated: true },
    },
    {
      path: '/players/:id',
      name: 'player-profile',
      component: () => import('@/views/PlayerProfileView.vue'),
      meta: { authenticated: true },
    },
    {
      path: '/become-player',
      name: 'become-player',
      component: () => import('@/views/BecomePlayerView.vue'),
      meta: { hideChrome: true },
    },
    {
      path: '/book/:playerId',
      name: 'booking',
      component: () => import('@/views/BookingView.vue'),
    },
    {
      path: '/bookings',
      name: 'my-bookings',
      component: () => import('@/views/MyBookingsView.vue'),
    },
    { path: '/messages', name: 'messages', component: () => import('@/views/MessagesView.vue') },
    {
      path: '/dashboard/player',
      name: 'player-dashboard',
      component: () => import('@/views/PlayerDashboardView.vue'),
    },
    {
      path: '/dashboard/user',
      name: 'user-dashboard',
      component: () => import('@/views/UserDashboardView.vue'),
    },
    { path: '/settings', name: 'settings', component: () => import('@/views/SettingsView.vue') },
    { path: '/admin', name: 'admin', component: () => import('@/views/AdminView.vue') },
    {
      path: '/checkout/:bookingId',
      name: 'checkout',
      component: () => import('@/views/CheckoutView.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

export default router
