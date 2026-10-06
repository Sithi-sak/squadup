-- Realtime for Order Detail (CHECKPOINT.md 4.67a).
-- Order Detail subscribes to its booking's `UPDATE`s through the frontend's anon-key+JWT
-- client, the same way Messages does (20260823055705_messages_realtime_rls.sql). Realtime
-- authorizes each event against the RLS a SELECT would see, so `bookings` needs read policies.
-- Every write still goes through `routers/bookings.py`'s service-role client, which bypasses RLS.

create policy "Buyers can view their own bookings"
  on public.bookings for select
  to authenticated
  using (auth.uid() = user_id);

-- The subquery sees the Pal's own `players` row through "Players can view their own row".
create policy "Pals can view bookings for them"
  on public.bookings for select
  to authenticated
  using (
    exists (
      select 1
      from public.players p
      where p.id = bookings.player_id
        and p.user_id = auth.uid()
    )
  );

alter publication supabase_realtime add table public.bookings;
