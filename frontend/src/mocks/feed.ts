export interface FeedPost {
  id: string
  author: string
  handle: string
  tier: string | null
  timeAgo: string
  text: string
  hasImage: boolean
  likes: number
  comments: number
  following: boolean
  online: boolean
  category: 'games' | 'chilling' | 'clips'
}

export const mockFeedPosts: FeedPost[] = [
  {
    id: 'fp1',
    author: 'Oomfie',
    handle: '@oomfie',
    tier: 'Pal 3',
    timeAgo: '2h',
    text: 'Ranked grind paid off, hit Radiant with the squad tonight. Booking slots open this weekend, come climb with me.',
    hasImage: true,
    likes: 420,
    comments: 61,
    following: false,
    online: true,
    category: 'games',
  },
  {
    id: 'fp2',
    author: 'Meowa',
    handle: '@meowa',
    tier: 'Pal 2',
    timeAgo: '1d',
    text: 'New eMeow Feeding sessions are live. First order free this week only, lemme feed your kitty!',
    hasImage: false,
    likes: 420,
    comments: 61,
    following: true,
    online: false,
    category: 'chilling',
  },
  {
    id: 'fp3',
    author: 'CheyyChey',
    handle: '@cheyychey',
    tier: 'Pal 2',
    timeAgo: '1d',
    text: 'Finished a new commission today. Swipe through my Album for the full piece, taking 3 more slots this month!',
    hasImage: true,
    likes: 420,
    comments: 61,
    following: false,
    online: false,
    category: 'clips',
  },
]

export const mockFollowingPosts: FeedPost[] = [
  {
    id: 'ffp1',
    author: 'Oomfie',
    handle: '@oomfie',
    tier: 'Pal 3',
    timeAgo: '1h',
    text: 'About to go live for a ranked session, drop in and watch the climb. Booking open right after.',
    hasImage: true,
    likes: 420,
    comments: 61,
    following: true,
    online: true,
    category: 'games',
  },
  {
    id: 'ffp2',
    author: 'Denlynn',
    handle: '@denlynn',
    tier: 'Pal 2',
    timeAgo: '4h',
    text: 'Teaching Overwatch fundamentals all weekend. First order free, come say hi!',
    hasImage: false,
    likes: 420,
    comments: 61,
    following: true,
    online: false,
    category: 'chilling',
  },
  {
    id: 'ffp3',
    author: 'CheyyChey',
    handle: '@cheyychey',
    tier: 'Pal 2',
    timeAgo: '1d',
    text: 'New art drop, which one should I ink next? Swipe and vote in the comments.',
    hasImage: true,
    likes: 420,
    comments: 61,
    following: true,
    online: false,
    category: 'clips',
  },
]

export interface FeedPostDetail {
  id: string
  author: string
  handle: string
  tier: string | null
  timeAgo: string
  text: string
  hasImage: boolean
  likes: number
  comments: number
}

/** Looks up a post across every feed source (main feed, following, saved) by id. */
export function findFeedPost(id: string): FeedPostDetail | undefined {
  const post = mockFeedPosts.find((p) => p.id === id) ?? mockFollowingPosts.find((p) => p.id === id)
  if (post) return post

  const saved = mockSavedItems.find((item) => item.kind === 'post' && item.id === id)
  if (saved && saved.kind === 'post') {
    return {
      id: saved.id,
      author: saved.author,
      handle: saved.handle,
      tier: saved.tier,
      timeAgo: saved.savedAgo,
      text: saved.text,
      hasImage: saved.hasImage,
      likes: saved.likes,
      comments: saved.comments,
    }
  }

  return undefined
}

export interface FeedComment {
  id: string
  author: string
  timeAgo: string
  text: string
  likes: number
  isCreator?: boolean
  replies?: FeedComment[]
}

export const mockPostComments: Record<string, FeedComment[]> = {
  fp1: [
    {
      id: 'c1',
      author: 'KaiRuu',
      timeAgo: '2h',
      text: 'gg that duo was insane, ranked up twice 🔥 booking you again this weekend',
      likes: 42,
      replies: [
        {
          id: 'c1-r1',
          author: 'Oomfie',
          isCreator: true,
          timeAgo: '1h',
          text: "let's run it back tonight 💪 I'll hold a slot for you",
          likes: 12,
        },
      ],
    },
    {
      id: 'c2',
      author: 'mochi',
      timeAgo: '3h',
      text: 'booking you this weekend! do you do unrated chill games too?',
      likes: 18,
    },
    {
      id: 'c3',
      author: 'ZeroTwo',
      timeAgo: '5h',
      text: "what's your peak rank this act?",
      likes: 7,
    },
    {
      id: 'c4',
      author: 'lunaaa',
      timeAgo: '6h',
      text: 'the pentakill clip was so clean 👏 saved it to my album',
      likes: 23,
    },
  ],
}

export type SavedItem =
  | {
      kind: 'post'
      id: string
      author: string
      handle: string
      tier: string | null
      savedAgo: string
      text: string
      hasImage: boolean
      likes: number
      comments: number
    }
  | {
      kind: 'service'
      id: string
      name: string
      by: string
      category: string
      priceCoins: number
      priceUnit: string
      promoLabel: string | null
    }

export const mockSavedItems: SavedItem[] = [
  {
    kind: 'post',
    id: 'sv1',
    author: 'Oomfie',
    handle: '@oomfie',
    tier: 'Pal 3',
    savedAgo: 'saved 2h ago',
    text: 'Ranked grind paid off, hit Radiant with the squad tonight. Slots open this weekend.',
    hasImage: true,
    likes: 420,
    comments: 61,
  },
  {
    kind: 'service',
    id: 'sv2',
    name: 'eMeow Feeding',
    by: 'Meowa',
    category: 'Chilling service',
    priceCoins: 0,
    priceUnit: '/game',
    promoLabel: '1st free',
  },
  {
    kind: 'post',
    id: 'sv3',
    author: 'SleepySiren',
    handle: '@sleepysiren',
    tier: 'Pal 3',
    savedAgo: 'saved 3d ago',
    text: "Learn from the #1 eStar on SquadUp, free coaching VODs dropping every Friday. Bookmark this.",
    hasImage: false,
    likes: 420,
    comments: 61,
  },
]

export interface ExplorePost {
  id: string
  category: string
  author: string
  likes: string
}

export const exploreCategories = ['Trending', 'Valorant', 'League', 'Chilling', 'Clips', 'Art', 'Minecraft']

export const mockExplorePosts: ExplorePost[] = [
  { id: 'ep1', category: 'Valorant', author: 'Meowa', likes: '5.9k' },
  { id: 'ep2', category: 'Art', author: 'Meowa', likes: '5.9k' },
  { id: 'ep3', category: 'League', author: 'Meowa', likes: '5.9k' },
  { id: 'ep4', category: 'Chilling', author: 'Meowa', likes: '5.9k' },
  { id: 'ep5', category: 'Trending', author: 'Meowa', likes: '5.9k' },
  { id: 'ep6', category: 'Minecraft', author: 'Meowa', likes: '5.9k' },
  { id: 'ep7', category: 'Trending', author: 'Meowa', likes: '5.9k' },
  { id: 'ep8', category: 'Clips', author: 'Meowa', likes: '5.9k' },
  { id: 'ep9', category: 'Trending', author: 'Meowa', likes: '5.9k' },
]

export interface SuggestedPal {
  id: string
  name: string
  subtitle: string
}

export const mockSuggestedPals: SuggestedPal[] = [
  { id: 'sp1', name: 'anna1emil', subtitle: 'Valorant · 5.0' },
  { id: 'sp2', name: 'NanaOsak', subtitle: 'Adding Socials' },
  { id: 'sp3', name: 'Tilminah', subtitle: 'Profile Likes' },
  { id: 'sp4', name: 'Denlynn', subtitle: 'Overwatch 2' },
]

export interface TrendingTopic {
  id: string
  label: string
  postCount: string
}

export const mockTrendingTopics: TrendingTopic[] = [
  { id: 't1', label: '#RadiantRush', postCount: '2.4k posts' },
  { id: 't2', label: 'Valorant', postCount: '1.8k posts' },
  { id: 't3', label: 'eMeow Feeding', postCount: '950 posts' },
  { id: 't4', label: 'Watch Together', postCount: '610 posts' },
  { id: 't5', label: '#PentakillClips', postCount: '480 posts' },
]
