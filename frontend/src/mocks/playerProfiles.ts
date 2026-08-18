import type { PlayerProfile, PlayerServiceDetail, PlayerSummary } from '@/stores/players'

/**
 * Fully authored Player Profile detail, keyed by `PlayerSummary.id`. Only `p1` gets the full
 * treatment for now (see squadup_ui/PROFILE/*.jpg); every other mock player falls back to
 * `buildGenericProfile` below.
 */
export const mockPlayerProfiles: Record<string, PlayerProfile> = {
  p1: {
    id: 'p1',
    handle: '@1525835767',
    timezone: 'GMT+07:00',
    language: 'English',
    tier: 'Pal 2',
    highlightBadge: 'Legends',
    subscribeLabel: 'Subscribe: 20% Off',
    highlightedServiceId: 'ranked-duo',
    services: [
      { id: 'echat', name: 'E-Chat', promoBadge: '1st Order Free', priceCoins: 0, priceUnit: '/15min' },
      {
        id: 'ranked-duo',
        name: 'Ranked Duo',
        promoBadge: '1st Order Free',
        priceCoins: 0,
        priceUnit: '/Game',
      },
      { id: 'lol', name: 'League of Legends', promoBadge: '15% Off', priceCoins: 200, priceUnit: '/Game' },
      { id: 'album-likes', name: 'Album Likes', promoBadge: '1st Order Free', priceCoins: 0, priceUnit: '/++Game' },
      { id: 'coaching', name: 'Coaching Session', promoBadge: null, priceCoins: 300, priceUnit: '/Game' },
      { id: 'voice-call', name: 'Voice Call', promoBadge: null, priceCoins: 250, priceUnit: '/Game' },
      { id: 'watch-together', name: 'Watch Together', promoBadge: null, priceCoins: 200, priceUnit: '/Game' },
    ],
    serviceDetails: {
      echat: {
        title: 'E-Chat',
        rating: null,
        servedCount: 0,
        description: 'Voice call and chill, no game required. First 15 minutes are on the house.',
        styles: ['Laid Back'],
        platforms: ['SquadUp'],
        serviceTypes: [
          { label: 'Voice Chat (15 min)', priceCoins: 0, priceUnit: '/15min', promoBadge: '1st Order Free' },
        ],
        avgResponseTime: '5-10 mins',
      },
      'ranked-duo': {
        title: 'Ranked Duo',
        rating: 4.8,
        servedCount: 640,
        description:
          'Free order is a placement-game duo; paid order is a full ranked climbing session with VOD review after.',
        styles: ['Aggressive Mid Lane', 'Shotcalling'],
        platforms: ['League of Legends', 'SquadUp'],
        serviceTypes: [
          { label: 'Duo Queue (5 games)', priceCoins: 0, priceUnit: '/Game', promoBadge: '1st Order Free' },
        ],
        avgResponseTime: '5-10 mins',
      },
      lol: {
        title: 'League of Legends',
        rating: 4.6,
        servedCount: 1200,
        description: 'Ranked or normals, any role. Bring your own duo or queue up with mine.',
        styles: ['Mid Lane', 'Jungle'],
        platforms: ['League of Legends'],
        serviceTypes: [
          { label: 'Ranked Game', priceCoins: 200, priceUnit: '/Game', promoBadge: '15% Off' },
        ],
        avgResponseTime: '10-15 mins',
      },
      'album-likes': {
        title: 'Album Likes',
        rating: null,
        servedCount: 0,
        description: 'Drop a highlight clip and get feedback on it during our session.',
        styles: [],
        platforms: ['SquadUp'],
        serviceTypes: [
          { label: 'Clip Review', priceCoins: 0, priceUnit: '/++Game', promoBadge: '1st Order Free' },
        ],
        avgResponseTime: '10-20 mins',
      },
      coaching: {
        title: 'Coaching Session',
        rating: 4.9,
        servedCount: 210,
        description: 'One-on-one VOD review and lane fundamentals, tailored to your rank.',
        styles: ['Fundamentals', 'Macro Play'],
        platforms: ['League of Legends', 'SquadUp'],
        serviceTypes: [{ label: 'Coaching (1 hour)', priceCoins: 300, priceUnit: '/Game', promoBadge: null }],
        avgResponseTime: '10-15 mins',
      },
      'voice-call': {
        title: 'Voice Call',
        rating: 4.7,
        servedCount: 88,
        description: 'Just here to chat and keep you company between matches.',
        styles: ['Laid Back'],
        platforms: ['SquadUp'],
        serviceTypes: [{ label: 'Voice Call', priceCoins: 250, priceUnit: '/Game', promoBadge: null }],
        avgResponseTime: '15-20 mins',
      },
      'watch-together': {
        title: 'Watch Together',
        rating: 4.5,
        servedCount: 54,
        description: 'Pro matches, streams, or your favorite show. Let’s watch it together.',
        styles: ['Laid Back'],
        platforms: ['SquadUp'],
        serviceTypes: [{ label: 'Watch Session', priceCoins: 200, priceUnit: '/Game', promoBadge: null }],
        avgResponseTime: '15-20 mins',
      },
    },
    reviews: {
      'ranked-duo': [
        {
          id: 'r1',
          author: 'Nary K.',
          rating: 5,
          text: 'Carried me from Gold to Plat in a week, super patient with call-outs.',
          timeAgo: '2d',
          sentiment: 'positive',
        },
        {
          id: 'r2',
          author: 'Sok R.',
          rating: 5,
          text: 'Great comms and always on time.',
          timeAgo: '5d',
          sentiment: 'positive',
        },
        {
          id: 'r3',
          author: 'Dara P.',
          rating: 3,
          text: 'Good gameplay but response time was a bit slow.',
          timeAgo: '1w',
          sentiment: 'neutral',
        },
      ],
    },
    feed: [
      {
        id: 'f1',
        timeAgo: '2h',
        text: "GG on tonight's duo queue grind, five straight wins and finally broke into Diamond. Book me this week for a carry.",
        hasImage: true,
        likes: 420,
        comments: 61,
      },
      {
        id: 'f2',
        timeAgo: '1d',
        text: 'New service dropped: Ranked Duo! First order is free, come climb with me.',
        hasImage: false,
        likes: 210,
        comments: 34,
      },
      {
        id: 'f3',
        timeAgo: '3d',
        text: 'Late-night stream was wild, thanks to everyone who dropped by. Clip of the pentakill is in my Album tab.',
        hasImage: true,
        likes: 530,
        comments: 88,
      },
    ],
    album: [
      { id: 'a1', kind: 'clip', label: 'Ranked Duo', views: 8100, likes: 940, shares: 180, durationSeconds: 42 },
      { id: 'a2', kind: 'clip', label: 'Pentakill', views: 18000, likes: 3100, shares: 880, durationSeconds: 162 },
      { id: 'a3', kind: 'screenshot', label: 'Screenshot', views: 3200, likes: 410, shares: 52, durationSeconds: null },
      { id: 'a4', kind: 'clip', label: 'Clutch Play', views: 21000, likes: 2400, shares: 610, durationSeconds: 22 },
      { id: 'a5', kind: 'screenshot', label: 'Fan Art', views: 5900, likes: 780, shares: 96, durationSeconds: null },
      { id: 'a6', kind: 'clip', label: 'Practice VOD', views: 4400, likes: 520, shares: 71, durationSeconds: 102 },
      { id: 'a7', kind: 'screenshot', label: 'Watch Party', views: 2900, likes: 300, shares: 40, durationSeconds: null },
      { id: 'a8', kind: 'clip', label: 'Highlight Reel', views: 8100, likes: 940, shares: 180, durationSeconds: 152 },
      { id: 'a9', kind: 'screenshot', label: 'Emote', views: 6700, likes: 1500, shares: 210, durationSeconds: null },
    ],
    wish: [
      { id: 'w1', title: 'Immortal Rank Boost', game: 'Valorant', type: 'Boosting', priceCoins: 1200, saved: true },
      { id: 'w2', title: 'Duo to Diamond', game: 'League of Legends', type: 'Duo', priceCoins: 900, saved: true },
      { id: 'w3', title: 'Full Clear Run', game: 'Genshin Impact', type: 'Co-op', priceCoins: 600, saved: true },
      { id: 'w4', title: 'Boss Rush Help', game: 'Elden Ring', type: 'Co-op', priceCoins: 750, saved: true },
      { id: 'w5', title: 'Victory Royale x5', game: 'Fortnite', type: 'Carry', priceCoins: 500, saved: true },
      { id: 'w6', title: 'Ranked Grind Night', game: 'Apex Legends', type: 'Coaching', priceCoins: 850, saved: true },
    ],
    postsCount: 42,
    followersCount: 1200,
    followingCount: 30,
  },
  /** The current mock account's own (freshly started) Pal profile, linked via `AuthUser.playerId`.
   * Distinct from `p1`, which is a separate seed Pal the current account books/messages. */
  self: {
    id: 'self',
    handle: '@1525835767',
    timezone: 'GMT+07:00',
    language: 'English',
    tier: 'Pal 2',
    highlightBadge: null,
    subscribeLabel: null,
    highlightedServiceId: '',
    services: [],
    serviceDetails: {},
    reviews: {},
    feed: [],
    album: [],
    wish: [],
    postsCount: 128,
    followersCount: 3400,
    followingCount: 86,
  },
}

/** Minimal detail built from a sidebar listing, for services that have no authored entry. */
export function fallbackServiceDetail(name: string, priceCoins: number, priceUnit: string, promoBadge: string | null): PlayerServiceDetail {
  return {
    title: name,
    rating: null,
    servedCount: 0,
    description: 'Service details coming soon.',
    styles: [],
    platforms: [],
    serviceTypes: [{ label: name, priceCoins, priceUnit, promoBadge }],
    avgResponseTime: '10-20 mins',
  }
}

/** Lightweight profile for mock players without an authored `mockPlayerProfiles` entry. */
function buildGenericProfile(player: PlayerSummary): PlayerProfile {
  const serviceId = 'main'
  return {
    id: player.id,
    handle: `@${player.id}`,
    timezone: 'GMT+07:00',
    language: player.languages[0] ?? 'English',
    tier: 'Pal 1',
    highlightBadge: null,
    subscribeLabel: null,
    highlightedServiceId: serviceId,
    services: [
      {
        id: serviceId,
        name: player.games[0] ?? 'Session',
        promoBadge: player.promoBadge,
        priceCoins: player.priceCoins ?? 0,
        priceUnit: '/Game',
      },
    ],
    serviceDetails: {
      [serviceId]: {
        title: player.games[0] ?? 'Session',
        rating: player.rating,
        servedCount: player.reviewCount ?? 0,
        description: player.tagline ?? 'Service details coming soon.',
        styles: player.role ? [player.role] : [],
        platforms: player.games,
        serviceTypes: [
          { label: 'Standard Session', priceCoins: player.priceCoins ?? 0, priceUnit: '/Game', promoBadge: player.promoBadge },
        ],
        avgResponseTime: '10-20 mins',
      },
    },
    reviews: { [serviceId]: [] },
    feed: [],
    album: [],
    wish: [],
    postsCount: 0,
    followersCount: 0,
    followingCount: 0,
  }
}

export function getPlayerProfile(player: PlayerSummary): PlayerProfile {
  return mockPlayerProfiles[player.id] ?? buildGenericProfile(player)
}
