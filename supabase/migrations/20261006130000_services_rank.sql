-- Rank per service (CHECKPOINT.md 4.68a).
-- The rank a service is offered at (e.g. a Valorant duo at Immortal), shown as a chip on the
-- service card. Separate from `players.game_skills` (4.64), the Pal's own rank per game, so two
-- services for the same game can differ. Null for services without one.

alter table public.services add column rank text;
