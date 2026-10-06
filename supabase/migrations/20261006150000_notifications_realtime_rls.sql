-- Realtime for the header bell and messages badge (CHECKPOINT.md 4.73a).
-- The frontend subscribes to its own `notifications` INSERTs through the anon-key+JWT client,
-- the same way Messages and Order Detail do (20260823055705_messages_realtime_rls.sql,
-- 20261006120000_bookings_realtime_rls.sql). Realtime authorizes each event against the RLS a
-- SELECT would see, so the table needs a read policy. Every write still goes through the
-- service-role backend (`core/notify.py`, `routers/notifications.py`), which bypasses RLS.

create policy "Users can view their own notifications"
  on public.notifications for select
  to authenticated
  using (auth.uid() = user_id);

alter publication supabase_realtime add table public.notifications;
