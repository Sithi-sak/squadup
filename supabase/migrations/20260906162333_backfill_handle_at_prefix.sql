-- Handles were always meant to carry a leading "@" (auto-generated Pal handles and every seeded
-- mock already do), but `PATCH /users/me` stored the Settings "Username" field verbatim until
-- now, so accounts that set a username by hand ended up without the "@". Backfill those in place.
update public.users
set handle = '@' || handle
where handle is not null and handle not like '@%';
