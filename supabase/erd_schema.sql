-- SquadUp - consolidated schema snapshot for ERD tools (drawDB, dbdiagram, etc).
-- Generated from supabase/migrations/*.sql, flattened to the current state of every table.
-- Not a migration: RLS policies, triggers, RPC functions and storage buckets are omitted,
-- and the auth.users foreign key on public.users is left as a comment so the file imports
-- standalone.

-- Enums ---------------------------------------------------------------------

create type user_role as enum ('user', 'admin');
create type pal_application_status as enum ('pending_review', 'approved', 'rejected');
create type payout_schedule as enum ('weekly', 'bi_weekly', 'monthly');
create type booking_status as enum ('pending', 'accepted', 'declined', 'completed');
create type payment_method as enum ('coins', 'card');
create type cancellation_refund_option as enum ('full', 'partial', 'none');
create type dispute_requested_outcome as enum ('full_refund', 'partial_refund', 'reporting');
create type dispute_status as enum ('open', 'investigating', 'resolved', 'refunded');
create type notification_type as enum
  ('booking', 'message', 'review', 'payout', 'follow', 'service', 'gift', 'streak', 'moderation');
create type feed_category as enum ('games', 'chilling', 'clips');
create type post_kind as enum ('user', 'status');
create type saved_item_kind as enum ('post', 'service');
create type subscription_billing_cycle as enum ('monthly', 'quarterly');
create type subscription_status as enum ('active', 'cancelled');
create type wallet_transaction_kind as enum ('topup', 'order', 'refund', 'payout', 'tip');
create type wallet_transaction_status as enum ('completed', 'pending', 'blocked');
create type withdrawal_status as enum ('requested', 'paid', 'in_progress', 'rejected');
create type flagged_player_status as enum ('pending', 'reviewing', 'actioned', 'dismissed');
create type album_item_kind as enum ('clip', 'screenshot');
create type review_sentiment as enum ('positive', 'neutral', 'negative');

-- Accounts ------------------------------------------------------------------
-- One account browses and books as a user and can also carry its own Pal profile
-- (`players`), additive rather than exclusive.

create table users (
  id uuid primary key, -- references auth.users (id) on delete cascade
  email text not null unique,
  handle text unique,
  display_name text,
  phone text,
  country text,
  role user_role not null default 'user',
  onboarding_complete boolean not null default false,
  coin_balance integer not null default 0,
  posts_count integer not null default 0,
  followers_count integer not null default 0,
  following_count integer not null default 0,
  created_at timestamptz not null default now()
);

create table players (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users (id) on delete cascade,
  display_name text not null,
  avatar_url text,
  tagline text,
  bio text,
  timezone text,
  language text,
  tier text,
  highlight_badge text,
  subscribe_label text,
  games text[] not null default '{}',
  rank text,
  role text,
  languages text[] not null default '{}',
  price_per_hour numeric(10, 2),
  rating numeric(3, 2),
  review_count integer not null default 0,
  online boolean not null default false,
  is_new boolean not null default true,
  status pal_application_status not null default 'approved',
  is_banned boolean not null default false,
  highlighted_service_id uuid,
  payout_schedule payout_schedule not null default 'weekly',
  id_front_url text,
  id_back_url text,
  rank_verification_url text,
  created_at timestamptz not null default now()
);

create index players_user_id_idx on players (user_id);
create index players_status_is_banned_idx on players (status, is_banned);

create table user_blocks (
  id uuid primary key default gen_random_uuid(),
  blocker_id uuid not null references users (id) on delete cascade,
  blocked_id uuid not null references users (id) on delete cascade,
  created_at timestamptz not null default now(),
  constraint user_blocks_no_self check (blocker_id <> blocked_id),
  constraint user_blocks_unique unique (blocker_id, blocked_id)
);

create index user_blocks_blocker_id_idx on user_blocks (blocker_id);
create index user_blocks_blocked_id_idx on user_blocks (blocked_id);

create table active_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users (id) on delete cascade,
  device text,
  location text,
  last_active_at timestamptz not null default now(),
  is_current boolean not null default false,
  created_at timestamptz not null default now()
);

create index active_sessions_user_id_idx on active_sessions (user_id);

-- Services ------------------------------------------------------------------

create table services (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references players (id) on delete cascade,
  name text not null,
  description text,
  cover_image_url text,
  styles text[] not null default '{}',
  platforms text[] not null default '{}',
  whats_included text[] not null default '{}',
  avg_response_time text,
  rating numeric(3, 2),
  served_count integer not null default 0,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create index services_player_id_idx on services (player_id);

alter table players
  add constraint players_highlighted_service_id_fkey
  foreign key (highlighted_service_id) references services (id) on delete set null;

create table service_pricing_options (
  id uuid primary key default gen_random_uuid(),
  service_id uuid not null references services (id) on delete cascade,
  label text not null,
  price_coins integer not null default 0,
  price_unit text not null,
  sort_order integer not null default 0,
  created_at timestamptz not null default now()
);

create index service_pricing_options_service_id_idx on service_pricing_options (service_id);

create table service_promotions (
  id uuid primary key default gen_random_uuid(),
  service_id uuid not null references services (id) on delete cascade,
  label text not null,
  discount_type text not null check (discount_type in ('percent_off', 'flat_off', 'first_order_free')),
  discount_value numeric(10, 2),
  active boolean not null default true,
  starts_at timestamptz,
  ends_at timestamptz,
  created_at timestamptz not null default now()
);

create index service_promotions_service_id_idx on service_promotions (service_id);

-- Pal profile: album and wishlist -------------------------------------------

create table album_items (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references players (id) on delete cascade,
  kind album_item_kind not null,
  label text,
  media_url text,
  views integer not null default 0,
  likes integer not null default 0,
  shares integer not null default 0,
  duration_seconds integer,
  created_at timestamptz not null default now()
);

create index album_items_player_id_idx on album_items (player_id);

create table wish_items (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references players (id) on delete cascade,
  service_id uuid references services (id) on delete set null,
  title text not null,
  game text,
  type text,
  price_coins integer not null default 0,
  saved boolean not null default true,
  created_at timestamptz not null default now()
);

create index wish_items_player_id_idx on wish_items (player_id);

-- Bookings ------------------------------------------------------------------

create table addons (
  id uuid primary key default gen_random_uuid(),
  label text not null,
  price_coins integer not null default 0,
  created_at timestamptz not null default now()
);

create table bookings (
  id uuid primary key default gen_random_uuid(),
  order_number text not null unique,
  player_id uuid not null references players (id) on delete cascade,
  service_id uuid not null references services (id) on delete cascade,
  user_id uuid not null references users (id) on delete cascade,
  status booking_status not null default 'pending',
  service_type_label text not null,
  price_coins integer not null default 0,
  price_unit text not null,
  quantity integer not null default 1,
  promo_label text,
  subtotal_coins integer not null default 0,
  addons_coins integer not null default 0,
  discount_coins integer not null default 0,
  total_coins integer not null default 0,
  commission_pct numeric not null default 0,
  commission_coins integer not null default 0,
  payment_method payment_method not null default 'coins',
  scheduled_for timestamptz,
  created_at timestamptz not null default now()
);

create index bookings_player_id_idx on bookings (player_id);
create index bookings_user_id_idx on bookings (user_id);
create index bookings_status_idx on bookings (status);
create index bookings_status_created_at_idx on bookings (status, created_at);

-- Each addon is snapshotted at booking time (label and price captured, not just referenced).
create table booking_addons (
  id uuid primary key default gen_random_uuid(),
  booking_id uuid not null references bookings (id) on delete cascade,
  addon_id uuid not null references addons (id),
  label text not null,
  price_coins integer not null default 0
);

create index booking_addons_booking_id_idx on booking_addons (booking_id);

create table order_cancellations (
  id uuid primary key default gen_random_uuid(),
  booking_id uuid not null references bookings (id) on delete cascade,
  cancelled_by uuid not null references users (id) on delete cascade,
  reason text not null,
  refund_option cancellation_refund_option not null,
  refund_coins integer not null default 0,
  note text,
  created_at timestamptz not null default now()
);

create index order_cancellations_booking_id_idx on order_cancellations (booking_id);

-- Backs both the buyer's report-an-issue flow and the admin Disputes tab.
create table order_disputes (
  id uuid primary key default gen_random_uuid(),
  booking_id uuid not null references bookings (id) on delete cascade,
  reported_by uuid not null references users (id) on delete cascade,
  reason text not null,
  requested_outcome dispute_requested_outcome not null,
  refund_coins integer,
  note text,
  attachment_urls text[] not null default '{}',
  status dispute_status not null default 'open',
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

create index order_disputes_booking_id_idx on order_disputes (booking_id);
create index order_disputes_status_idx on order_disputes (status);

-- Reviews -------------------------------------------------------------------

create table reviews (
  id uuid primary key default gen_random_uuid(),
  service_id uuid not null references services (id) on delete cascade,
  booking_id uuid references bookings (id) on delete set null,
  author_id uuid not null references users (id) on delete cascade,
  rating integer not null check (rating between 1 and 5),
  text text,
  sentiment review_sentiment not null default 'neutral',
  highlights text[] not null default '{}',
  tip_coins integer not null default 0 check (tip_coins >= 0),
  created_at timestamptz not null default now()
);

create index reviews_service_id_idx on reviews (service_id);
create unique index reviews_booking_id_key on reviews (booking_id) where booking_id is not null;

-- Messages ------------------------------------------------------------------
-- One shared thread row per pair of accounts; mute and delete are per participant.

create table message_threads (
  id uuid primary key default gen_random_uuid(),
  user_a_id uuid not null references users (id) on delete cascade,
  user_b_id uuid not null references users (id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (user_a_id, user_b_id)
);

create table messages (
  id uuid primary key default gen_random_uuid(),
  thread_id uuid not null references message_threads (id) on delete cascade,
  sender_id uuid not null references users (id) on delete cascade,
  body text not null default '',
  image_url text,
  read_at timestamptz,
  created_at timestamptz not null default now()
);

create index messages_thread_id_idx on messages (thread_id);
create index messages_thread_id_created_at_idx on messages (thread_id, created_at desc);
create index messages_unread_idx on messages (thread_id, sender_id) where read_at is null;

create table message_thread_states (
  thread_id uuid not null references message_threads (id) on delete cascade,
  user_id uuid not null references users (id) on delete cascade,
  muted boolean not null default false,
  deleted_at timestamptz,
  primary key (thread_id, user_id)
);

-- Feed ----------------------------------------------------------------------
-- Posts and follows hang off `users`, so any account (Pal or buyer) can post and be followed.

create table posts (
  id uuid primary key default gen_random_uuid(),
  author_id uuid not null references users (id) on delete cascade,
  text text,
  image_url text,
  image_urls text[] not null default '{}',
  category feed_category not null default 'games',
  kind post_kind not null default 'user',
  tag text,
  likes_count integer not null default 0,
  comments_count integer not null default 0,
  created_at timestamptz not null default now()
);

create index posts_author_id_idx on posts (author_id);
create index posts_tag_idx on posts (tag) where tag is not null;

create table comments (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references posts (id) on delete cascade,
  author_id uuid not null references users (id) on delete cascade,
  parent_comment_id uuid references comments (id) on delete cascade,
  text text not null,
  likes_count integer not null default 0,
  created_at timestamptz not null default now()
);

create index comments_post_id_idx on comments (post_id);

create table post_likes (
  user_id uuid not null references users (id) on delete cascade,
  post_id uuid not null references posts (id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, post_id)
);

create table comment_likes (
  user_id uuid not null references users (id) on delete cascade,
  comment_id uuid not null references comments (id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, comment_id)
);

create table follows (
  follower_id uuid not null references users (id) on delete cascade,
  followed_id uuid not null references users (id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (follower_id, followed_id),
  constraint follows_no_self_follow check (follower_id <> followed_id)
);

create table saved_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users (id) on delete cascade,
  kind saved_item_kind not null,
  post_id uuid references posts (id) on delete cascade,
  service_id uuid references services (id) on delete cascade,
  created_at timestamptz not null default now(),
  constraint saved_items_kind_target_check check (
    (kind = 'post' and post_id is not null and service_id is null)
    or (kind = 'service' and service_id is not null and post_id is null)
  ),
  unique (user_id, post_id),
  unique (user_id, service_id)
);

create index saved_items_user_id_idx on saved_items (user_id);

-- Notifications -------------------------------------------------------------

create table notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users (id) on delete cascade,
  type notification_type not null,
  message text not null,
  thread_id uuid references message_threads (id) on delete set null,
  read boolean not null default false,
  created_at timestamptz not null default now()
);

create index notifications_user_id_idx on notifications (user_id);

-- Subscriptions -------------------------------------------------------------

create table subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users (id) on delete cascade,
  player_id uuid not null references players (id) on delete cascade,
  service_id uuid references services (id) on delete set null,
  billing_cycle subscription_billing_cycle not null,
  renews_on date not null,
  price_coins integer not null default 0,
  status subscription_status not null default 'active',
  created_at timestamptz not null default now()
);

create index subscriptions_user_id_idx on subscriptions (user_id);
create index subscriptions_player_id_idx on subscriptions (player_id);

-- Wallet and payouts --------------------------------------------------------

create table topup_packages (
  id uuid primary key default gen_random_uuid(),
  coins integer not null,
  price_usd numeric(10, 2) not null,
  bonus_coins integer not null default 0,
  is_base_rate boolean not null default false,
  created_at timestamptz not null default now()
);

create table payout_methods (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references players (id) on delete cascade,
  brand text not null,
  label text not null,
  detail text,
  is_default boolean not null default false,
  created_at timestamptz not null default now()
);

create index payout_methods_player_id_idx on payout_methods (player_id);

create table withdrawals (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references players (id) on delete cascade,
  payout_method_id uuid references payout_methods (id) on delete set null,
  coins integer not null,
  fee_coins integer not null default 0,
  reference text,
  status withdrawal_status not null default 'requested',
  reviewed_at timestamptz,
  created_at timestamptz not null default now()
);

create index withdrawals_player_id_idx on withdrawals (player_id);
create index withdrawals_status_idx on withdrawals (status);
create unique index withdrawals_reference_key on withdrawals (reference);

create table wallet_transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users (id) on delete cascade,
  kind wallet_transaction_kind not null,
  status wallet_transaction_status not null default 'completed',
  label text not null,
  detail text,
  coins integer not null,
  booking_id uuid references bookings (id) on delete set null,
  withdrawal_id uuid references withdrawals (id) on delete set null,
  payment_reference text unique,
  created_at timestamptz not null default now()
);

create index wallet_transactions_user_id_idx on wallet_transactions (user_id);

create table payway_topups (
  tran_id text primary key,
  user_id uuid not null references users (id) on delete cascade,
  package_id uuid references topup_packages (id) on delete set null,
  method text not null default 'card' check (method in ('card', 'khqr')),
  coins integer not null,
  amount_usd numeric(10, 2) not null,
  status text not null default 'pending' check (status in ('pending', 'paid')),
  created_at timestamptz not null default now(),
  paid_at timestamptz
);

create index payway_topups_user_id_idx on payway_topups (user_id, created_at desc);

create table payment_cards (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users (id) on delete cascade,
  brand text not null,
  label text not null,
  detail text,
  is_default boolean not null default false,
  created_at timestamptz not null default now()
);

create index payment_cards_user_id_idx on payment_cards (user_id);

-- Admin ---------------------------------------------------------------------
-- Disputes reuse `order_disputes`; this table only backs the Flagged Players tab.

create table admin_flags (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references players (id) on delete cascade,
  reason text not null,
  details text,
  reported_by uuid references users (id) on delete set null,
  report_count integer not null default 1,
  status flagged_player_status not null default 'pending',
  created_at timestamptz not null default now()
);

create index admin_flags_player_id_idx on admin_flags (player_id);
create index admin_flags_status_idx on admin_flags (status);
