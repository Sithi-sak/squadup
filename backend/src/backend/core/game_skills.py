from pydantic import BaseModel

from .schema import CamelModel


class GameSkill(CamelModel):
    """One game a Pal plays, with their rank/role in that game (`players.game_skills`, 4.64)."""

    game: str
    rank: str | None = None
    role: str | None = None


class GameSkillIn(BaseModel):
    game: str
    rank: str | None = None
    role: str | None = None


def _clean(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value.strip() or None


def game_skills_of(player: dict) -> list[dict]:
    """A Pal's per-game rank/role, one entry per game in `games` (same order). Rows written
    before `game_skills` existed (or before the migration is applied, where the key is absent)
    fall back to the old single `rank`/`role` on the first game, which is what the old Become a
    Pal form tied them to."""
    games: list[str] = player.get("games") or []
    stored = {s.get("game"): s for s in player.get("game_skills") or [] if isinstance(s, dict)}
    skills = []
    for index, game in enumerate(games):
        skill = stored.get(game)
        if skill is not None:
            rank, role = _clean(skill.get("rank")), _clean(skill.get("role"))
        elif not stored and index == 0:
            rank, role = player.get("rank"), player.get("role")
        else:
            rank, role = None, None
        skills.append({"game": game, "rank": rank, "role": role})
    return skills
