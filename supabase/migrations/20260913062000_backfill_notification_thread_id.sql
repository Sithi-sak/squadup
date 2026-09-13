-- Backfills `thread_id` on pre-existing "message" notifications (added in the prior migration,
-- but only new sends populate it going forward). `notify()` is called right after the message
-- insert in the same request, so each notification's `created_at` sits within a second or two of
-- the message that triggered it - match on closest timestamp within a 10s window, scoped to a
-- thread the notified user actually belongs to, to avoid pairing with an unrelated message.

with matches as (
  select distinct on (n.id)
    n.id as notification_id,
    m.thread_id
  from public.notifications n
  join public.messages m on m.sender_id <> n.user_id
  join public.message_threads t
    on t.id = m.thread_id
   and (t.user_a_id = n.user_id or t.user_b_id = n.user_id)
  where n.type = 'message'
    and n.thread_id is null
    and abs(extract(epoch from (n.created_at - m.created_at))) < 10
  order by n.id, abs(extract(epoch from (n.created_at - m.created_at)))
)
update public.notifications n
set thread_id = matches.thread_id
from matches
where matches.notification_id = n.id;
