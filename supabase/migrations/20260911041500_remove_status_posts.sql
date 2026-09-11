-- All system-generated status posts (new follower, Pal verified, review left, booking
-- completed) cluttered the feed with low-value activity. The app no longer creates any of
-- these (feed_events.post_status and its callers were removed) - clean out what's left.
delete from public.posts
where kind = 'status';
