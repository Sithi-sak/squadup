-- Estars Leaderboard trend (4.60): `GET /estars/leaderboard` now also ranks the previous period
-- (e.g. the 7 days before this week) to tell whether each eStar moved up or down. That needs an
-- upper bound on `bookings.created_at`, so the RPC gains an optional `until`. Postgres can't add
-- a parameter with `create or replace`, so the old two-arg version is dropped first.

drop function public.estars_leaderboard(timestamptz, text);

create function public.estars_leaderboard(
  cutoff timestamptz,
  category_filter text default null,
  until timestamptz default null
)
returns table (
  id uuid,
  display_name text,
  avatar_url text,
  category text,
  rating numeric,
  coins bigint
)
language sql
stable
as $$
  select
    p.id,
    p.display_name,
    p.avatar_url,
    s.name as category,
    p.rating,
    sum(b.total_coins) as coins
  from public.bookings b
  join public.players p on p.id = b.player_id
  left join public.services s on s.id = p.highlighted_service_id
  where b.status = 'completed'
    and (cutoff is null or b.created_at >= cutoff)
    and (until is null or b.created_at < until)
  group by p.id, p.display_name, p.avatar_url, s.name, p.rating
  having sum(b.total_coins) > 0
    and (category_filter is null or lower(s.name) = lower(category_filter))
  order by coins desc
$$;
