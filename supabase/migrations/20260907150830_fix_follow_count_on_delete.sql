-- `follows` rows are ON DELETE CASCADE on both sides (unify_social_graph.sql), so deleting a
-- user (e.g. seed_demo_data.py's `teardown`, or any other account deletion) silently removes
-- their `follows` rows without ever touching the other side's denormalized
-- `users.followers_count`/`following_count` - those only get recomputed inside the
-- follow_user/unfollow_user endpoints (backend/src/backend/routers/feed.py), which a raw
-- cascade delete never calls. Add a trigger so the counts stay correct no matter how a
-- `follows` row disappears, then backfill the counts that are already stale.

create or replace function public.handle_follow_delete() returns trigger as $$
begin
  update public.users set following_count = greatest(following_count - 1, 0) where id = old.follower_id;
  update public.users set followers_count = greatest(followers_count - 1, 0) where id = old.followed_id;
  return old;
end;
$$ language plpgsql security definer;

create trigger on_follow_deleted
  after delete on public.follows
  for each row execute function public.handle_follow_delete();

update public.users u
set following_count = coalesce((select count(*) from public.follows f where f.follower_id = u.id), 0),
    followers_count = coalesce((select count(*) from public.follows f where f.followed_id = u.id), 0);
