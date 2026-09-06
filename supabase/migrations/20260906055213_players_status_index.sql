-- `status`/`is_banned` (added in 20260905160703) were never indexed, even though every
-- public player listing query (`GET /players`, `/players/suggested`) filters on both together.
create index players_status_is_banned_idx on public.players (status, is_banned);
