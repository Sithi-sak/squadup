/** Settings page fixtures (1.14) not already covered by `AuthUser` / `PlayerProfile`, built per
 * `squadup_ui/SETTINGS/*.jpg`. */

export interface PaymentCard {
  id: string
  brand: 'visa' | 'apple-pay'
  label: string
  detail: string
  isDefault: boolean
}

export const mockPaymentCards: PaymentCard[] = [
  { id: 'visa-4242', brand: 'visa', label: 'Visa •••• 4242', detail: 'Expires 08/27', isDefault: true },
  { id: 'apple-pay', brand: 'apple-pay', label: 'Apple Pay', detail: 'ari@icloud.com', isDefault: false },
]

export interface ActiveSession {
  id: string
  device: string
  location: string
  lastActive: string
  current: boolean
}

export const mockActiveSessions: ActiveSession[] = [
  { id: 's1', device: 'Chrome · macOS', location: 'Phnom Penh', lastActive: 'active now', current: true },
  { id: 's2', device: 'iPhone · SquadUp', location: 'Phnom Penh', lastActive: '2h ago', current: false },
  { id: 's3', device: 'Firefox · Windows', location: 'Bangkok', lastActive: '5 days ago', current: false },
]

export const mockAccountDetails = {
  phone: '+855 12 345 678',
  country: 'Cambodia',
  memberSince: 'June 2024',
}

export const mockBlockedAccountsCount = 3
