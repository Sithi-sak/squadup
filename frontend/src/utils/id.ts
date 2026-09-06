const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

/** Seed/demo Pals (`p1`..`p8`, mocks/playerProfiles.ts) and their service ids are hand-authored
 * strings like "main", not real `services`/`players` rows - the backend has nothing to book
 * against until the 3.17 seed script lands. A uuid shape is the only reliable signal that an id
 * actually came from the database rather than a mock fixture. */
export function isRealId(id: string): boolean {
  return UUID_RE.test(id)
}
