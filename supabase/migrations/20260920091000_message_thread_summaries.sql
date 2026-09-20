-- Messages inbox performance (4.49). `GET /messages/threads` (routers/messages.py) used to make
-- four sequential REST round-trips - every thread, this user's thread states, their blocks, and
-- then *every message ever sent in any of those threads* - only to keep the last one per thread
-- and a per-thread unread tally. On an account with real history that last query grows without
-- bound while the page renders one preview line per chat.
--
-- This RPC does the whole thing in Postgres in one round-trip: the soft-delete and block filters
-- become `where` clauses, `distinct on` picks each thread's newest message off
-- `messages_thread_id_created_at_idx`, and the unread count is a grouped count off the partial
-- `messages_unread_idx`.
create function public.message_thread_summaries(p_user_id uuid)
returns table (
  id uuid,
  participant_id uuid,
  participant_display_name text,
  last_message_body text,
  last_message_image_url text,
  updated_at timestamptz,
  unread_count integer,
  muted boolean
)
language sql
stable
as $$
  with mine as (
    select
      t.id,
      t.created_at,
      case when t.user_a_id = p_user_id then t.user_b_id else t.user_a_id end as participant_id
    from public.message_threads t
    where t.user_a_id = p_user_id or t.user_b_id = p_user_id
  ),
  visible as (
    -- A thread the viewer deleted stays hidden until either side posts again
    -- (`_set_thread_state(..., deleted_at=None)`), and a blocked account's conversation drops
    -- out of the inbox in both directions (4.39) without the thread or its messages being
    -- touched, so unblocking brings the history back.
    select m.id, m.created_at, m.participant_id, coalesce(s.muted, false) as muted
    from mine m
    left join public.message_thread_states s
      on s.thread_id = m.id and s.user_id = p_user_id
    where s.deleted_at is null
      and not exists (
        select 1
        from public.user_blocks b
        where (b.blocker_id = p_user_id and b.blocked_id = m.participant_id)
           or (b.blocked_id = p_user_id and b.blocker_id = m.participant_id)
      )
  ),
  last_message as (
    select distinct on (msg.thread_id) msg.thread_id, msg.body, msg.image_url, msg.created_at
    from public.messages msg
    where msg.thread_id in (select id from visible)
    order by msg.thread_id, msg.created_at desc
  ),
  unread as (
    select msg.thread_id, count(*)::int as c
    from public.messages msg
    where msg.thread_id in (select id from visible)
      and msg.sender_id <> p_user_id
      and msg.read_at is null
    group by msg.thread_id
  )
  select
    v.id,
    v.participant_id,
    u.display_name,
    lm.body,
    lm.image_url,
    -- An empty thread sorts by when it was started, which is what the inbox showed before.
    coalesce(lm.created_at, v.created_at),
    coalesce(un.c, 0),
    v.muted
  from visible v
  left join public.users u on u.id = v.participant_id
  left join last_message lm on lm.thread_id = v.id
  left join unread un on un.thread_id = v.id
  order by coalesce(lm.created_at, v.created_at) desc
$$;
