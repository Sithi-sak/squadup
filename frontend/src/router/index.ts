import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'landing', component: () => import('@/views/LandingView.vue') },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    { path: '/signup', name: 'signup', component: () => import('@/views/SignupView.vue') },
    {
      path: '/onboarding',
      name: 'onboarding',
      component: () => import('@/views/OnboardingView.vue'),
    },
    { path: '/players', name: 'players', component: () => import('@/views/PlayersView.vue') },
    {
      path: '/players/:id',
      name: 'player-profile',
      component: () => import('@/views/PlayerProfileView.vue'),
    },
    {
      path: '/become-player',
      name: 'become-player',
      component: () => import('@/views/BecomePlayerView.vue'),
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
