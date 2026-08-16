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
  displayName: string
  email: string
  phone: string
  region: string
  timezone: string
  password: string
  agreedToTerms: boolean
}

export function createAccountStepData(): AccountStepData {
  return {
    avatarUrl: null,
    displayName: '',
    email: '',
    phone: '',
    region: '',
    timezone: '',
    password: '',
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
