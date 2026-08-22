export interface BecomePlayerStepMeta {
  id: number
  title: string
  subtitle: string
}

export const becomePlayerSteps: BecomePlayerStepMeta[] = [
  { id: 1, title: 'Account', subtitle: 'Basic details' },
  { id: 2, title: 'Games & skills', subtitle: 'What you play' },
  { id: 3, title: 'Rates & availability', subtitle: 'Set your prices' },
  { id: 4, title: 'Verify & payout', subtitle: 'ID + Squad Coin payout' },
  { id: 5, title: 'Review & submit', subtitle: 'Final check' },
]

export interface AccountStepData {
  avatarUrl: string | null
  avatarFile: File | null
  displayName: string
  email: string
  phone: string
  region: string
  timezone: string
  agreedToTerms: boolean
}

export function createAccountStepData(): AccountStepData {
  return {
    avatarUrl: null,
    avatarFile: null,
    displayName: '',
    email: '',
    phone: '',
    region: '',
    timezone: '',
    agreedToTerms: false,
  }
}

export interface GamesStepData {
  games: string[]
  highestRank: string
  role: string
  languages: string[]
  headline: string
}

export function createGamesStepData(): GamesStepData {
  return {
    games: [],
    highestRank: '',
    role: '',
    languages: [],
    headline: '',
  }
}

export type PricingModel = 'per-game' | 'per-hour' | 'per-session'

export interface GameRate {
  game: string
  price: number | null
}

export interface AvailabilityDay {
  key: string
  label: string
}

export const availabilityDays: AvailabilityDay[] = [
  { key: 'mon', label: 'M' },
  { key: 'tue', label: 'T' },
  { key: 'wed', label: 'W' },
  { key: 'thu', label: 'T' },
  { key: 'fri', label: 'F' },
  { key: 'sat', label: 'S' },
  { key: 'sun', label: 'S' },
]

export interface RatesStepData {
  rates: GameRate[]
  pricingModel: PricingModel
  offerFirstOrderFree: boolean
  availableDays: string[]
  timeWindow: string
  instantBooking: boolean
}

export function createRatesStepData(): RatesStepData {
  return {
    rates: [],
    pricingModel: 'per-game',
    offerFirstOrderFree: true,
    availableDays: [],
    timeWindow: '',
    instantBooking: false,
  }
}

export type PayoutSchedule = 'weekly' | 'bi-weekly' | 'monthly'

export interface VerifyStepData {
  idFrontFile: File | null
  idBackFile: File | null
  selfieVerified: boolean
  payoutSchedule: PayoutSchedule
}

export function createVerifyStepData(): VerifyStepData {
  return {
    idFrontFile: null,
    idBackFile: null,
    selfieVerified: false,
    payoutSchedule: 'weekly',
  }
}

// Mock Squad Coin wallet handle shared by the Verify and Review steps — real
// accounts will get a generated handle once auth is wired up in Phase 2/3.
export const mockWalletHandle = '1525835767'

export interface ReviewStepData {
  confirmedAccurate: boolean
}

export function createReviewStepData(): ReviewStepData {
  return {
    confirmedAccurate: false,
  }
}
