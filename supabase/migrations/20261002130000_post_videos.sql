-- Video clip posts (4.61). A post carries either images or one video. The upload is re-encoded
-- server-side by ffmpeg (`core/video.py`: 720p, up to 60fps, H.264/AAC, at most 30MB) in a
-- background task, so the row is written first as `processing` and only gets `video_url` and
-- its poster frame once the encode lands. `ready` posts show to everyone; `processing` and
-- `failed` ones only to their author. `video_status` is null on posts without a video.
alter table public.posts
  add column video_url text,
  add column video_poster_url text,
  add column video_status text check (video_status in ('processing', 'ready', 'failed'));

-- The encoded clips. The 30MB limit matches the encoder's output budget; posters go to
-- `post-images` as WebP like every other post image.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  ('post-videos', 'post-videos', true, 31457280, array['video/mp4'])
on conflict (id) do nothing;
