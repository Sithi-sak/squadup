-- `_refresh_post`/`_refresh_comment` (routers/feed.py) used to do a `SELECT count(*)` then a
-- separate `UPDATE ... set likes_count`, two round trips with no locking. Two overlapping
-- like/unlike requests on the same post (e.g. a fast double-click) could interleave between
-- those two statements and leave `likes_count` permanently wrong - not just a UI flicker, a
-- corrupted stored value. Recomputing and writing the count in one atomic statement makes the
-- second of two concurrent calls block on Postgres's row lock and then re-read the true
-- committed count, instead of racing on a value read in application code.
create function public.refresh_post_likes_count(target_post_id uuid)
returns integer
language sql
security definer
set search_path = public
as $$
  update public.posts
  set likes_count = (select count(*) from public.post_likes where post_id = target_post_id)
  where id = target_post_id
  returning likes_count;
$$;

create function public.refresh_comment_likes_count(target_comment_id uuid)
returns integer
language sql
security definer
set search_path = public
as $$
  update public.comments
  set likes_count = (select count(*) from public.comment_likes where comment_id = target_comment_id)
  where id = target_comment_id
  returning likes_count;
$$;
