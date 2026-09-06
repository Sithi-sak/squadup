-- Estars Leaderboard performance: `GET /estars/leaderboard` (routers/estars.py) used to pull
-- every player row and every matching booking row into Python and aggregate them there (3
-- sequential REST round-trips, unbounded for period=all_time). This RPC does the join/sum/filter
-- in Postgres in one round-trip instead.

create function public.estars_leaderboard(cutoff timestamptz, category_filter text default null)
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
  group by p.id, p.display_name, p.avatar_url, s.name, p.rating
  having sum(b.total_coins) > 0
    and (category_filter is null or lower(s.name) = lower(category_filter))
  order by coins desc
$$;

-- The RPC's `where b.status = 'completed' and b.created_at >= cutoff` needs both columns
-- together; `bookings_status_idx` (initial schema) only covers `status` alone.
create index bookings_status_created_at_idx on public.bookings (status, created_at);
