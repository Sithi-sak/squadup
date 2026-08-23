-- Realtime for Messages (CHECKPOINT.md 3.5b).
-- The Messages page's live-update subscription runs through the frontend's own anon-key+JWT
-- Supabase client straight against these tables (`supabase.channel(...).on('postgres_changes',
-- ...)` in 3.5d), not the service-role backend every other feature uses. Supabase Realtime
-- authorizes each change event against the same RLS a SELECT would see, so these tables need
-- read policies even though every actual write still goes through `routers/messages.py`'s
-- service-role client, which bypasses RLS entirely and is unaffected by these policies.

create policy "Participants can view their message threads"
  on public.message_threads for select
  to authenticated
  using (auth.uid() = user_a_id or auth.uid() = user_b_id);

create policy "Participants can view their thread's messages"
  on public.messages for select
  to authenticated
  using (
    exists (
      select 1
      from public.message_threads mt
      where mt.id = messages.thread_id
        and (mt.user_a_id = auth.uid() or mt.user_b_id = auth.uid())
    )
  );

-- Supabase's `supabase_realtime` publication starts empty; a table must be added explicitly
-- before `postgres_changes` will ever fire for it, independent of the RLS policies above.
alter publication supabase_realtime add table public.message_threads;
alter publication supabase_realtime add table public.messages;
