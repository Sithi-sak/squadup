-- Posts can carry several images now (the composer accepts a multi-pick, `FeedPostCard.vue`
-- lays them out as a collage). `image_url` stays, always holding the first image, so everything
-- reading it today (saved items, `has_image`, older rows) keeps working untouched.

alter table public.posts
  add column image_urls text[] not null default '{}';

update public.posts
  set image_urls = array[image_url]
  where image_url is not null;
