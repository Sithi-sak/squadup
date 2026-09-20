-- Settings' Profile tab has shown Headline and Bio inputs since 1.x, but only Headline had a
-- column behind it (`players.tagline`) and neither was ever saved - both were local `ref()`s
-- that reset on tab switch. `bio` is the longer "About" paragraph shown under the tagline on a
-- Pal's profile; `tagline` stays the one-liner browse cards render.
alter table public.players
  add column bio text;
