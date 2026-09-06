-- Become a Pal step 1 and Settings' Account tab both collect phone/country, but neither ever
-- had a real column to land in - the fields were mock-only local state. Adding them to
-- `public.users` (row-level RLS already covers new columns, no policy change needed) lets both
-- surfaces read/write the same account-level values instead of each other's throwaway drafts.
alter table public.users
  add column phone text,
  add column country text;
