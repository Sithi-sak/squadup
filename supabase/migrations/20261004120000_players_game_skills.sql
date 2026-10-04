-- Rank/role per game (4.64). `players.rank`/`role` were a single value across every game a Pal
-- listed, so a Pal with Valorant and CS2 could only give one rank for both. `game_skills` holds
-- one `{game, rank, role}` per game instead. Additive only: `rank`/`role` stay and the backend
-- keeps them mirrored from the first game, so code that still reads them keeps working.
alter table public.players
  add column game_skills jsonb not null default '[]'::jsonb;

-- Backfill: one entry per listed game. The old form took its rank/role ladder from the first
-- game that had one, which is almost always the first game, so that is where they land.
update public.players p
set game_skills = (
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'game', g.game,
        'rank', case when g.ord = 1 then p.rank end,
        'role', case when g.ord = 1 then p.role end
      )
      order by g.ord
    ),
    '[]'::jsonb
  )
  from unnest(p.games) with ordinality as g (game, ord)
);
