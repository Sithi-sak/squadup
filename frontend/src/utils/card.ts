/** Card number helpers, mirroring `routers/wallet.py`'s `_luhn_ok`/`_card_network` so the Add
 * payout method form validates and labels exactly what the backend would accept (4.32). */

export type CardNetwork = 'visa' | 'mastercard' | 'card'

/** Spaces and dashes carry no meaning in a card number - the backend strips them the same way. */
export function cardDigits(value: string) {
  return value.replace(/\D/g, '')
}

/**
 * The check digit every real card number carries. It catches a typo or an invented number like
 * 1111111111111111 - it does not prove the card exists, and nothing here can, since no network is
 * ever contacted.
 */
export function luhnOk(digits: string) {
  let total = 0
  for (let index = 0; index < digits.length; index += 1) {
    let value = Number(digits[digits.length - 1 - index])
    if (index % 2 === 1) {
      value *= 2
      if (value > 9) value -= 9
    }
    total += value
  }
  return total % 10 === 0
}

/** Network from the issuer prefix. Only Visa and Mastercard have an icon in `assets/`, so every
 * other network falls back to the generic 'card' rather than being mislabelled as one of them. */
export function cardNetwork(digits: string): CardNetwork {
  if (digits.startsWith('4')) return 'visa'
  const two = Number(digits.slice(0, 2))
  const four = Number(digits.slice(0, 4))
  if (digits.length >= 2 && two >= 51 && two <= 55) return 'mastercard'
  if (digits.length >= 4 && four >= 2221 && four <= 2720) return 'mastercard'
  return 'card'
}

/** 4.59: the demo payout card (user request). Payouts are simulated, and this number fails the
 * Luhn check, so it is let through by name. Mirrors `routers/wallet.py`'s `_DEMO_PAYOUT_CARDS`. */
const DEMO_PAYOUT_CARDS = new Set(['5156839937706777'])

export function isValidCardNumber(digits: string) {
  if (DEMO_PAYOUT_CARDS.has(digits)) return true
  return digits.length >= 12 && digits.length <= 19 && luhnOk(digits)
}

/** Groups of four as you type, the way a real card form reflows the number back at you. */
export function formatCardNumber(value: string) {
  return (cardDigits(value).match(/.{1,4}/g) ?? []).join(' ').slice(0, 23)
}
