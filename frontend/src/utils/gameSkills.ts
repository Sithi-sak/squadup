import { games } from '@/data/games'
import type { GameSkill } from '@/stores/players'

/** Rank/role being edited for one game (4.64). Strings rather than nulls so they bind straight
 * to the select/input fields; `toGameSkills` turns blanks back into nulls for the API. */
export interface GameSkillDraft {
  rank: string
  role: string
}

export function gameRankOptions(game: string): string[] | null {
  return games.find((g) => g.name === game)?.ranks ?? null
}

export function gameRoleOptions(game: string): string[] | null {
  return games.find((g) => g.name === game)?.roles ?? null
}

/** Rank is required for every game; role only where the game has a role list (it's optional
 * free text otherwise). */
export function isGameSkillComplete(game: string, skill: GameSkillDraft | undefined): boolean {
  if (!skill?.rank.trim()) return false
  return !gameRoleOptions(game) || skill.role.trim().length > 0
}

export function toGameSkills(gameNames: string[], skills: Record<string, GameSkillDraft>): GameSkill[] {
  return gameNames.map((game) => ({
    game,
    rank: skills[game]?.rank.trim() || null,
    role: skills[game]?.role.trim() || null,
  }))
}

export function toGameSkillDrafts(gameSkills: GameSkill[]): Record<string, GameSkillDraft> {
  return Object.fromEntries(
    gameSkills.map((skill) => [skill.game, { rank: skill.rank ?? '', role: skill.role ?? '' }]),
  )
}
