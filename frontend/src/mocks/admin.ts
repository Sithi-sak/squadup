/** Mock data for the Admin panel (1.15). Built against `mockPlayers` (`mocks/players.ts`) and
 * `mockBuyers` (`mocks/buyers.ts`) ids so names line up with the rest of the app. No backend yet,
 * matches the "flagged players, disputes list" scope from CHECKPOINT.md; full moderation actions
 * (suspend, ban, payouts) land with the real admin endpoints in Phase 3 (3.8). */

import { generatedAvatarUrl } from '@/utils/avatar'

export type FlaggedPlayerStatus = 'pending' | 'reviewing' | 'actioned' | 'dismissed'
export type DisputeStatus = 'open' | 'investigating' | 'resolved' | 'refunded'
export type PalApplicationStatus = 'pending_review' | 'approved' | 'rejected'
/** Mirrors the `withdrawal_status` enum (4.28b). `requested` is what a Pal's payout lands as; an
 * admin moves it to `paid` (or `in_progress` first) or `rejected`. */
export type AdminWithdrawalStatus = 'requested' | 'in_progress' | 'paid' | 'rejected'

export interface AdminFlaggedPlayer {
  id: string
  playerId: string
  displayName: string
  avatarUrl: string | null
  reason: string
  details: string
  reportedBy: string
  reportCount: number
  reportedAt: string
  status: FlaggedPlayerStatus
  isBanned: boolean
}

export interface AdminPalApplication {
  id: string
  displayName: string
  avatarUrl: string | null
  email: string
  tagline: string | null
  timezone: string | null
  games: string[]
  rank: string | null
  role: string | null
  languages: string[]
  payoutSchedule: string
  idFrontUrl: string | null
  idBackUrl: string | null
  submittedAt: string
  status: PalApplicationStatus
}

export interface AdminDispute {
  id: string
  orderNumber: string
  buyerName: string
  palName: string
  serviceLabel: string
  reason: string
  totalCoins: number
  openedAt: string
  status: DisputeStatus
}

/** Mirrors `AdminWithdrawalOut` (`routers/admin.py`). `payoutCoins` is the 80% the Pal keeps
 * after SquadUp's 20% cut, which is the figure the admin is actually approving. */
export interface AdminWithdrawal {
  id: string
  reference: string | null
  playerId: string
  displayName: string
  avatarUrl: string | null
  coins: number
  feeCoins: number
  payoutCoins: number
  methodLabel: string
  methodDetail: string | null
  status: AdminWithdrawalStatus
  requestedAt: string
  reviewedAt: string | null
}

/** Mirrors `AdminNotificationOut` (`routers/admin.py`, 4.54). Derived from whatever is awaiting
 * a decision rather than stored, so `id` is source-prefixed (`flag:...`, `dispute:...`) and an
 * item disappears from the feed once it is decided. */
export type AdminNotificationType = 'report' | 'dispute' | 'payout' | 'application'

/** The Admin panel's tabs (`AdminView.vue`), named here so an alert can point at one. */
export type AdminTabKey = 'overview' | 'applications' | 'flagged' | 'disputes' | 'payouts'

export interface AdminNotification {
  id: string
  type: AdminNotificationType
  title: string
  message: string
  /** Admin tab this alert belongs to, so a click can open the queue that resolves it. */
  tab: AdminTabKey
  createdAt: string
}

export interface AdminOverviewStats {
  totalUsers: number
  totalPals: number
  ordersToday: number
  coinsInEscrow: number
  /** Platform revenue, split by where it came from (4.41). */
  bookingCommissionCoins: number
  payoutFeeCoins: number
  totalCommissionCoins: number
  reportsThisWeek: { day: string; count: number }[]
}

export const mockAdminFlaggedPlayers: AdminFlaggedPlayer[] = [
  {
    id: 'flag-1',
    playerId: 'p2',
    displayName: 'VelvetAce',
    avatarUrl: generatedAvatarUrl('p2'),
    reason: 'Inappropriate content',
    details: 'Profile bio contains a Discord invite promoting an off-platform payment scheme.',
    reportedBy: 'buyer-nova',
    reportCount: 4,
    reportedAt: '2026-08-20T09:12:00.000Z',
    status: 'pending',
    isBanned: false,
  },
  {
    id: 'flag-2',
    playerId: 'p5',
    displayName: 'RuneMender',
    avatarUrl: generatedAvatarUrl('p5'),
    reason: 'Harassment or bullying',
    details: 'Buyer reports being insulted in voice chat after a loss during a booked session.',
    reportedBy: 'buyer-kairuu',
    reportCount: 2,
    reportedAt: '2026-08-19T14:30:00.000Z',
    status: 'reviewing',
    isBanned: false,
  },
  {
    id: 'flag-3',
    playerId: 'p7',
    displayName: 'GlacierBloom',
    avatarUrl: generatedAvatarUrl('p7'),
    reason: 'Impersonation',
    details: 'Reported for using a pro player’s name and clips in the profile album.',
    reportedBy: 'buyer-pixel',
    reportCount: 1,
    reportedAt: '2026-08-18T08:05:00.000Z',
    status: 'pending',
    isBanned: false,
  },
  {
    id: 'flag-4',
    playerId: 'p3',
    displayName: 'MythicRoamer',
    avatarUrl: generatedAvatarUrl('p3'),
    reason: 'Spam or a scam',
    details: 'Multiple buyers report being asked to pay outside the app for a discount.',
    reportedBy: 'buyer-zerotwo',
    reportCount: 6,
    reportedAt: '2026-08-16T19:40:00.000Z',
    status: 'actioned',
    isBanned: false,
  },
  {
    id: 'flag-5',
    playerId: 'p6',
    displayName: 'EmberVanguard',
    avatarUrl: generatedAvatarUrl('p6'),
    reason: 'Something else',
    details: 'Report withdrawn by buyer after miscommunication was resolved directly.',
    reportedBy: 'buyer-lunaaa',
    reportCount: 1,
    reportedAt: '2026-08-14T11:20:00.000Z',
    status: 'dismissed',
    isBanned: false,
  },
]

export const mockAdminDisputes: AdminDispute[] = [
  {
    id: 'dispute-1',
    orderNumber: 'SU-48213',
    buyerName: 'mochi',
    palName: 'ShadowStrike',
    serviceLabel: 'Ranked Duo · 3 games',
    reason: "The Pal didn't show up",
    totalCoins: 1500,
    openedAt: '2026-08-21T10:00:00.000Z',
    status: 'open',
  },
  {
    id: 'dispute-2',
    orderNumber: 'SU-48190',
    buyerName: 'nova',
    palName: 'VelvetAce',
    serviceLabel: 'Coaching · 1 hour',
    reason: 'Service not as described',
    totalCoins: 600,
    openedAt: '2026-08-20T16:45:00.000Z',
    status: 'investigating',
  },
  {
    id: 'dispute-3',
    orderNumber: 'SU-48102',
    buyerName: 'kenji',
    palName: 'FrostJungler',
    serviceLabel: 'Ranked Duo · 2 games',
    reason: 'Billing - charged incorrectly',
    totalCoins: 800,
    openedAt: '2026-08-19T07:15:00.000Z',
    status: 'refunded',
  },
  {
    id: 'dispute-4',
    orderNumber: 'SU-47988',
    buyerName: 'pixel',
    palName: 'MythicRoamer',
    serviceLabel: 'Chill & Chat · 2 hours',
    reason: 'Poor quality or unskilled',
    totalCoins: 400,
    openedAt: '2026-08-17T13:25:00.000Z',
    status: 'resolved',
  },
  {
    id: 'dispute-5',
    orderNumber: 'SU-47915',
    buyerName: 'lunaaa',
    palName: 'RuneMender',
    serviceLabel: 'Ranked Duo · 1 game',
    reason: 'Inappropriate behaviour',
    totalCoins: 500,
    openedAt: '2026-08-15T21:05:00.000Z',
    status: 'open',
  },
]

export const mockAdminPalApplications: AdminPalApplication[] = [
  {
    id: 'application-1',
    displayName: 'NightOwlDrift',
    avatarUrl: generatedAvatarUrl('application-1'),
    email: 'nightowldrift@example.com',
    tagline: 'Diamond Duo Queue, chill vibes only',
    timezone: 'GMT+07:00',
    games: ['Valorant', 'League of Legends'],
    rank: 'Diamond',
    role: 'Duo Queue',
    languages: ['English', 'Khmer'],
    payoutSchedule: 'weekly',
    idFrontUrl: null,
    idBackUrl: null,
    submittedAt: '2026-09-04T10:15:00.000Z',
    status: 'pending_review',
  },
  {
    id: 'application-2',
    displayName: 'PixelSagess',
    avatarUrl: generatedAvatarUrl('application-2'),
    email: 'pixelsagess@example.com',
    tagline: 'Coaching + ranked climbs',
    timezone: 'GMT+07:00',
    games: ['Valorant'],
    rank: 'Immortal',
    role: 'Coach',
    languages: ['English'],
    payoutSchedule: 'bi_weekly',
    idFrontUrl: null,
    idBackUrl: null,
    submittedAt: '2026-09-03T18:40:00.000Z',
    status: 'pending_review',
  },
]

/** Fallback rows for the Payouts tab (4.28e), same offline convention as the lists above. */
export const mockAdminWithdrawals: AdminWithdrawal[] = [
  {
    id: 'withdrawal-1',
    reference: 'PO-4F2A9C31',
    playerId: 'p2',
    displayName: 'VelvetAce',
    avatarUrl: generatedAvatarUrl('p2'),
    coins: 4500,
    feeCoins: 900,
    payoutCoins: 3600,
    methodLabel: 'Card',
    methodDetail: '•••• 4242',
    status: 'requested',
    requestedAt: '2026-09-18T09:12:00',
    reviewedAt: null,
  },
  {
    id: 'withdrawal-2',
    reference: 'PO-9B17E6C0',
    playerId: 'p3',
    displayName: 'NovaStrike',
    avatarUrl: generatedAvatarUrl('p3'),
    coins: 1800,
    feeCoins: 360,
    payoutCoins: 1440,
    methodLabel: 'ABA Bank',
    methodDetail: '•••• 3356',
    status: 'requested',
    requestedAt: '2026-09-17T16:40:00',
    reviewedAt: null,
  },
  {
    id: 'withdrawal-3',
    reference: 'PO-2D80A5F4',
    playerId: 'p4',
    displayName: 'KiraByte',
    avatarUrl: generatedAvatarUrl('p4'),
    coins: 9000,
    feeCoins: 1800,
    payoutCoins: 7200,
    methodLabel: 'ABA Bank',
    methodDetail: '•••• 8810',
    status: 'paid',
    requestedAt: '2026-09-12T11:05:00',
    reviewedAt: '2026-09-13T08:30:00',
  },
]


/** Fallback rows for the admin bell (4.54), same offline convention as the lists above. */
export const mockAdminNotifications: AdminNotification[] = [
  {
    id: 'flag:flag-1',
    type: 'report',
    title: 'New report',
    message: 'VelvetAce was reported for inappropriate content',
    tab: 'flagged',
    createdAt: '2026-09-19T09:12:00.000Z',
  },
  {
    id: 'dispute:dispute-1',
    type: 'dispute',
    title: 'New dispute',
    message: "mochi opened a dispute on #SU-48213: The Pal didn't show up",
    tab: 'disputes',
    createdAt: '2026-09-19T08:40:00.000Z',
  },
  {
    id: 'withdrawal:withdrawal-1',
    type: 'payout',
    title: 'Payout request',
    message: 'VelvetAce requested a payout of 3,600 SC',
    tab: 'payouts',
    createdAt: '2026-09-18T09:12:00.000Z',
  },
  {
    id: 'application:application-1',
    type: 'application',
    title: 'Pal application',
    message: 'NightOwlDrift applied to become a Pal',
    tab: 'applications',
    createdAt: '2026-09-04T10:15:00.000Z',
  },
]
