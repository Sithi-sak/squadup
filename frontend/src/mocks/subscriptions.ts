/** Manage Subscriptions page fixtures (2.0) built per `squadup_ui/s2/MANAGE SUBSCRIPTIONS.jpg`. */

export type SubscriptionBillingCycle = 'Monthly' | 'Quarterly'
export type SubscriptionStatus = 'active' | 'cancelled'

export interface Subscription {
  id: string
  palName: string
  rating: string
  billingCycle: SubscriptionBillingCycle
  serviceLabel: string
  /** Next renewal date while active, or the date access ends once cancelled. */
  renewsOn: string
  priceCoins: number
  status: SubscriptionStatus
}

export const mockSubscriptions: Subscription[] = [
  {
    id: 'sub-1',
    palName: 'Oomfie',
    rating: '5.0',
    billingCycle: 'Monthly',
    serviceLabel: 'Valorant duo',
    renewsOn: '2026-08-08',
    priceCoins: 990,
    status: 'active',
  },
  {
    id: 'sub-2',
    palName: 'Meowa',
    rating: '5.0',
    billingCycle: 'Monthly',
    serviceLabel: 'eMeow Feeding',
    renewsOn: '2026-08-12',
    priceCoins: 990,
    status: 'active',
  },
  {
    id: 'sub-3',
    palName: 'SleepySiren',
    rating: '4.99',
    billingCycle: 'Quarterly',
    serviceLabel: 'Coaching',
    renewsOn: '2026-10-01',
    priceCoins: 891,
    status: 'active',
  },
]
