/** Lightweight buyer directory for orders placed against the current mock account's own Pal
 * profile (`self`), e.g. Pal Dashboard incoming orders. Distinct from `mockPlayers`, which are
 * seed Pals, not buyers. */
export interface BuyerSummary {
  id: string
  displayName: string
}

export const mockBuyers: BuyerSummary[] = [
  { id: 'buyer-kairuu', displayName: 'KaiRuu' },
  { id: 'buyer-mochi', displayName: 'mochi' },
  { id: 'buyer-zerotwo', displayName: 'ZeroTwo' },
  { id: 'buyer-lunaaa', displayName: 'lunaaa' },
  { id: 'buyer-pixel', displayName: 'pixel' },
  { id: 'buyer-nova', displayName: 'nova' },
  { id: 'buyer-kenji', displayName: 'kenji' },
]

export function getBuyer(id: string): BuyerSummary | null {
  return mockBuyers.find((b) => b.id === id) ?? null
}
