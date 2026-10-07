-- 4.77a: post reports. `admin_flags` is keyed on `player_id`, and any user can post, so feed
-- posts get their own queue.
--
-- `author_id` and `post_text` are copied from the post when the report is filed. "Remove post"
-- in the admin panel deletes the post, and `post_id` is `set null` rather than cascading so the
-- report (and what was reported) stays in the queue's history after the post is gone.

create table public.post_reports (
  id uuid primary key default gen_random_uuid(),
  post_id uuid references public.posts (id) on delete set null,
  author_id uuid references public.users (id) on delete set null,
  post_text text,
  reason text not null,
  details text,
  reported_by uuid references public.users (id) on delete set null,
  report_count integer not null default 1,
  status flagged_player_status not null default 'pending',
  created_at timestamptz not null default now()
);

create index post_reports_post_id_idx on public.post_reports (post_id);
create index post_reports_status_idx on public.post_reports (status);

-- Same posture as every other table: RLS on with no policies, so anon/authenticated get nothing
-- and the service-role backend keeps working.
alter table public.post_reports enable row level security;
