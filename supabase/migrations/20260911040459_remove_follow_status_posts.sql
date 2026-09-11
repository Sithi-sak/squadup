-- "Started following X." status posts fired on every follow and quickly buried the feed under
-- low-value activity. The app no longer creates them (see follow_user in routers/feed.py) -
-- clean up the ones already seeded/created so they stop showing up.
delete from public.posts
where kind = 'status' and text like 'Started following %';
