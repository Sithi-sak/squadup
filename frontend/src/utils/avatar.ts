// DiceBear (https://www.dicebear.com) "Character" category styles only, per direct
// instruction — Minimalist and Scene styles are excluded. Kept to a curated subset with
// strong visual variety so avatars feel distinct from one another across the app.
const CHARACTER_STYLES = [
  'adventurer',
  'avataaars',
  'big-ears',
  'big-smile',
  'bottts',
  'croodles',
  'dylan',
  'fun-emoji',
  'lorelei',
  'micah',
  'miniavs',
  'notionists',
  'open-peeps',
  'personas',
  'pixel-art',
  'thumbs',
] as const

function hashSeed(seed: string): number {
  let hash = 0
  for (let i = 0; i < seed.length; i++) {
    hash = (hash << 5) - hash + seed.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

/** Deterministically picks a Character-category style for a given seed. */
export function avatarStyleFor(seed: string): (typeof CHARACTER_STYLES)[number] {
  return CHARACTER_STYLES[hashSeed(seed) % CHARACTER_STYLES.length] as (typeof CHARACTER_STYLES)[number]
}

/** Builds a DiceBear SVG URL for a seed, mixing styles so the app feels varied and alive. */
export function generatedAvatarUrl(seed: string): string {
  const style = avatarStyleFor(seed)
  return `https://api.dicebear.com/9.x/${style}/svg?seed=${encodeURIComponent(seed)}`
}

/**
 * Prefers a real uploaded photo when one exists, otherwise falls back to a generated
 * DiceBear avatar seeded off a stable id so the same entity always gets the same avatar.
 */
export function resolveAvatarUrl(seed: string, explicitUrl?: string | null): string {
  return explicitUrl || generatedAvatarUrl(seed)
}
