/** Mock data for the Admin panel (1.15). Built against `mockPlayers` (`mocks/players.ts`) and
 * `mockBuyers` (`mocks/buyers.ts`) ids so names line up with the rest of the app. No backend yet,
 * matches the "flagged players, disputes list" scope from CHECKPOINT.md; full moderation actions
 * (suspend, ban, payouts) land with the real admin endpoints in Phase 3 (3.8). */

import { generatedAvatarUrl } from '@/utils/avatar'

export type FlaggedPlayerStatus = 'pending' | 'reviewing' | 'actioned' | 'dismissed'
export type DisputeStatus = 'open' | 'investigating' | 'resolved' | 'refunded'
export type PalApplicationStatus = 'pending_review' | 'approved' | 'rejected'

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

export interface AdminOverviewStats {
  totalUsers: number
  totalPals: number
  ordersToday: number
  coinsInEscrow: number
  totalCommissionCoins: number
  reportsThisWeek: { day: string; count: number }[]
}

export const mockAdminOverviewStats: AdminOverviewStats = {
  totalUsers: 8420,
  totalPals: 1180,
  ordersToday: 246,
  coinsInEscrow: 58400,
  totalCommissionCoins: 41600,
  reportsThisWeek: [
    { day: 'M', count: 2 },
    { day: 'T', count: 4 },
    { day: 'W', count: 1 },
    { day: 'T', count: 5 },
    { day: 'F', count: 3 },
    { day: 'S', count: 7 },
    { day: 'S', count: 3 },
  ],
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
