-- Initial schema for SquadUp (CHECKPOINT.md 2.3).
-- Column shapes are matched against frontend/src/mocks/*.ts and frontend/src/stores/*.ts.
-- RLS is enabled on every table with no policies yet: service_role (used by the FastAPI
-- backend, see backend/src/backend/core/supabase.py) bypasses RLS entirely, so the API keeps
-- working; anon/authenticated get zero access until policies are added per-feature in Phase 3
-- alongside real Supabase Auth (2.5).

create extension if not exists pgcrypto;

-- Enums -----------------------------------------------------------------

create type user_role as enum ('user', 'admin');
create type booking_status as enum ('pending', 'accepted', 'declined', 'completed');
create type payment_method as enum ('coins', 'card');
create type cancellation_refund_option as enum ('full', 'partial', 'none');
create type dispute_requested_outcome as enum ('full_refund', 'partial_refund', 'reporting');
create type dispute_status as enum ('open', 'investigating', 'resolved', 'refunded');
create type notification_type as enum
  ('booking', 'message', 'review', 'payout', 'follow', 'service', 'gift', 'streak');
create type feed_category as enum ('games', 'chilling', 'clips');
create type saved_item_kind as enum ('post', 'service');
create type subscription_billing_cycle as enum ('monthly', 'quarterly');
create type subscription_status as enum ('active', 'cancelled');
create type wallet_transaction_kind as enum ('topup', 'order', 'refund', 'payout');
create type wallet_transaction_status as enum ('completed', 'pending', 'blocked');
create type withdrawal_status as enum ('paid', 'in_progress');
create type flagged_player_status as enum ('pending', 'reviewing', 'actioned', 'dismissed');
create type album_item_kind as enum ('clip', 'screenshot');
create type payout_schedule as enum ('weekly', 'bi_weekly', 'monthly');
create type review_sentiment as enum ('positive', 'neutral', 'negative');

-- Users & Players ---------------------------------------------------------
-- One account can browse/book as a user and also carry its own Pal profile (additive, not
-- exclusive) — see CHECKPOINT.md's "Account model" note. `players.user_id` is nullable because
-- seed/demo Pals (mocks/players.ts p1..p8) aren't linked to any account.

create table public.users (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null unique,
  display_name text,
  role user_role not null default 'user',
  onboarding_complete boolean not null default false,
  coin_balance integer not null default 0,
  created_at timestamptz not null default now()
);

create table public.players (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users (id) on delete set null,
  handle text unique,
  display_name text not null,
  avatar_url text,
  tagline text,
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
  posts_count integer not null default 0,
  followers_count integer not null default 0,
  following_count integer not null default 0,
  highlighted_service_id uuid,
  payout_schedule payout_schedule not null default 'weekly',
  created_at timestamptz not null default now()
);

create index players_user_id_idx on public.players (user_id);

-- Services ----------------------------------------------------------------
-- `services` covers both the sidebar listing and the detail panel from PlayerProfile/
-- PlayerServiceDetail (one row per service, keyed the same way the frontend already does).

create table public.services (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references public.players (id) on delete cascade,
  name text not null,
  description text,
  styles text[] not null default '{}',
  platforms text[] not null default '{}',
  whats_included text[] not null default '{}',
  avg_response_time text,
  rating numeric(3, 2),
  served_count integer not null default 0,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create index services_player_id_idx on public.services (player_id);

alter table public.players
  add constraint players_highlighted_service_id_fkey
  foreign key (highlighted_service_id) references public.services (id) on delete set null;

-- One row per `ServiceTypeOption` (the pricing/service-type list on Service Detail).
create table public.service_pricing_options (
  id uuid primary key default gen_random_uuid(),
  service_id uuid not null references public.services (id) on delete cascade,
  label text not null,
  price_coins integer not null default 0,
  price_unit text not null,
  sort_order integer not null default 0,
  created_at timestamptz not null default now()
);

create index service_pricing_options_service_id_idx on public.service_pricing_options (service_id);

-- Structured backing for the `promoBadge` text shown on services/pricing options
-- (e.g. "10% Off", "1st Order Free").
create table public.service_promotions (
  id uuid primary key default gen_random_uuid(),
  service_id uuid not null references public.services (id) on delete cascade,
  label text not null,
  discount_type text not null check (discount_type in ('percent_off', 'flat_off', 'first_order_free')),
  discount_value numeric(10, 2),
  active boolean not null default true,
  starts_at timestamptz,
  ends_at timestamptz,
  created_at timestamptz not null default now()
);

create index service_promotions_service_id_idx on public.service_promotions (service_id);

-- Player Profile: Album & Wish tabs ---------------------------------------

create table public.album_items (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references public.players (id) on delete cascade,
  kind album_item_kind not null,
  label text,
  media_url text,
  views integer not null default 0,
  likes integer not null default 0,
  shares integer not null default 0,
  duration_seconds integer,
  created_at timestamptz not null default now()
);

create index album_items_player_id_idx on public.album_items (player_id);

create table public.wish_items (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references public.players (id) on delete cascade,
  service_id uuid references public.services (id) on delete set null,
  title text not null,
  game text,
  type text,
  price_coins integer not null default 0,
  saved boolean not null default true,
  created_at timestamptz not null default now()
);

create index wish_items_player_id_idx on public.wish_items (player_id);

-- Bookings ------------------------------------------------------------------
-- `addons` is a flat, platform-wide catalog for now, matching mocks/bookings.ts's
-- `mockAddons` (see CHECKPOINT.md's Booking flow note — per-Pal add-ons is a 3.1 decision).

create table public.addons (
  id uuid primary key default gen_random_uuid(),
  label text not null,
  price_coins integer not null default 0,
  created_at timestamptz not null default now()
);

create table public.bookings (
  id uuid primary key default gen_random_uuid(),
  order_number text not null unique,
  player_id uuid not null references public.players (id),
  service_id uuid not null references public.services (id),
  user_id uuid not null references public.users (id),
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
  payment_method payment_method not null default 'coins',
  scheduled_for timestamptz,
  created_at timestamptz not null default now()
);

create index bookings_player_id_idx on public.bookings (player_id);
create index bookings_user_id_idx on public.bookings (user_id);
create index bookings_status_idx on public.bookings (status);

-- Snapshot of each addon at booking time (label/price captured, not just referenced), matching
-- the embedded `BookingAddon[]` shape on `Booking.addons`.
create table public.booking_addons (
  id uuid primary key default gen_random_uuid(),
  booking_id uuid not null references public.bookings (id) on delete cascade,
  addon_id uuid not null references public.addons (id),
  label text not null,
  price_coins integer not null default 0
);

create index booking_addons_booking_id_idx on public.booking_addons (booking_id);

create table public.order_cancellations (
  id uuid primary key default gen_random_uuid(),
  booking_id uuid not null references public.bookings (id) on delete cascade,
  cancelled_by uuid not null references public.users (id),
  reason text not null,
  refund_option cancellation_refund_option not null,
  refund_coins integer not null default 0,
  note text,
  created_at timestamptz not null default now()
);

create index order_cancellations_booking_id_idx on public.order_cancellations (booking_id);

-- Backs both the buyer-facing "report an issue" flow (Order Detail / RefundModal) and the
-- admin Disputes tab (mocks/admin.ts's `AdminDispute`) — one table instead of two copies of the
-- same case, since the mock's `AdminDispute` fields are all derivable by joining back to
-- `bookings`/`players`/`users`.
create table public.order_disputes (
  id uuid primary key default gen_random_uuid(),
  booking_id uuid not null references public.bookings (id) on delete cascade,
  reported_by uuid not null references public.users (id),
  reason text not null,
  requested_outcome dispute_requested_outcome not null,
  refund_coins integer,
  note text,
  attachment_urls text[] not null default '{}',
  status dispute_status not null default 'open',
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

create index order_disputes_booking_id_idx on public.order_disputes (booking_id);
create index order_disputes_status_idx on public.order_disputes (status);

-- Messages --------------------------------------------------------------
-- One thread per pair of users (there's one inbox per account, not a separate buyer/Pal
-- persona — see CHECKPOINT.md's Messages note).

create table public.message_threads (
  id uuid primary key default gen_random_uuid(),
  user_a_id uuid not null references public.users (id),
  user_b_id uuid not null references public.users (id),
  created_at timestamptz not null default now(),
  unique (user_a_id, user_b_id)
);

create table public.messages (
  id uuid primary key default gen_random_uuid(),
  thread_id uuid not null references public.message_threads (id) on delete cascade,
  sender_id uuid not null references public.users (id),
  body text not null,
  read_at timestamptz,
  created_at timestamptz not null default now()
);

create index messages_thread_id_idx on public.messages (thread_id);

-- Reviews -----------------------------------------------------------------

create table public.reviews (
  id uuid primary key default gen_random_uuid(),
  service_id uuid not null references public.services (id) on delete cascade,
  booking_id uuid references public.bookings (id) on delete set null,
  author_id uuid not null references public.users (id),
  rating integer not null check (rating between 1 and 5),
  text text,
  sentiment review_sentiment not null default 'neutral',
  created_at timestamptz not null default now()
);

create index reviews_service_id_idx on public.reviews (service_id);

-- Feed: posts, comments, follows, saved items ------------------------------

create table public.posts (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references public.players (id) on delete cascade,
  text text,
  image_url text,
  category feed_category not null default 'games',
  likes_count integer not null default 0,
  comments_count integer not null default 0,
  created_at timestamptz not null default now()
);

create index posts_player_id_idx on public.posts (player_id);

create table public.comments (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references public.posts (id) on delete cascade,
  author_id uuid not null references public.users (id),
  parent_comment_id uuid references public.comments (id) on delete cascade,
  text text not null,
  likes_count integer not null default 0,
  created_at timestamptz not null default now()
);

create index comments_post_id_idx on public.comments (post_id);

create table public.follows (
  follower_id uuid not null references public.users (id) on delete cascade,
  player_id uuid not null references public.players (id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (follower_id, player_id)
);

create table public.saved_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  kind saved_item_kind not null,
  post_id uuid references public.posts (id) on delete cascade,
  service_id uuid references public.services (id) on delete cascade,
  created_at timestamptz not null default now(),
  constraint saved_items_kind_target_check check (
    (kind = 'post' and post_id is not null and service_id is null)
    or (kind = 'service' and service_id is not null and post_id is null)
  ),
  unique (user_id, post_id),
  unique (user_id, service_id)
);

create index saved_items_user_id_idx on public.saved_items (user_id);

-- Notifications -------------------------------------------------------------

create table public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  type notification_type not null,
  message text not null,
  read boolean not null default false,
  created_at timestamptz not null default now()
);

create index notifications_user_id_idx on public.notifications (user_id);

-- Subscriptions ---------------------------------------------------------

create table public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id),
  player_id uuid not null references public.players (id),
  service_id uuid references public.services (id) on delete set null,
  billing_cycle subscription_billing_cycle not null,
  renews_on date not null,
  price_coins integer not null default 0,
  status subscription_status not null default 'active',
  created_at timestamptz not null default now()
);

create index subscriptions_user_id_idx on public.subscriptions (user_id);
create index subscriptions_player_id_idx on public.subscriptions (player_id);

-- Wallet: transactions, top-up packages, payouts, withdrawals -------------

create table public.topup_packages (
  id uuid primary key default gen_random_uuid(),
  coins integer not null,
  price_usd numeric(10, 2) not null,
  bonus_coins integer not null default 0,
  is_base_rate boolean not null default false,
  created_at timestamptz not null default now()
);

create table public.wallet_transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  kind wallet_transaction_kind not null,
  status wallet_transaction_status not null default 'completed',
  label text not null,
  detail text,
  coins integer not null,
  booking_id uuid references public.bookings (id) on delete set null,
  created_at timestamptz not null default now()
);

create index wallet_transactions_user_id_idx on public.wallet_transactions (user_id);

create table public.payout_methods (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references public.players (id) on delete cascade,
  brand text not null,
  label text not null,
  detail text,
  is_default boolean not null default false,
  created_at timestamptz not null default now()
);

create index payout_methods_player_id_idx on public.payout_methods (player_id);

create table public.withdrawals (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references public.players (id),
  payout_method_id uuid references public.payout_methods (id) on delete set null,
  coins integer not null,
  fee_coins integer not null default 0,
  status withdrawal_status not null default 'in_progress',
  created_at timestamptz not null default now()
);

create index withdrawals_player_id_idx on public.withdrawals (player_id);

-- Settings: payment cards, active sessions ---------------------------------

create table public.payment_cards (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  brand text not null,
  label text not null,
  detail text,
  is_default boolean not null default false,
  created_at timestamptz not null default now()
);

create index payment_cards_user_id_idx on public.payment_cards (user_id);

create table public.active_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  device text,
  location text,
  last_active_at timestamptz not null default now(),
  is_current boolean not null default false,
  created_at timestamptz not null default now()
);

create index active_sessions_user_id_idx on public.active_sessions (user_id);

-- Admin: flagged players ----------------------------------------------------
-- Disputes reuse `order_disputes` above; this table is only for the Flagged Players tab.

create table public.admin_flags (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references public.players (id) on delete cascade,
  reason text not null,
  details text,
  reported_by uuid references public.users (id),
  report_count integer not null default 1,
  status flagged_player_status not null default 'pending',
  created_at timestamptz not null default now()
);

create index admin_flags_player_id_idx on public.admin_flags (player_id);
create index admin_flags_status_idx on public.admin_flags (status);

-- Row Level Security --------------------------------------------------------
-- Enabled everywhere with no policies yet: service_role (backend) bypasses RLS and keeps
-- working; anon/authenticated get zero access until per-feature policies land in Phase 3
-- alongside real Supabase Auth (2.5).

alter table public.users enable row level security;
alter table public.players enable row level security;
alter table public.services enable row level security;
alter table public.service_pricing_options enable row level security;
alter table public.service_promotions enable row level security;
alter table public.album_items enable row level security;
alter table public.wish_items enable row level security;
alter table public.addons enable row level security;
alter table public.bookings enable row level security;
alter table public.booking_addons enable row level security;
alter table public.order_cancellations enable row level security;
alter table public.order_disputes enable row level security;
alter table public.message_threads enable row level security;
alter table public.messages enable row level security;
alter table public.reviews enable row level security;
alter table public.posts enable row level security;
alter table public.comments enable row level security;
alter table public.follows enable row level security;
alter table public.saved_items enable row level security;
alter table public.notifications enable row level security;
alter table public.subscriptions enable row level security;
alter table public.topup_packages enable row level security;
alter table public.wallet_transactions enable row level security;
alter table public.payout_methods enable row level security;
alter table public.withdrawals enable row level security;
alter table public.payment_cards enable row level security;
alter table public.active_sessions enable row level security;
alter table public.admin_flags enable row level security;
