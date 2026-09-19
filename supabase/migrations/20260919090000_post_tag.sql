-- The composer's "Tag a game or service" chips are free text (a game name from `data/games.ts`
-- or one of the author's own service names), which `posts.category` can't hold: that column is
-- the `feed_category` enum ('games' | 'chilling' | 'clips'), a post *type*, and writing a game
-- name into it fails with `invalid input value for enum feed_category`. So tags get their own
-- nullable column; `category` keeps its existing meaning and default.

alter table public.posts
  add column tag text;

create index posts_tag_idx on public.posts (tag) where tag is not null;
