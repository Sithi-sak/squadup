import { generatedAvatarUrl } from '@/utils/avatar'

export interface EstarLeaderboardEntry {
  id: string
  rank: number
  displayName: string
  avatarUrl: string | null
  category: string
  rating: number
  coins: number
  trend: 'up' | 'down' | 'flat'
}

export const mockEstarsLeaderboard: EstarLeaderboardEntry[] = [
  {
    id: 'e1',
    rank: 1,
    displayName: 'Oomfie',
    avatarUrl: generatedAvatarUrl('e1'),
    category: 'Valorant duo',
    rating: 5.0,
    coins: 48200,
    trend: 'up',
  },
  {
    id: 'e2',
    rank: 2,
    displayName: 'Meowa',
    avatarUrl: generatedAvatarUrl('e2'),
    category: 'eMeow Feeding',
    rating: 5.0,
    coins: 41900,
    trend: 'up',
  },
  {
    id: 'e3',
    rank: 3,
    displayName: 'SleepySiren',
    avatarUrl: generatedAvatarUrl('e3'),
    category: 'Coaching',
    rating: 4.99,
    coins: 38400,
    trend: 'flat',
  },
  {
    id: 'e4',
    rank: 4,
    displayName: 'CheyyChey',
    avatarUrl: generatedAvatarUrl('e4'),
    category: 'Drawing',
    rating: 5.0,
    coins: 31200,
    trend: 'up',
  },
  {
    id: 'e5',
    rank: 5,
    displayName: 'MayBeGenius',
    avatarUrl: generatedAvatarUrl('e5'),
    category: 'League of Legends',
    rating: 4.98,
    coins: 28700,
    trend: 'up',
  },
  {
    id: 'e6',
    rank: 6,
    displayName: 'PrettyGirls',
    avatarUrl: generatedAvatarUrl('e6'),
    category: 'Adding Socials',
    rating: 5.0,
    coins: 26400,
    trend: 'down',
  },
  {
    id: 'e7',
    rank: 7,
    displayName: 'anna1emilia',
    avatarUrl: generatedAvatarUrl('e7'),
    category: 'Valorant',
    rating: 5.0,
    coins: 24100,
    trend: 'up',
  },
  {
    id: 'e8',
    rank: 8,
    displayName: 'Tilminah',
    avatarUrl: generatedAvatarUrl('e8'),
    category: 'Profile Likes',
    rating: 4.99,
    coins: 22800,
    trend: 'flat',
  },
  {
    id: 'e9',
    rank: 9,
    displayName: 'NanaOsaki',
    avatarUrl: generatedAvatarUrl('e9'),
    category: 'Adding Socials',
    rating: 5.0,
    coins: 21300,
    trend: 'up',
  },
  {
    id: 'e10',
    rank: 10,
    displayName: 'Teddy_',
    avatarUrl: generatedAvatarUrl('e10'),
    category: 'Minecraft',
    rating: 5.0,
    coins: 19900,
    trend: 'up',
  },
]

export const estarsCategories = [
  'All categories',
  'Valorant',
  'League of Legends',
  'Minecraft',
  'Coaching',
  'Drawing',
  'Adding Socials',
  'Profile Likes',
  'eMeow Feeding',
]
