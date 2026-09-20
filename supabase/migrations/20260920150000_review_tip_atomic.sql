-- 4.53: `POST /reviews` lost a tip mid-flight (user report, 2026-09-20). The handler did the
-- whole submission as eight separate PostgREST round-trips - duplicate check, insert, two rating
-- recomputes, then debit buyer / credit Pal as two more. A dropped Supabase connection between
-- the debit and the credit committed the first half and abandoned the second: booking
-- 934cc068 got its review and took 200 SC off the buyer, the Pal was never paid, and because a
-- review now existed the buyer couldn't retry - "already reviewed".
--
-- The submission becomes one transaction. Either the review, both rating recomputes and both
-- sides of the tip land together, or nothing does and the buyer can just press submit again.

-- One review per booking, enforced where it can't be raced. The handler's read-then-insert check
-- stays as the friendly 409, but two concurrent submits could both pass it.
create unique index if not exists reviews_booking_id_key
  on public.reviews (booking_id)
  where booking_id is not null;

-- Errors are raised with custom SQLSTATEs rather than text so `routers/reviews.py` maps them to
-- HTTP codes without matching on message strings:
--   SU404 order not found or not the caller's   SU409 order not completed
--   SU410 already reviewed                      SU411 Pal has no account to be tipped
--   SU412 buyer can't afford the tip
create or replace function public.submit_review(
  p_booking_id uuid,
  p_user_id uuid,
  p_rating integer,
  p_text text,
  p_sentiment review_sentiment,
  p_highlights text[],
  p_tip_coins integer,
  p_tip_detail text,
  p_tip_from text
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_service_id uuid;
  v_player_id uuid;
  v_status booking_status;
  v_pal_user_id uuid;
  v_balance integer;
  v_review_id uuid;
begin
  -- `for update` on the booking serialises two submits for the same order behind each other, so
  -- the loser sees the winner's review below instead of racing it to the unique index.
  select b.service_id, b.player_id, b.status
    into v_service_id, v_player_id, v_status
  from public.bookings b
  where b.id = p_booking_id and b.user_id = p_user_id
  for update;

  if not found then
    raise exception 'Order not found' using errcode = 'SU404';
  end if;
  if v_status <> 'completed' then
    raise exception 'Order must be completed before it can be reviewed' using errcode = 'SU409';
  end if;
  if exists (select 1 from public.reviews r where r.booking_id = p_booking_id) then
    raise exception 'This order has already been reviewed' using errcode = 'SU410';
  end if;

  select p.user_id into v_pal_user_id from public.players p where p.id = v_player_id;

  insert into public.reviews (service_id, booking_id, author_id, rating, text, sentiment, highlights, tip_coins)
  values (v_service_id, p_booking_id, p_user_id, p_rating, p_text, p_sentiment, p_highlights, p_tip_coins)
  returning id into v_review_id;

  -- Reviews hang off a service, but a Pal's headline rating aggregates across all of theirs, so
  -- both the service row and the player row are recomputed from scratch.
  update public.services s
  set rating = (select round(avg(r.rating)::numeric, 2) from public.reviews r where r.service_id = s.id)
  where s.id = v_service_id;

  update public.players p
  set rating = agg.avg_rating, review_count = agg.n
  from (
    select round(avg(r.rating)::numeric, 2) as avg_rating, count(*)::int as n
    from public.reviews r
    join public.services s on s.id = r.service_id
    where s.player_id = v_player_id
  ) agg
  where p.id = v_player_id;

  if p_tip_coins > 0 then
    if v_pal_user_id is null then
      raise exception 'This Pal can''t receive tips yet' using errcode = 'SU411';
    end if;

    select u.coin_balance into v_balance from public.users u where u.id = p_user_id for update;
    if v_balance is null or v_balance < p_tip_coins then
      raise exception 'Insufficient Squad Coin balance' using errcode = 'SU412';
    end if;

    update public.users set coin_balance = coin_balance - p_tip_coins where id = p_user_id;
    update public.users set coin_balance = coin_balance + p_tip_coins where id = v_pal_user_id;

    insert into public.wallet_transactions (user_id, kind, status, label, detail, coins, booking_id)
    values
      (p_user_id, 'tip', 'completed', 'Tip', p_tip_detail, -p_tip_coins, p_booking_id),
      (v_pal_user_id, 'tip', 'completed', 'Tip', p_tip_from, p_tip_coins, p_booking_id);
  end if;

  return v_review_id;
end;
$$;

revoke all on function public.submit_review(uuid, uuid, integer, text, review_sentiment, text[], integer, text, text) from public, anon, authenticated;
grant execute on function public.submit_review(uuid, uuid, integer, text, review_sentiment, text[], integer, text, text) to service_role;
