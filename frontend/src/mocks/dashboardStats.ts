/** Aggregate Pal Dashboard numbers that aren't naturally derivable from a handful of seed
 * bookings (lifetime totals, response rate, payout history). Built for 1.12 per
 * `squadup_ui/DASHBOARD.jpg` and `squadup_ui/DASHBOARD/EARNINGS.jpg`. */
export interface PalDashboardStats {
  coinsThisMonthChangePct: number
  usdEquivalentThisMonth: number
  ordersCompleted: number
  ordersCompletedThisWeek: number
  avgRating: number
  reviewCount: number
  responseRatePct: number
  avgResponseTime: string
  earningsThisWeek: { day: string; coins: number }[]
  pendingClearanceCoins: number
  pendingClearanceDays: number
  lifetimeEarnedCoins: number
  lifetimeEarnedChangePct: number
  payoutMethod: { label: string; handle: string }
  nextPayoutDate: string
  payoutSchedule: string
  payoutHistory: { date: string; label: string; coins: number; status: 'paid' | 'processing' }[]
  earningsOverview: { month: string; coins: number }[]
}

export const mockPalDashboardStats: PalDashboardStats = {
  coinsThisMonthChangePct: 18,
  usdEquivalentThisMonth: 32.4,
  ordersCompleted: 48,
  ordersCompletedThisWeek: 6,
  avgRating: 4.9,
  reviewCount: 312,
  responseRatePct: 98,
  avgResponseTime: '5-10 mins',
  earningsThisWeek: [
    { day: 'M', coins: 320 },
    { day: 'T', coins: 480 },
    { day: 'W', coins: 260 },
    { day: 'T', coins: 610 },
    { day: 'F', coins: 540 },
    { day: 'S', coins: 890 },
    { day: 'S', coins: 410 },
  ],
  pendingClearanceCoins: 480,
  pendingClearanceDays: 2,
  lifetimeEarnedCoins: 18920,
  lifetimeEarnedChangePct: 18,
  payoutMethod: { label: 'Squad Coin Wallet', handle: '@1525835767' },
  nextPayoutDate: '2026-08-24',
  payoutSchedule: 'Weekly',
  payoutHistory: [
    { date: '2026-08-17', label: 'Squad Coin · Weekly payout', coins: 1240, status: 'processing' },
    { date: '2026-08-10', label: 'Squad Coin · Weekly payout', coins: 980, status: 'paid' },
    { date: '2026-08-03', label: 'Squad Coin · Weekly payout', coins: 1520, status: 'paid' },
    { date: '2026-07-27', label: 'Squad Coin · Weekly payout', coins: 760, status: 'paid' },
  ],
  earningsOverview: [
    { month: 'Jan', coins: 980 },
    { month: 'Feb', coins: 1120 },
    { month: 'Mar', coins: 1480 },
    { month: 'Apr', coins: 1360 },
    { month: 'May', coins: 1740 },
    { month: 'Jun', coins: 1920 },
    { month: 'Jul', coins: 2210 },
    { month: 'Aug', coins: 3240 },
  ],
}
