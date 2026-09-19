import { ApiError } from '@/lib/api'

/** Toast description for a caught error. Only an `ApiError`'s `detail` is written for a person
 * to read (`raise HTTPException(..., "You already have a booking with this Pal")`); anything
 * else is a bug, a dropped connection, or a framework message, and showing it verbatim just
 * hands the user something like "x is not a function". Those get `fallback` instead. */
export function userErrorMessage(err: unknown, fallback = 'Something went wrong. Please try again.') {
  if (err instanceof ApiError && err.status < 500 && err.message.trim()) return err.message
  return fallback
}
