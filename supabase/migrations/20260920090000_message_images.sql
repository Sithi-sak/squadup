-- Image messages in chat (4.49). The composer's paperclip has been decoration since 3.5c; this
-- gives it somewhere to put a file.
--
-- `body` stays `not null` but drops to a default of '' so an image-only message is still one
-- ordinary `messages` row rather than a second table or a nullable column every reader has to
-- branch on - `routers/messages.py` requires text *or* an image, and the transcript renders
-- whichever parts are present.
alter table public.messages
  add column image_url text,
  alter column body set default '';

-- Uploads are re-encoded to WebP server-side (`core/storage.py`'s `upload_image_as_webp`)
-- before landing here, so webp is the only allowed mime type - same as `post-images` (2026-09-06).
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  ('message-images', 'message-images', true, 8388608, array['image/webp'])
on conflict (id) do nothing;

-- `message_thread_summaries` (next migration) takes each thread's newest message via
-- `distinct on (thread_id) ... order by thread_id, created_at desc`, and counts the unread ones.
-- `messages_thread_id_idx` (initial schema) covers only `thread_id`, so both still sorted.
create index messages_thread_id_created_at_idx on public.messages (thread_id, created_at desc);
create index messages_unread_idx on public.messages (thread_id, sender_id) where read_at is null;
