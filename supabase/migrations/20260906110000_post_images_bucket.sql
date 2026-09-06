-- Backs the Feed composer's image upload (`CreatePostModal.vue`), which had a file picker UI
-- since 1.6b/1.8a but no storage bucket or backend wiring behind it (found 2026-09-06 - a user
-- post with an attached image never showed it). Uploads are re-encoded to WebP server-side
-- (`core/storage.py`'s `upload_image_as_webp`) before landing here, so the allowed mime type is
-- just webp regardless of what the client originally picked.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  ('post-images', 'post-images', true, 8388608, array['image/webp'])
on conflict (id) do nothing;
