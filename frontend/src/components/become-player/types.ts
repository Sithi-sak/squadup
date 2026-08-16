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
