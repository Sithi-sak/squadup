# SquadUp — Build Checkpoint

This file is the single source of truth for build progress. Work **one task at a time**:
pick the next unchecked box under "Next Up", implement it, check it off, then stop and
return here before starting the next one. Don't jump ahead or batch multiple tasks.

**Stack correction from the original recap:** UI is built with **Tailwind CSS v4 +
Nuxt UI** (Vue install path, not the Nuxt framework — this is a Vite app) and
`@phosphor-icons/vue` for icons, all in `frontend/package.json`. Nuxt UI is wired up
via the `@nuxt/ui/vite` plugin in `vite.config.ts` (component auto-import,
`colorMode: false` since this app is dark-only) and `@nuxt/ui/vue-plugin` in
`main.ts`. `App.vue` root is wrapped in `<UApp>`. Element Plus was removed.

**Brand colors:** primary `#059669`, accent `#6EE7B7`, ink wordmark `#064E3B`,
background `#0F172A`, dark `#0A0A0A` — dark theme only (no light/dark toggle).
Tailwind v4's stock `emerald`/`slate`/`neutral` scales are OKLCH-based and don't
reproduce these hexes exactly, so a custom `brand` color ramp is defined in
`frontend/src/styles/theme.css` (`@theme static`), anchored exactly at the given
hexes (300 = accent, 600 = primary, 900 = ink; other stops interpolated). Nuxt UI's
semantic `primary` points at it via `colors: { primary: 'brand', neutral: 'slate' }`
in the `@nuxt/ui/vite` plugin options (`vite.config.ts`). `bg` and `dark` are flat
tokens (`--color-squadup-bg`, `--color-squadup-dark`) used directly, e.g.
`bg-squadup-bg` / `bg-squadup-dark` utility classes — not part of a shade scale.
Brand logo lives at `frontend/src/assets/brand.svg`, coin icon at
`frontend/src/assets/squadup-coin.svg`. Font is Inter, loaded via Google Fonts
`<link>` in `index.html`.

**Order of operations:** Frontend UI first (static/mock data, no backend calls) →
Backend (FastAPI + Supabase) to wire everything for real → Payment integration
(Stripe/Bakong KHQR). **Amended 2026-08-25:** per user direction, Phase 4 (Payment) is
now done *before* 3.16/3.17 rather than strictly last — Stripe first, Bakong KHQR last
(scope/complexity TBD when reached). ABA PayWay was dropped from scope entirely, it was
never built beyond this line and a throwaway mock label. 3.16 (clean out mocks) and 3.17
(seed script) resume once Phase 4 is done.

**Copy style:** never use em dashes in UI copy (headings, body text, labels,
buttons). Use a comma, period, or rewrite the sentence instead.

**Account model:** a user and a Pal are **additive, not exclusive** — one
account can browse/book as a user and also carry its own Pal profile, matching
the recap's relational `users` + `players` tables (2.3) rather than a single
exclusive role tag. `AuthUser.role` is just `'user' | 'admin'`; `AuthUser.playerId`
links to a `PlayerProfile` (`stores/players.ts`) when the account also has a Pal
profile, mirroring the future `players.user_id → users.id` foreign key. Seed
Pals (`p1`..`p8` in `mocks/players.ts`) are independent marketplace NPCs, not
linked to any mock account. Components should branch on `playerId` presence
(e.g. `AppHeader.vue`'s dashboard link, `FeedSidebar.vue`'s profile card), not
on `role`. Apply this when building Dashboards (1.12/1.13) and wiring real auth
(2.5).

**Booking flow (built for 1.9):** the flow ended up wider than the original
"duration + time picker" plan, driven by `squadup_ui/s2/SERVICE DETAIL.jpg` and
`squadup_ui/s1/{BOOKING,CHECKOUT,ORDER CONFIRMATION}.jpg`. Actual shape: Player
Profile Services tab "Book" → **Service Detail** page (`/players/:id/services/:serviceId`,
new route, not in the original table) → **"Book now"** opens a `BookingModal`
(quantity + add-ons + promo code) → **Continue to checkout** creates a draft
`Booking` in `stores/bookings.ts` and routes to `/checkout/:bookingId` → **Place
order** finalizes payment method/start time and routes to
`/checkout/:bookingId/confirmation` (new route). The old placeholder
`/book/:playerId` route and `BookingView.vue` were removed. Notes for Phase 2/3:
- `Booking` in `stores/bookings.ts` was redesigned around quantity/add-ons/promo/
  payment/scheduling (not the original `durationMinutes` shape) — `mocks/bookings.ts`
  matches the new shape; use it as the reference when designing the `bookings`
  table (2.3) and the create/accept/decline flow (3.4).
- A booking currently goes straight to `status: 'pending'` the moment the modal's
  "Continue to checkout" fires (before "Place order" is even clicked). Decide in
  3.4 whether the backend wants a real draft/cart state distinct from a submitted
  "pending" request, since right now both are collapsed into one client-side object.
- Add-ons (`mocks/bookings.ts` → `mockAddons`) are one flat global list, not
  per-service. Decide whether Pals can configure their own add-ons (3.1) or
  whether a platform-wide list is fine long-term.
- Promo codes are a single hardcoded demo code (`SQUAD10`) plus an auto-applied
  discount parsed from a service type's `promoBadge` string (e.g. `"15% Off"`,
  `"1st Order Free"`). Real promo/coupon logic and "first order" detection need a
  backend rule, not string parsing.
- Order numbers (`SQ-XXXXX`) and booking IDs are generated client-side
  (`Math.random()` / `Date.now()`). Backend must generate both server-side to
  avoid collisions once multiple clients can create bookings.
- Checkout's "Squad Coin balance" option reads `mockCurrentUser.coinBalance`
  directly and computes "left after this order" client-side with no real
  deduction. Wire this to the real wallet once it exists; also decide the
  coin↔real-money exchange rate before Phase 4.
- "Schedule" start time uses `@internationalized/date` + `UInputDate`/`UCalendar`
  (added `@internationalized/date` as an explicit dependency) and converts via
  `getLocalTimeZone()` — i.e. the browser's local zone, not the Pal's profile
  timezone (`PlayerProfile.timezone`, e.g. `"GMT+07:00"`). Pick a canonical
  storage timezone (UTC) and reconcile against the Pal's displayed timezone
  before this is real.
- `WishItem` gained a `serviceId` field so its "Book" button can open the same
  Service Detail page. For `p1`'s mock wishlist several of those links are
  best-effort matches (the wish game doesn't always match the linked service) —
  revisit once wishlist items are backed by real data (3.1) rather than needing
  a service reference at all.

**Messages / dashboard shell (built for 1.11):** the two sides needed different chrome around
the same chat UI — per `squadup_ui/DASHBOARD/MESSAGE.jpg`, a Pal sees Messages inside a
dashboard shell (left rail: Dashboard/Orders/My services/Earnings/Messages/Settings + online
toggle + profile), while a plain user just gets the chat panel under the normal header, no
sidebar. `MessagesView.vue` branches on `mockCurrentUser.playerId` (same convention as
`AppHeader`'s Dashboard button and `FeedSidebar`) to pick one of two wrappers around a shared
`components/messages/MessagesPanel.vue` (thread list + message pane, both sides read/write the
same mock thread data via `stores/messages.ts` — there's one inbox per account, not a separate
buyer/Pal persona). The dashboard shell itself is a new reusable pair,
`components/dashboard/DashboardLayout.vue` + `DashboardSidebar.vue`, meant to be reused as-is by
1.12 Player Dashboard rather than rebuilt. Two notes for 1.12:
- The sidebar's Orders/My services/Earnings items all currently link to the `/dashboard/player`
  placeholder route since those don't have their own routes yet — 1.12 needs to decide whether
  they become real sub-routes or stay as sections/tabs on one dashboard page (the original 1.12
  scope line reads like one page, which conflicts with the mock's separate nav items).
  `/dashboard/player` and `/dashboard/user` were also given `authenticated: true` +
  `hideFooter: true` route meta now (they had neither) so the header/footer render correctly
  once those pages are built.
- `/messages`, `/dashboard/player`, and `/dashboard/user` use a new `hideFooter` route meta
  (`App.vue`) instead of `hideChrome`, since these keep the signed-in header but drop the
  marketing footer. The page height is pinned to `h-[calc(100vh-65px)]` (65px = the header's
  `h-16` plus its 1px `border-b`) so the panel fills the viewport with internal scrolling instead
  of the page scrolling — reuse that exact offset rather than `4rem`, which is 1px short and
  reintroduces a stray scrollbar.

**Pal Dashboard (built for 1.12/1.13):** per `squadup_ui/DASHBOARD.jpg` and
`squadup_ui/DASHBOARD/{EARNINGS,MY SERVICES,ORDERS}.jpg`, the Figma's 4 screens became 4 real
routes (not tabs on one page) so `DashboardSidebar` can deep-link into each: `/dashboard/player`
(overview + incoming orders + earnings-this-week + top services + upcoming schedule),
`/dashboard/player/orders` (full order list, filterable, "View" opens a detail modal),
`/dashboard/player/services` (service cards with an active/paused toggle), and
`/dashboard/player/earnings` (balance, 8-month chart, payout method + history). All four reuse
`DashboardLayout`/`DashboardSidebar` unchanged. `squadup_ui/SETTING.jpg`'s sidebar tab stays
pointed at 1.14. `squadup_ui/CREATE SERVICE.jpg` (the full service creation/edit flow) was **not**
built, it's a separate task, not part of the 5 images this task was scoped against, so "+ New
Service", "Edit", "View stats", "Export", "Withdraw", and "Change payout settings" are all
disabled stub buttons for now.
- The mock account's own Pal profile (`self` in `mocks/playerProfiles.ts`) was upgraded from an
  empty "freshly started Pal" to a fully authored one (4 services matching MY SERVICES.jpg) so
  these pages render populated instead of empty-state. A new `mocks/buyers.ts` (`BuyerSummary`,
  distinct from `mockPlayers`/seed Pals) and `mocks/bookings.ts`'s `mockIncomingBookings` (7
  bookings with `playerId: 'self'`) back Orders/incoming-orders; `mocks/dashboardStats.ts` holds
  the aggregate numbers that aren't derivable from those 7 rows (lifetime earned, response rate,
  payout history). "Top services" on the overview page *is* derived live from
  `mockIncomingBookings` rather than duplicated into the stats mock.
- The mockups show 5 order-status pills (Pending/In progress/Scheduled/Completed/Cancelled) but
  `BookingStatus` only has 4 values. Rather than widen the enum, "Scheduled" is a presentation-only
  derivation in the new `utils/orderStatus.ts`: an `accepted` booking whose `scheduledFor` is still
  in the future. Reuse `orderStatusMeta()` wherever a booking's status is shown as one of these 5
  labels instead of re-deriving it.
- `PlayerServiceListing` (`stores/players.ts`) gained an optional `active?: boolean` for the My
  Services toggle. It's additive, other Pal profiles (`p1`, generic fallback) simply don't set it.
- Orders' "View" opens a `UModal` with the order detail inline rather than routing to
  `/checkout/:bookingId/confirmation` — that page is written from the *buyer's* POV ("Your request
  was sent to {Pal}") and doesn't fit a Pal viewing an order they're fulfilling.

**Settings (built for 1.14):** per `squadup_ui/SETTINGS/*.jpg`, one page (`/settings`) with a
vertical tab nav (`components/settings/SettingsNav.vue`) and six tab components: Profile, Account,
Notifications, Payments, Privacy, Security. Follows the same `isPal` branch as Messages/Dashboard
(`SettingsView.vue`): a Pal gets the full `DashboardLayout` shell (`active="settings"`) with all 6
tabs, default tab "Profile"; a plain user (no `playerId`) gets a lightweight header-only wrapper
with the Pal-only Profile tab dropped, default tab "Account". Three small reusable row components
(`SettingsToggleRow`, `SettingsSelectRow`, `SettingsActionRow`) cover the repeated
label+switch/select/button row shape across tabs instead of duplicating that markup ~30 times.
New fixtures in `mocks/settings.ts` (payment cards, active sessions, phone/country/member-since)
fill gaps `AuthUser`/`PlayerProfile` don't cover; `assets/visa.svg` added for the card row icon.
Matching the "+ New Service" / "+ Withdraw" stub convention from 1.12/1.13, anything that would
need real backend logic ("Save changes", "Edit", "Change", "Enable", "Manage", "Request",
"+ Add card/payout method", "Deactivate", "Delete") is a disabled button. Two things are
interactive purely client-side, no backend needed to make them meaningful locally: Security tab's
session list ("Sign out" removes a session from the local array, mirroring My Services' `active`
toggle) and Payments tab's card "..." menu (set default / remove).

**Additional pages (folded into later commits, never itemized above):** three public/legal pages
are hardcoded content with no mock file, no backend implication: FAQ (`/faq`), Help Center
(`/help`), Terms of Service (`/terms`, tabbed Terms/Privacy/Guidelines). Seven more do carry new
mock/store data and are the reason Phase 2/3 below were rewritten: Estars Leaderboard (`/estars`,
`mocks/estars.ts`, a Pal ranking by category/period), Notifications (`/notifications` + header
dropdown, `stores/notifications.ts` wrapping `mocks/notifications.ts`), Subscriptions
(`/subscriptions`, `mocks/subscriptions.ts`, recurring buyer→Pal billing, `CancelSubscriptionModal`),
Order Detail (`/bookings/:bookingId`, buyer's single-order view with a timeline, wires
`CancelOrderModal` and `RefundModal`/"report an issue"), Withdraw (`/wallet/withdraw`,
`mocks/wallet.ts`'s payout methods + withdrawal history + platform fee), Create Service
(`/dashboard/player/services/new` — supersedes the 1.12/1.13 note that `CREATE SERVICE.jpg` "was
not built"; it has been, as its own route), and Post Detail (`/feed/:postId`, threaded comments on
`mocks/feed.ts` posts). Settings also gained two modals implying flows not previously scoped:
`TwoFactorAuthModal` and `DeleteAccountModal`.

**Database schema (built for 2.3):** 28 tables, 18 enums, in
`supabase/migrations/20260822070728_initial_schema.sql` (CLI-managed migrations, pushed with
`bunx supabase db push`). Columns were matched against `stores/*.ts` interfaces and
`mocks/*.ts` seed data rather than the 2.3 checklist line verbatim, which surfaced a few
deviations:
- `admin_disputes` was **not** created as a separate table from `order_disputes` — `AdminDispute`
  (`mocks/admin.ts`) is just `order_disputes` joined back to `bookings`/`players`/`users`, so one
  table backs both the buyer's "report an issue" flow (Order Detail / `RefundModal`) and the
  admin Disputes tab. `admin_flags` (Flagged Players tab) stays its own table.
- Three tables aren't in the 2.3 line but were required to represent what the mocks already
  model: `message_threads` (one per user pair, `messages` alone can't express thread-level
  `unreadCount`/`lastMessagePreview`), `addons` (the flat global catalog from `mockAddons`, with
  `booking_addons` as a per-booking snapshot junction), and `topup_packages` (Wallet's top-up
  tiers). `album_items` and `wish_items` were also added under the `players` domain to fully
  back the Player Profile Album/Wish tabs, since "players" in the 2.3 line only named the table,
  not its satellite data.
- Estars leaderboard, Pal Dashboard stats, and the buyer directory (`mocks/estars.ts`,
  `mocks/dashboardStats.ts`, `mocks/buyers.ts`) got **no tables** — all three are either cuttable
  (3.12) or explicitly documented as derivable from `bookings`/`reviews`/`wallet_transactions`
  (3.7), and `BuyerSummary` is just a subset of `users`. Revisit only if 3.7/3.12 turn out to need
  a materialized/cached version instead of a live query.
- Every table has RLS **enabled with zero policies**. `service_role` (the backend's client,
  `core/supabase.py`) bypasses RLS and keeps working; `anon`/`authenticated` get zero access
  until per-feature policies are written alongside real Supabase Auth (2.5) and each Phase 3
  feature. Don't assume a table is reachable from the frontend just because it exists.
- `players.user_id` is nullable (seed/demo Pals aren't linked to an account, matching
  `mocks/players.ts` `p1`..`p8`); `bookings.order_number` is a unique text column but nothing
  generates it server-side yet, that's still a 3.4 task per the Booking flow note above.

**Storage buckets (built for 2.4):** 5 buckets in
`supabase/migrations/20260822071454_storage_buckets.sql`. `avatars`/`service-covers` are public
(served by plain URL, no auth needed to view a profile/service card); `rank-verification`/
`id-documents`/`dispute-attachments` are private, readable only via the backend's service-role
client (e.g. signed URLs), matching how sensitive those uploads are. Same RLS posture as 2.3:
`storage.objects` RLS is on with no policies, so only service_role can write until per-feature
policies land in 2.5/Phase 3. Two follow-ups to the 2.3 schema, both required for these buckets
to actually be usable: `services.cover_image_url` (Create Service's cover upload had no column
yet) and `players.id_front_url`/`id_back_url`/`rank_verification_url` (Become a Pal's Verify
step, plus rank verification which has no upload UI yet — column provisioned ahead of it).
`order_disputes.attachment_urls` from 2.3 already covers the dispute-attachments bucket, no
change needed there.

**Auth wiring (built for 2.5):** scoped to **Google OAuth only** (per the task), not
email/password — `LoginView`/`SignupView`'s email forms are unchanged stubs, still `TODO`.
- Frontend: `lib/supabase.ts` (anon/publishable client), `stores/auth.ts` rewritten with
  `init()` (restores/subscribes to the session, memoized into a single promise), `signInWithGoogle()`
  (`supabase.auth.signInWithOAuth({ provider: 'google' })`, `redirectTo` → `/home`), and
  `signOut()`. Both "Continue with Google" buttons now call it; `AppHeader`'s "Log out" calls
  `signOut()`. `AuthUser.playerId` is hardcoded `null` for now, real Pal-profile linkage is 3.1.
- Route guards: a new `requiresAuth` meta flag (separate from the pre-existing `authenticated`
  flag, which only controls chrome and is also set on the 404 catch-all — gating on it directly
  would have redirected logged-out users hitting a bad URL to `/login`). Applied to the
  conservative set only: `/home`, `/dashboard/*`, `/messages`, `/settings`, `/wallet*`,
  `/bookings*`, `/checkout*`, `/become-player`, `/subscriptions`, `/notifications`. Browsing
  (players, profiles, feed, services, estars) stays public. The guard `await`s the same memoized
  `init()` promise the app boot sequence uses rather than trusting call-order in `main.ts` —
  `app.use(router)` kicks off Vue Router's own initial navigation (and guard run)
  asynchronously, so it does not actually wait for a separate `await authStore.init()` call made
  after it; without the guard awaiting the promise itself, first-load hits a real race (session
  not yet restored → bounced to `/login` even when valid).
- Backend: `handle_new_user()` trigger (`security definer`, on `auth.users` insert) populates
  `public.users`, since Google sign-in creates the `auth.users` row directly with no app code in
  between. First real RLS policies (self select/update on `public.users`), per the "policies
  land in 2.5" note left in the 2.3 section above; every other table is still service_role-only.
- Not done here, left for Phase 3 as each feature is wired: email/password auth, backend JWT
  verification for FastAPI routes (nothing calls the API with a bearer token yet), and replacing
  the pervasive `mockCurrentUser` reads across the app (header, dashboards, settings, etc.) with
  the real `authStore.user` — 2.5 only wires the session itself, not every consumer of it.

---

## Status

- **Current phase:** Phase 4 — Payment, moved up ahead of 3.16/3.17 per user direction
  (2026-08-25). 3.15 (Docker + Docker Compose) is done; 3.16 (clean out mock/demo data) and
  3.17 (seed script) are deferred until Phase 4 finishes.
- **Next task:** 4.1 is fully done (4.1a-k, including 4.1f's live smoke test). 4.2 (Squad Coin
  ledger wiring) and 4.3 (manual platform commission tracking) are done. Next up is 4.4 (Bakong
  KHQR integration, scope TBD) then 4.5 (final-report escrow note), after which 3.16/3.17 resume.
- **Last updated:** 2026-08-26

---

## Phase 0 — Frontend Foundations

- [x] 0.1 Strip default Vite/Vue boilerplate (`HelloWorld`-style demo content, `stores/counter.ts`, sample router entry)
- [x] 0.2 Configure Nuxt UI + Tailwind CSS v4 (Vue install path, global setup, brand theme vars, confirm `@phosphor-icons/vue` as the icon set)
- [x] 0.3 Base layout shell: app header/navbar, footer, main content container, responsive breakpoints
- [x] 0.4 Register all page routes in `router/index.ts` as placeholder components (see full route table in Phase 1)
- [x] 0.5 Pinia store skeletons: `auth`, `players`, `bookings`, `messages`, `ui` (empty state shape only, no data fetching yet)
- [x] 0.6 Shared mock data fixtures (fake players, bookings, messages) to build UI against before backend exists

## Phase 1 — Frontend Pages (static UI, mock data only)

Build in this order — each one is a single task:

- [x] 1.1 Landing (`/`) — hero, how it works, featured players, games supported
- [x] 1.2 Login (`/login`) + Signup (`/signup`) — forms only, no real auth yet (plus Forgot Password `/forgot-password` and Set New Password `/reset-password`)
- [x] 1.3 Home (`/home`) — authenticated landing hub shown right after login (post-signup role modal and future login redirect both land here instead of `/players`/`/become-player` directly). Quick-action cards into Browse Players, Become a Player, My Bookings, Messages, and role dashboard; recommended players / recent activity sections. This is the branch point every post-login page links out from, so build it before the pages it links to. `/` (`LandingView`) stays the logged-out public marketing page.
- [x] 1.4 All Services (`/services`) — service/category directory built per `squadup_ui/ALL SERVICES.jpg`. Linked from the navbar `Games` link and the homepage `All Services` tile. Games/Chilling/Valorant tiles reuse existing assets; Hobbies Talk, E-Chat, and Watch Together are left image-less placeholders pending real artwork.
- [x] 1.5 Browse Players (`/players`) — card grid, filters (game, rank, role, price, availability, language)
- [x] 1.6 Player Profile (`/players/:id`) — profile details, reviews list, "Book" CTA, built per the mockups in `squadup_ui/PROFILE/`. One profile page with 4 tabs, images left blank pending real artwork. Full mock detail (services, reviews, feed, album, wish) authored for player `p1`; other mock players fall back to a minimal generic profile. Split into sub-tasks, one tab at a time:
  - [x] 1.6a Services — service list sidebar, selected service detail (styles/platforms/service types), reviews list (`SERVICE.jpg`)
  - [x] 1.6b Feeds — post composer (visual only, no backend) + feed post list (`FEEDS.jpg`)
  - [x] 1.6c Album — highlights grid with All/Clips/Screens filter (`ALBUM.jpg`)
  - [x] 1.6d Wish — wishlist grid with "Book" CTA per item (`WISH.jpg`)
- [x] 1.7 Become a Player (`/become-player`) — 5-step "Pal Application" wizard, built per the mockups in `squadup_ui/ONBOARDING/` (folder name is a misnomer — this is the only signup-adjacent flow in the design; there's no separate base-profile onboarding). After signup, a modal ("Just looking for a player" / "Become a Pal") routes here or to Browse Players — see `PostSignupRoleModal.vue`. Split into sub-tasks, one screen at a time:
  - [x] 1.7a Account — avatar, display name, email, phone, region, timezone, password, terms checkbox (`ACCOUNT.jpg`)
  - [x] 1.7b Games & skills — game(s), rank, role (`GAMES.jpg`)
  - [x] 1.7c Rates & availability — pricing, schedule (`RATES.jpg`)
  - [x] 1.7d Verify & payout — ID upload, Squad Coin payout setup (`VERIFY.jpg`)
  - [x] 1.7e Review & submit — final summary before submitting (`REVIEW.jpg`)
  - [x] 1.7f Success — confirmation screen after submit (`SUCCESS.jpg`)
- [x] 1.8 Feed (`/feed`) — social feed hub built per `squadup_ui/FEED.jpg` and `squadup_ui/FEED/`. Linked from the navbar beside "Discover". Left sidebar (profile card + Feed/Following/Explore/Saved/Your profile nav) and right rail (Suggested Pals, Trending now) are shared across all 4 screens; images left blank pending real artwork.
  - [x] 1.8a Feed (`/feed`) — composer + feed post list (`FEED.jpg`)
  - [x] 1.8b Following (`/feed/following`) — posts from followed Pals, filterable (`FEED/FOLLOWING.jpg`)
  - [x] 1.8c Explore (`/feed/explore`) — search + category grid of trending posts (`FEED/EXPLORE.jpg`)
  - [x] 1.8d Saved (`/feed/saved`) — bookmarked posts and services, filterable (`FEED/SAVED.jpg`)
- [x] 1.9 Booking — Service Detail page (`/players/:id/services/:serviceId`), "Book a session"
      modal (quantity/add-ons/promo), Checkout (`/checkout/:bookingId`), and Order Confirmation
      (`/checkout/:bookingId/confirmation`), built per `squadup_ui/s2/SERVICE DETAIL.jpg` and
      `squadup_ui/s1/{BOOKING,CHECKOUT,ORDER CONFIRMATION}.jpg`. Replaces the originally planned
      `/book/:playerId` duration/time-picker page. See the "Booking flow" note above for what's
      still mocked and needs real backend decisions.
- [x] 1.10 My Bookings (`/bookings`) — list with status (pending/accepted/declined/completed)
- [x] 1.11 Messages (`/messages`) — chat UI shell (thread list + message pane), no realtime wiring yet
- [x] 1.12 Player Dashboard (`/dashboard/player`) — profile mgmt, availability editor, incoming requests, session history, earnings view
- [x] 1.13 User Dashboard (`/dashboard/user`) — not an analytics dashboard (that's Player Dashboard's job, see the Account model note above). A plain user account has no need for one, so this route is just a lightweight "Become a Pal" upsell/ad for accounts with no `playerId`. Session/booking history lives on My Bookings (1.10) instead, reviews-left and spending stay wherever wallet/Settings ends up; don't duplicate that content here.
- [x] 1.14 Settings (`/settings`) — account settings form
- [x] 1.14a State pages + Wallet (`/wallet`) — reusable `EmptyState` component
      (`components/common/EmptyState.vue`) built per
      `squadup_ui/STATE/{404,EMPTY SEARCH,EMPTY FEED,EMPTY WALLET}.jpg`, wired into 404
      (`NotFoundView`), Browse Players' no-search-results state, Feed Following's
      no-follows state, and a new Wallet page (`/wallet`, zero-balance state) linked from
      the header's coin balance / top-up button.
- [x] 1.15 Admin (`/admin`) — flagged players, disputes list. Single route, gated behind a
      mock credential login (`stores/admin.ts`, `admin@squadup.gg` / `SquadUp-Admin-26`,
      session-only via `sessionStorage`) since there's exactly one admin account and no
      real auth yet (that lands with 2.5 / 3.8). Once logged in, `AdminView.vue` renders
      its own dashboard shell (`hideChrome: true`, no public header/footer or Pal dashboard
      chrome) with three tabs built like Settings' tab pattern (`SettingsNav` reused as-is):
      `AdminOverviewPanel` (stat cards + `DashboardBarChart` reuse + recent lists),
      `AdminFlaggedPlayersPanel` and `AdminDisputesPanel` (filter pills + table + review
      modal, mirroring `PlayerOrdersView`'s table/modal shape). Mock data in `mocks/admin.ts`.
- [x] 1.16 Checkout (`/checkout/:bookingId`) — built early as part of 1.9's booking flow (payment
      summary UI shell only, no live payment logic — that's still Phase 4)
- [x] 1.17 Additional pages folded in after 1.9-1.14, not previously itemized: FAQ (`/faq`), Help
      Center (`/help`), Terms of Service (`/terms`), Estars Leaderboard (`/estars`), Notifications
      (`/notifications`), Subscriptions (`/subscriptions`), Order Detail (`/bookings/:bookingId`),
      Withdraw (`/wallet/withdraw`), Create Service (`/dashboard/player/services/new`), Post Detail
      (`/feed/:postId`), plus Two-Factor Auth / Delete Account / Cancel Order / Cancel Subscription
      confirmation modals — see note above.

## Phase 2 — Backend Foundations

- [x] 2.1 FastAPI app structure: routers per domain (players, bookings, messages, reviews, auth, feed, wallet, notifications, subscriptions, admin), `pydantic-settings` config, CORS for the Vite dev origin
- [x] 2.2 Supabase connection (service-role client for backend, anon client pattern documented for frontend)
- [x] 2.3 Database schema in Supabase: `users`, `players`, `services` (+ `service_pricing_options`, `service_promotions` for 1.17's Create Service), `bookings` (+ `order_cancellations`, `order_disputes` for Order Detail's cancel/report flows), `messages`, `reviews`, `posts` (+ `comments`, `follows`, `saved_items` for Feed/Post Detail), `notifications`, `subscriptions`, `wallet_transactions` (+ `payout_methods`, `withdrawals` for Wallet/Withdraw), `payment_cards`, `active_sessions` (Settings), `admin_flags`/`admin_disputes` tables + relations — match each table's shape against the corresponding `mocks/*.ts` file cataloged above before finalizing columns
- [x] 2.4 Supabase Storage buckets: player avatars, rank verification screenshots, Pal ID/KYC documents (1.7d), service cover images (Create Service), dispute/report attachments (Order Detail's "report an issue" flow)
- [x] 2.5 Auth wiring: Supabase Auth end-to-end (signup/login/logout, session persistence, route guards on frontend)

**Task breakdown convention:** any Phase 2/3 task large enough to span multiple files or
layers (e.g. backend + frontend, or several pages) gets broken into lettered sub-items
(`3.1a`, `3.1b`, ...) under its checklist line, each checked off independently as it lands,
same pattern Phase 1 already used for 1.6/1.7/1.8. Don't leave a multi-part task as one big
unchecked box until the whole thing is done.

## Phase 3 — Backend Features (wire real data into Phase 1 pages)

- [x] 3.1 User profile CRUD + player profile CRUD + service CRUD (Create/Edit Service) + connect to Player Profile / Become a Player / Player Dashboard / Create Service pages. Backend (FastAPI + Supabase) for user/player/service CRUD, live-smoke-tested against the real project; frontend wired end-to-end (Become a Player wizard, Create/My Services, Player Profile + Service Detail) with a mock fallback on Player Profile/Service Detail for seed Pals (`p1`..`p8`) not yet in the DB (3.2's call). Type-check/lint clean; manual browser walkthrough not run by Claude, left to the user.
  - [x] 3.1a Backend core: bearer-token auth dependency, Supabase Storage upload helper,
        camelCase response schema base (`core/auth.py`, `core/storage.py`, `core/schema.py`)
  - [x] 3.1b Backend: `GET/PATCH /users/me` (`routers/users.py`)
  - [x] 3.1c Backend: `GET /players/{id}` (public profile), `GET/POST/PATCH /players/me`
        (`routers/players.py`) — `POST /players/me` is the Become a Player submission and
        auto-creates a `services` row per priced game from the Rates step
  - [x] 3.1d Backend: `POST/PATCH/DELETE /players/me/services/{id}` (`routers/players.py`)
  - [x] 3.1e Backend: live smoke test against the real Supabase project (create a throwaway
        test user, curl through create-player → get → create-service → toggle-active). Caught
        and fixed two bugs only a live run surfaces: (1) `postgrest-py`'s `.maybe_single()`
        returns `None` itself (not a response with `.data = None`) on zero rows, which crashed
        every "no row yet" path (`GET /players/me` before a profile exists, the existing-profile
        check in `POST /players/me`, etc.) across `routers/users.py` and `routers/players.py` -
        all six call sites now guard `if not result or not result.data`. (2) `_get_owned_service`'s
        `players!inner(user_id)` embed was ambiguous once `players.highlighted_service_id` (a
        second FK between `services` and `players`) existed, so PostgREST rejected every
        `PATCH`/`DELETE /players/me/services/{id}` - fixed by naming the FK explicitly
        (`players!services_player_id_fkey!inner(user_id)`). Also noted: deleting an `auth.users`
        row only cascades to `public.users`, not `players`/`services` (no FK cascade configured
        in 2.3's schema) - not fixed now since no delete-account flow is wired yet (3.13), but
        worth remembering before that lands.
  - [x] 3.1f Frontend: `lib/api.ts` bearer-token fetch client + `VITE_API_URL` env var
  - [x] 3.1g Frontend: `stores/auth.ts` real `playerId` lookup (queries `players.id` by
        `user_id` alongside the existing `users` row query) + `stores/players.ts` real
        `mine`/`mineLoading`/`mineError` state and `fetchMine`/`createMine`/`createService`/
        `updateService`/`deleteService` actions against `/players/me...`. Mutations refetch
        `mine` afterward rather than re-deriving `highlightedServiceId`/profile-level
        `priceCoins` client-side. `MyPlayerProfile`/`MyService`/`ServiceUpdate` types added
        alongside the existing mock-backed `PlayerProfile` (kept for 3.1j's reviews/feed/
        album/wish, still mock-only until 3.6/3.8).
  - [x] 3.1h Frontend: Become a Player wizard wired to the real submit endpoint (drop the
        dead password field/strength meter, track raw `File`s for avatar/ID upload)
  - [x] 3.1i Frontend: Create Service + My Services (Player Dashboard) pages wired to real
        service CRUD — `CreateServiceView.vue` posts multipart `FormData` to
        `playersStore.createService` (name/description/platforms/pricing_options JSON/
        first_order_free/percent_off/cover), with a submitting/error state on Publish;
        "Category" stays UI-only since the backend has no matching field. `PlayerServicesView.vue`
        (`/dashboard/player/services`) now fetches `playersStore.mine` on mount with
        loading/error/no-profile/empty states (each via `UEmpty`), the active toggle calls
        `updateService`, and a new trash-icon button + `ConfirmModal` wires `deleteService`
        (toast on failure via `useToast`). "Edit" stays disabled — no edit form/route exists yet,
        out of scope here.
  - [x] 3.1j Frontend: Player Profile page wired to real data with a mock fallback (seed
        Pals `p1`..`p8` aren't in the DB yet, that's 3.2's call). Added `players.fetchPlayer`
        (`GET /players/{id}`, public) plus `playerSummaryFromDetail`/`playerProfileFromDetail`
        converters, and a shared `usePlayerProfileData(id)` composable that tries the real
        endpoint and falls back to `mocks/playerProfiles.ts` on any failure (404 for a real
        missing id, or a Postgres error for a non-uuid mock id like `p1`) — reviews/feed/album/wish
        come back empty for a real profile rather than mock data, consistent with `mine`'s `self`
        entry. `ServiceDetailView.vue` (`/players/:id/services/:serviceId`) uses the same
        composable since it's a direct drill-down from the profile page and would otherwise break
        for real playerIds.
  - [x] 3.1k Verification: `vue-tsc --build` and `eslint` both clean (the only eslint hits,
        `StepRates.vue`/`RefundModal.vue` unused-var errors, predate 3.1 and are unrelated).
        Manual browser walkthrough skipped per standing instruction not to run the `run` skill
        in this project - user to verify the flow manually.
- [x] 3.2 Browse & filter endpoint + connect to Browse Players page
  - [x] 3.2a Backend: `GET /players` (`routers/players.py`) — a new list route registered above
        the `/{player_id}` catch-all (distinct path shape, no collision risk, but kept there for
        readability alongside `/me`). Filters (`q`, `game`, `rank`, `role`, `language`,
        `max_price`, `online`, `is_new`) and `sort` (`rating`/`price_asc`/`price_desc`) are all
        applied in Python over one `players` fetch plus one batched `services` fetch scoped to
        each player's `highlighted_service_id` (fine at this dataset scale; avoids composing
        PostgREST filters against array columns for `games`/`languages`). Added `PlayerSummaryOut`
        (the browse-card slice of `PlayerDetailOut`, no `services`/`serviceDetails`) and a
        `_player_summary` helper alongside the existing `_serialize_player`. No `availability`
        filter: 1.5's actual filter chips never grew a dropdown for it and the `players` table
        (2.3) has no matching column, so there's nothing to wire it to yet.
  - [x] 3.2b Backend: live smoke test against the real Supabase project (create a throwaway user
        + player via `POST /players/me`, curl `GET /players` with each filter param and `sort`
        individually, confirm expected include/exclude/order, delete the throwaway user/player).
  - [x] 3.2c Frontend: `stores/players.ts` `fetchList()` action wired to `GET /players` into the
        pre-existing (previously-unused) `list`/`loading`/`error` state from the 0.5 store
        skeleton.
  - [x] 3.2d Frontend: `PlayersView.vue` now fetches `fetchList()` on mount and merges it with
        `mockPlayers` (`allPlayers` computed) rather than replacing the mock catalog outright —
        the call left open in 3.1j ("seed Pals aren't in the DB yet, that's 3.2's call"). Seed
        Pals `p1`..`p8` stay as demo content; any real signed-up Pal now also shows up in Browse
        Players alongside them. The existing search/game-category matching, promo/rating chips,
        and sort dropdown are unchanged, just operate over `allPlayers` instead of `mockPlayers`
        directly — those chip predicates (promo-badge string checks, rating thresholds) stay
        client-side rather than becoming more backend query params, since they're presentation
        categories layered on the fetched list, not independent data filters. `vue-tsc --build`
        and `eslint` both clean.
- [x] 3.3 Matching algorithm (weighted scoring: game 40 / rank 30 / role 20 / availability 10) + apply as default sort on Browse Players
  - [x] 3.3a Backend: `_match_score()` (`routers/players.py`) scores each `GET /players` result
        against the `game`/`rank`/`role` query params already accepted by 3.2a. Those three
        params moved out of `matches()`'s hard AND-filter and into scoring only, so a partial
        match now ranks lower instead of being excluded (e.g. a Diamond Duo Queue search still
        shows a Platinum Coaching Pal, just below exact matches). `online` stays a flat +10
        bonus regardless of filters, there's no `availability` column (per 3.2a's note) so
        "online now" is the only signal to score against. When `sort` isn't explicitly
        `rating`/`price_asc`/`price_desc`, results are ordered by this score descending
        (stable otherwise) - this is the "apply as default sort" half of the task.
  - [x] 3.3b Backend: live smoke test against the real Supabase project (inserted 4 throwaway
        `players` rows directly via the service-role client covering exact/partial/no-match
        combinations, started uvicorn, curled `GET /players?game=Valorant&rank=Diamond&role=Duo
        Queue` and confirmed the 100/70/50/10-score order, curled with no filters and confirmed
        online-first default order, confirmed `sort=rating` still overrides it, deleted the
        throwaway rows).
  - [x] 3.3c Frontend: `PlayersView.vue` now passes `game` (from the existing `gameFilter` route
        query) into `playersStore.fetchList()` on mount and on route change, so the backend's
        match-scored order actually has a game to score against on the `/players?game=...`
        pages; the plain `/players` browse page gets the online-first default with no changes
        needed since "Relevance" already sends no `sort` param. No rank/role filter UI exists
        in 1.5's actual build (only `q`/`game` reach the backend, see 3.2's note), so those two
        score components stay backend-only until such UI exists. `vue-tsc --build` and `eslint`
        both clean (same two pre-existing, unrelated errors noted in 3.1k).
- [x] 3.4 Booking request flow (create/accept/decline/cancel + refund/dispute reporting) + connect Booking / My Bookings / Order Detail / Player Dashboard
  - [x] 3.4a Backend: `routers/bookings.py` - `POST /bookings` (buyer submits, server-generates
        `order_number` and validates the service belongs to the player), `GET /bookings/mine`
        (buyer) / `GET /bookings/incoming` (Pal), `GET /bookings/{id}` (either party),
        `POST /bookings/{id}/{accept,decline,complete,cancel}` (status-transition guards per
        role), `POST /bookings/{id}/dispute` (buyer's "report an issue", writes `order_disputes`
        - same table the future admin Disputes tab reads, per the 2.3 note). Resolves the
        draft-vs-submitted question left open in the Booking flow note: "Continue to checkout"
        stays a client-side-only draft (`stores/bookings.ts`'s `draft` state, not persisted),
        and only Checkout's "Place order" actually calls `POST /bookings` - so an abandoned
        checkout never creates a real `pending` row. Add-ons are still an unauthored flat
        catalog (Booking flow note), so `_resolve_addon_id` self-heals the `addons` table by
        label the first time each one is booked rather than requiring a seed migration. No
        "mark complete" action existed in any mockup, but the schema's `booking_status` has
        nowhere else to reach `completed` from, so `POST /bookings/{id}/complete` + a "Mark
        complete" button on Pal Orders was added as the natural counterpart to accept/decline.
  - [x] 3.4b Backend: live smoke test against the real Supabase project (two throwaway users -
        buyer + Pal - a throwaway player/service, then the full lifecycle through real HTTP with
        real bearer tokens: create -> appears in `mine`/`incoming` -> non-owner accept rejected
        (404) -> accept -> double-accept rejected (409) -> complete -> dispute -> a second
        booking through decline -> a third through cancel, confirming `order_cancellations`/
        `order_disputes` rows land correctly and `booking_addons` self-heals into `addons`).
        Caught one bug only a live run surfaces: `_SELECT`'s embed initially asked for
        `users(display_name, avatar_url)`, but `public.users` (2.3) has no `avatar_url` column
        (only `players` does) - fixed by dropping the column from the select and from
        `BookingOut`/the frontend `Booking` type entirely (buyers have no avatar in this schema,
        so a perpetually-null field wasn't worth keeping). All rows/users cleaned up after.
  - [x] 3.4c Frontend: `stores/bookings.ts` rewritten around `draft` (the pre-submission
        selection), `list`/`incoming` (fetched from `/bookings/mine` and `/bookings/incoming`,
        each falling back to the existing mock fixtures on failure rather than replacing them
        outright, same resilience convention as 3.1j/3.2d), and action methods
        (`placeOrder`/`acceptBooking`/`declineBooking`/`completeBooking`/`cancelBooking`/
        `reportIssue`) that call the new endpoints and patch the booking back into whichever
        local list holds it. `Booking` gained optional denormalized `playerDisplayName`/
        `playerAvatarUrl`/`serviceName`/`buyerDisplayName` fields the backend now joins in, so
        list/detail views don't need a separate per-row player fetch (mock fixtures simply don't
        set them, and views fall back to the old `mocks/players.ts` lookup when absent).
  - [x] 3.4d Frontend: `BookingModal.vue` now builds a `BookingDraft` (carrying `palName`/
        `palTagline` along as `playerDisplayName`/`serviceName` so Checkout never needs a mock
        player lookup) and routes to Checkout without touching the backend. `CheckoutView.vue`
        reads the draft instead of a pre-existing booking, and "Place order" calls
        `bookingsStore.placeOrder(...)`, which is where the real `POST /bookings` happens; the
        real booking's id (not a client-generated one) is what Order Confirmation routes to.
  - [x] 3.4e Frontend: `MyBookingsView.vue` fetches `fetchList()` on mount and cancels through
        `bookingsStore.cancelBooking(id, payload)` (the modal already emitted a full
        reason/refundOption/refundCoins/note payload, it just wasn't wired to anything real).
        `OrderDetailView.vue` resolves a booking by checking the store first, then
        `GET /bookings/{id}` for a direct/deep link, then the mock fixtures as a last resort
        (`mocks/bookings.ts`'s new `getMockBooking`); cancel and "Report an issue" both call the
        real endpoints with toast error handling.
  - [x] 3.4f Frontend: `PlayerDashboardView.vue` and `PlayerOrdersView.vue` fetch
        `fetchIncoming()` on mount instead of reading `mockIncomingBookings` directly, and their
        previously-inert Accept/Decline buttons (dashboard widget) plus a new Accept/Decline/Mark
        complete set (Orders page table row and its detail modal) now call the real
        accept/decline/complete actions with per-row loading state and toast error handling.
        "Top services" (dashboard) now sums `bookingsStore.incoming` directly using each
        booking's own `serviceName` rather than cross-referencing `mocks/playerProfiles.ts`.
  - [x] 3.4g Verification: `vue-tsc --build`, `eslint`, and `ruff check` all clean (same two
        pre-existing unrelated eslint errors noted in 3.1k). Manual browser walkthrough skipped
        per standing instruction not to run the `run` skill in this project.
- [x] 3.5 Realtime chat via Supabase Realtime + connect Messages page
  - [x] 3.5a Backend: `routers/messages.py` - `GET /messages/threads` (list, joined participant
        display name + last message preview + unread count, batched over one `message_threads`
        fetch + one `messages` fetch scoped to those thread ids, same batching approach as
        3.2a), `POST /messages/threads` (find-or-create by `participantId`, canonicalizing
        `user_a_id`/`user_b_id` by sorting the two ids since the table's unique constraint is on
        the ordered tuple and either party can be the one who starts a thread),
        `GET /messages/threads/{id}/messages` (history, also marks the other party's unread
        messages read - replaces the frontend-only `unreadCount = 0` `selectThread` previously
        did), `POST /messages/threads/{id}/messages` (send). Already registered in
        `routers/__init__.py` from the 2.1 skeleton, no `main.py` change needed. Note for 3.5d:
        real threads carry a `participantId` that's a `users.id`, not a mock Pal id like
        `mocks/messages.ts`'s `p1`/`p2`/`p3` - `MessagesPanel.vue`'s `mockPlayers` lookup for
        online status/game tag will simply miss for real threads, same graceful-miss pattern as
        other mock-fallback lookups elsewhere.
  - [x] 3.5b Backend: `supabase/migrations/20260823055705_messages_realtime_rls.sql` - SELECT
        policies on `message_threads`/`messages` for `authenticated`, scoped to rows the caller
        is a participant in (the `messages` policy checks membership via a subquery join back to
        `message_threads` since the row itself only carries `thread_id`). SELECT only, not
        INSERT/UPDATE - every actual write still goes through `routers/messages.py`'s
        service-role client, which bypasses RLS entirely, and Supabase Realtime authorizes each
        `postgres_changes` event against the same RLS a SELECT would see, so SELECT is both
        necessary and sufficient here. Also `alter publication supabase_realtime add table` for
        both tables, a separate prerequisite from RLS - the publication starts empty on a fresh
        project, so `postgres_changes` would never fire for these tables even with the policies
        above. Pushed to the linked project with `bunx supabase db push`, confirmed in sync via
        `bunx supabase migration list`.
  - [x] 3.5c Backend: live smoke test against the real Supabase project (three throwaway
        users - A, B, a non-participant C - through real HTTP with real bearer tokens against a
        local uvicorn: A starts a thread with B, B starts one back with A, A starts again -
        all three return the same thread id, confirming find-or-create dedups regardless of
        initiator and never duplicates. Both sent a message; thread list showed the right
        preview/unread count for each side; opening the thread marked only the counterpart's
        messages read, leaving the other side's unread count untouched. Non-participant C got
        404 on the thread's messages, self-thread and empty-body both got 400. Confirmed RLS
        directly against PostgREST with each user's own anon-key+JWT: A could `select` the
        thread and its messages, C got zero rows for both - so Realtime's `postgres_changes`
        will authorize correctly once 3.5d subscribes.) All 21 checks passed with no bugs found
        - `_THREAD_SELECT`'s explicit FK names and the RLS policies from 3.5b were correct on
        the first live run. All rows/users cleaned up after, verified empty.
  - [x] 3.5d Frontend: `stores/messages.ts` rewritten around real `fetchThreads`/
        `fetchMessages`/`sendMessage`/`startThread` calls against `/messages/...`, mock fallback
        on failure (same resilience convention as 3.1j/3.2d/3.4c), plus a Supabase Realtime
        `postgres_changes` subscription (via `lib/supabase.ts`, already used for auth) on the
        `messages` table scoped to the active thread, subscribing/unsubscribing as
        `activeThreadId` changes, appending live inserts instead of polling. `MessageThread`'s
        mock-era `participantName` renamed to `participantDisplayName` to match the backend's
        `ThreadOut` field (`mocks/messages.ts` updated to match) - consistent with how
        `Booking` picked up `playerDisplayName` in 3.4c rather than keeping the old mock name.
        A shared `appendMessage` helper dedupes by message id since the sender's own `POST`
        response and the Realtime `INSERT` event for that same row both land in the store.
        `selectThread`/`fetchMessages` always refetch from the server rather than reusing a
        cached thread's messages, since opening a thread is also what marks the other party's
        messages read server-side. Left `MessagesPanel.vue` unwired to the new store shape -
        that's 3.5e; confirmed the resulting `participantName` type errors are confined to that
        one file via `vue-tsc --build`, `stores/messages.ts`/`mocks/messages.ts` themselves are
        clean, and `eslint` is clean on both.
  - [x] 3.5e Frontend: `MessagesPanel.vue` wired to the store's real loading/error state -
        chat list and active thread each get their own loading text / `UEmpty` w/ Retry
        (thread list also distinguishes "No chats yet" from a search yielding nothing), Send
        gets a `sending` guard (disables the input, `UButton`'s `loading` prop) with a toast on
        failure. `onMounted` calls `fetchThreads()` and auto-selects the first thread, replacing
        the old mock-era default-selected-first-thread behavior. "New chat" stays a disabled
        stub (`disabled` + `title="Coming soon"`, same plain-disabled convention as the "Edit"
        button in `PlayerServicesView.vue`) since no user-search UI exists in any mockup.
        Message-bubble alignment now compares `senderId` against a real `currentUserId`
        (`authStore.user?.id`, falling back to `mockCurrentUser.id` when signed out or on a
        mock-fallback thread) instead of the hardcoded mock id, since every message now carries
        a real `users.id` sender. Remaining `participantName` → `participantDisplayName`
        renames from 3.5d applied. `MessagesView.vue` needed no changes - it only picks a
        layout by persona, which stays on `mockCurrentUser` along with the rest of the app's
        not-yet-migrated persona/profile chrome (header, sidebar). `vue-tsc --build` and
        `eslint` both clean (same two pre-existing unrelated eslint errors noted since 3.1k).
  - [x] 3.5f Verification: `vue-tsc --build`, `eslint`, and `ruff check` all clean (the
        `eslint` run surfaces only the same two pre-existing unrelated errors noted since
        3.1k - `StepRates.vue`/`RefundModal.vue` unused vars). Manual browser walkthrough
        skipped per standing instruction not to run the `run` skill in this project.
- [x] 3.6 Ratings & reviews endpoint + connect to Player Profile and User Dashboard
  - [x] 3.6a Backend: `routers/reviews.py` - `POST /reviews` (the buyer's `LeaveReviewModal`
        submission: validates the booking is theirs and `completed`, rejects a second review for
        the same booking, derives `sentiment` from `rating` since the modal never collects it
        directly), `GET /reviews/player/{id}` (public, grouped by `service_id` - matches the
        frontend's `PlayerProfile.reviews: Record<string, PlayerReview[]>` shape exactly, no
        reshaping needed on the frontend side). A review recomputes both `services.rating` (that
        service's reviews only) and `players.rating`/`review_count` (every review across all of
        the Pal's services) from scratch each time - simple average over live rows, no running
        total to keep in sync. `highlights`/`tipCoins` the modal collects stay UI-only, same
        "stays UI-only" convention as Create Service's Category field - `reviews` (2.3) has no
        highlights column, and tips need the wallet ledger (3.9). `bookings.py`'s `BookingOut`
        gained `has_review` (a `reviews(id)` embed on the existing `_SELECT`) so My Bookings can
        tell a reviewed order from one still awaiting a review without a separate lookup.
  - [x] 3.6b Backend: live smoke test against the real Supabase project (a throwaway buyer + Pal
        through real HTTP with real bearer tokens: create Pal profile/service, book, accept,
        complete, submit a 5-star review -> `hasReview` flips true on `GET /bookings/{id}`,
        `GET /reviews/player/{id}` returns it grouped under the right service id, `GET
        /players/{id}` shows `rating: 5.0`/`reviewCount: 1` and the service's own `rating: 5.0`.
        Also confirmed: a second review on the same booking gets 409, the Pal reviewing their own
        booking gets 404 (not the buyer), a rating outside 1-5 gets 422, and reviewing a still-
        `pending` booking gets 409. All rows/users cleaned up after, verified empty.
  - [x] 3.6c Frontend: `stores/players.ts` gained `fetchPlayerReviews(id)`
        (`GET /reviews/player/{id}`, swallows failures into `{}` since no reviews yet is a normal
        empty state) plus a `reviewFromApi`-style converter that turns the backend's `createdAt`
        into the mock-era short `timeAgo` string (new `utils/timeAgo.ts`, e.g. `"2d"`/`"1w"`,
        matching `mocks/playerProfiles.ts`'s authored format). `stores/bookings.ts` gained
        `Booking.hasReview` (optional, mock fixtures leave it unset = never reviewed) and
        `submitReview(bookingId, {rating, text})` (`POST /reviews`, patches `hasReview` onto the
        local booking rather than refetching).
  - [x] 3.6d Frontend: `usePlayerProfileData` (shared by Player Profile and Service Detail, per
        3.1j) now also calls `fetchPlayerReviews` alongside `fetchPlayer` and merges the result
        into `profile.reviews` for a DB-backed player, so `ServiceReviewsPanel` (already wired to
        `profile.reviews[selectedServiceId]`) needed no changes itself. A DB-backed Pal's
        reviews/rating/reviewCount are now all real; the mock fallback (seed Pals `p1`..`p8`)
        is untouched.
  - [x] 3.6e Frontend + scope note: `MyBookingsView.vue`'s `LeaveReviewModal` (already built in
        Phase 1 but never wired to anything) now calls `bookingsStore.submitReview` on submit,
        with a toast on failure; a completed order that already has a review shows a disabled
        "Reviewed" button instead of "Leave review", using the new `hasReview` field. **User
        Dashboard deviation:** `UserDashboardView.vue` (1.13) is a static "Become a Pal" upsell
        card for accounts with no `playerId` - it never grew a reviews section, and 1.13's own
        note explicitly punted "reviews-left" to "wherever wallet/Settings ends up" without
        landing it anywhere. There is no reviews surface on User Dashboard to connect. My
        Bookings is the actual buyer-side page a review flow lives on in this build, so that's
        where 3.6 connects instead - flagging this now rather than leaving the checklist line
        looking unaddressed.
  - [x] 3.6f Verification: `vue-tsc --build` and `eslint` clean (same two pre-existing unrelated
        eslint errors noted since 3.1k), `ruff check` clean. Manual browser walkthrough skipped
        per standing instruction not to run the `run` skill in this project.
- [x] 3.7 Player earnings tracker (derived from completed bookings) + connect to Player Dashboard
  - [x] 3.7a Backend: `GET /players/me/earnings` (`routers/players.py`) — derives lifetime/this-month
        earned coins, orders completed (total + this week), response rate, a 7-day earnings bar
        series, and an 8-month earnings overview series, all computed in Python over one
        `bookings` fetch scoped to the caller's `player_id` (same aggregate-in-Python approach as
        3.2a/3.3a). Payout method/schedule/history/pending-clearance stay mock-backed since those
        depend on `payout_methods`/`withdrawals` actually being written to, which is 3.9's job.
  - [x] 3.7b Backend: live smoke test against the real Supabase project (a throwaway Pal with 6
        `completed` bookings seeded directly via the service-role client - spread across this
        week/this month/last month/~7 months ago - plus pending/accepted/declined noise, through
        real HTTP with a real bearer token against a local uvicorn: `lifetimeEarnedCoins`,
        `ordersCompleted`, `ordersCompletedThisWeek`, `responseRatePct` all matched hand-computed
        expected values exactly; `coinsThisMonthChangePct`/`earningsOverview` correctly bucketed
        the ~35-day-old booking into last month and the ~210-day-old one into the 8-month window's
        oldest slot. A second throwaway user with no player profile got 404; no bearer token got
        401. All rows/users cleaned up after, verified empty.
  - [x] 3.7c Frontend: `stores/players.ts` `fetchEarnings()` + `PlayerEarnings` type.
  - [x] 3.7d Frontend: `PlayerDashboardView.vue` now calls `playersStore.fetchMine()` +
        `fetchEarnings()` alongside the existing `fetchIncoming()` on mount. "This month"/"Orders
        completed"/"Response rate" cards and the "Earnings this week" chart read from
        `playersStore.earnings`; "Avg rating" reads `mine.rating`/`mine.reviewCount` instead of
        `mockPalDashboardStats` (rating/review count already real since 3.6, just never wired to
        this page). "This month"'s USD figure is computed client-side with the same
        `COINS_PER_USD = 99` constant already used on Wallet/Withdraw/Subscriptions, rather than
        adding a backend field for an exchange rate that hasn't been decided (see the Booking flow
        note). Dropped "Avg {{ responseTime }}" under Response rate - there's no
        status-change timestamp in the `bookings` schema to derive it from, so it'd just be a
        fabricated number; replaced with a plain "Accepted or declined vs received" label.
  - [x] 3.7e Frontend: `PlayerEarningsView.vue` now calls `fetchEarnings()` on mount; "Lifetime
        earned" and the "Earnings overview" chart read from `playersStore.earnings`. "Available
        balance"/"Pending clearance"/payout method/schedule/history stay on
        `mockPalDashboardStats` - those need a real payout ledger (`payout_methods`/
        `withdrawals`, both already in the 2.3 schema but not written to by anything yet), which
        is 3.9's job, not derivable from bookings alone.
  - [x] 3.7f Verification: `vue-tsc --build` and `eslint` clean (same two pre-existing unrelated
        eslint errors noted since 3.1k), `ruff check` clean. Manual browser walkthrough skipped
        per standing instruction not to run the `run` skill in this project.
- [x] 3.8 Social feed endpoints: posts/comments/likes/follows/saved items + connect to Feed (all tabs), Post Detail, Player Profile Feed/Wish/Album tabs
  - [x] 3.8a Backend: `routers/feed.py` — posts (`GET /feed` main list, `GET /feed/following`
        scoped to followed players, `POST /feed/posts` create, `GET /feed/posts/{id}` for Post
        Detail), likes (`POST/DELETE /feed/posts/{id}/like`, `POST/DELETE
        /feed/comments/{id}/like`), comments (`GET/POST /feed/posts/{id}/comments`, flat
        `parent_comment_id` rows rebuilt into the nested tree `FeedComment.replies` already
        expects), follows (`POST/DELETE /feed/follows/{playerId}`, table keys on `player_id` not
        a user-to-user relation), and saved items (`GET /feed/saved`, `POST/DELETE /feed/saved` —
        body picks `kind: 'post' | 'service'` per the `saved_items_kind_target_check` constraint).
        `GET /feed`, `/feed/following`, and `GET /feed/posts/{id}` stay public (browsing, per the
        2.5 note) via a new `get_optional_user_id` (`core/auth.py`) that returns `None` instead of
        401ing, so `liked`/`following` personalize only when a bearer token is present. New
        migration `supabase/migrations/20260823154043_feed_likes.sql` adds `post_likes`/
        `comment_likes` join tables (same shape as `follows`) since 2.3's `posts.likes_count`/
        `comments.likes_count` were plain counters with no per-user record to toggle against or
        derive a viewer's own `liked` state from — pushed to the linked project, same RLS posture
        as every other table (enabled, zero policies). `likes_count`/`comments_count`/
        `posts_count`/`followers_count`/`following_count` are all recomputed from live rows on
        every mutation rather than incremented, matching `reviews.py`'s "no running total to keep
        in sync" convention. Explore's `ExplorePost`/`SuggestedPal`/`TrendingTopic` have no
        backing tables and none were added — nothing in 1.8c's mock content (trending topics,
        suggested-Pal blurbs like "Adding Socials") maps to real columns, so Explore stays
        mock-only; not revisited unless a later pass decides it's worth deriving from
        `posts`/`players`. Sanity-checked route registration + public/private split locally
        (uvicorn, no live Supabase writes) - the real live smoke test is 3.8c.
  - [x] 3.8b Backend: `routers/players.py` — `GET /players/{id}/album`, `GET /players/{id}/wish`
        (public reads for the Profile Album/Wish tabs), both 404 via a new `_require_player_exists`
        if the id doesn't match a row. `wish_items.saved` decision: it's a column on the Pal's own
        row (keyed by `player_id`, not by viewer), so it's Pal-authored "still wished for" state,
        not the buyer-side bookmark concept `saved_items` (3.8a) already covers under
        `kind: 'service'`. `GET /players/{id}/wish` filters to `saved = true`, the same way
        `_fetch_services` filters the public services list to `active = true` — there's no
        save/unsave mutation for a viewer to call here. This means `ProfileWishTab.vue`'s heart
        toggle (currently local-only, toggling `saved` per viewer) is the wrong shape for what the
        column actually means; 3.8h should drop that toggle for a DB-backed profile (or repoint it
        at `saved_items`/`kind: 'service'` as a distinct "I bookmarked this" feature) rather than
        wiring it to a mutation that doesn't exist. `AlbumItemOut`/`WishItemOut` (`CamelModel`)
        mirror the DB columns directly (`album_items`/`wish_items` from 2.3), nullable where the
        schema allows null (`label`, `game`, `type`, `service_id`) even though the frontend's mock-
        era `AlbumItem`/`WishItem` types declare those as required strings — 3.8h reconciles that
        when it wires a DB-backed profile. Confirmed via `app.openapi()['paths']` that both routes
        register correctly alongside the existing `/players/{player_id}` catch-all (different path
        shape, no ordering conflict). `ruff check` clean.
  - [x] 3.8c Backend: live smoke test against the real Supabase project (a throwaway Pal + two
        buyer accounts - through real HTTP with real bearer tokens against a local uvicorn: create
        post → appears in main feed → follow the Pal → post appears in buyer_a's Following feed,
        absent from buyer_b's → like/unlike (`liked`/`likes` correct per-viewer) → comment + reply
        (nested tree, `isCreator` correct) → comment like/unlike → save a post and a service →
        both appear in `GET /feed/saved` → re-saving the same post returns the existing row
        (app-level find-or-create) → a raw duplicate insert via the service-role client (bypassing
        that app-level guard) confirmed the DB-level `unique(user_id, post_id)`/
        `unique(user_id, service_id)` constraints reject it directly → unsave → a non-owner's
        delete on someone else's saved-item id is a silent no-op, row still there → 401 with no
        bearer token, 400 on a Pal following themself → album/wish reads for the seeded player
        (2 album items, wish filtered to the 2 `saved = true` of 3 seeded, 404 for a bogus player
        id on both). 34/34 checks passed after two fixes; all rows/users cleaned up after,
        verified empty (no leftover `squadup-test.invalid` auth users). Caught two bugs only a
        live run surfaces, both the same "ambiguous PostgREST embed" class as 3.1e's fix:
        (1) `_COMMENT_SELECT`'s `users(display_name)` embed became ambiguous once 3.8a's own
        `comment_likes` join table added a second `comments`↔`users` relationship path - fixed by
        naming the FK explicitly (`users!comments_author_id_fkey(display_name)`), which broke
        `create_comment`, `list_comments`, and comment like/unlike (all three shared the constant).
        (2) `_SAVED_SELECT`'s `services(players(display_name))` embed was ambiguous against
        `players.highlighted_service_id` (the same second-FK situation 3.1e already hit on
        `services`↔`players`) - fixed the same way (`players!services_player_id_fkey`), and the
        parallel `posts(players(...))` embed was named explicit too
        (`players!posts_player_id_fkey`) even though only one FK path exists there, for
        consistency and to preempt the same class if a second one is ever added. `ruff check`
        clean after both fixes.
  - [x] 3.8d Frontend: new `stores/feed.ts` (`posts`/`following`/`saved` state, `fetchFeed`/
        `fetchFollowing`/`createPost`/`toggleLike`/`toggleFollow`/`fetchComments`/`postComment`/
        `toggleSaved` actions against `/feed/...`), same mock-fallback resilience convention as
        `stores/players.ts`/`bookings.ts`/`messages.ts` (3.1j/3.2d/3.4c/3.5d). Also added
        `fetchPost` (Post Detail's direct/deep-link fetch, the `fetchBooking`/`selectThread`
        counterpart) and `toggleCommentLike` (the backend already exposes `POST/DELETE
        /feed/comments/{id}/like` from 3.8a, and `FeedCommentItem.vue` already has a like
        button) - both straightforward extensions of the literal action list above. Types
        (`FeedPost`/`FeedComment`/`FeedSavedItem`) mirror the backend's camelCase response
        shapes (`PostOut`/`CommentOut`/`SavedItemOut`) rather than the older, thinner
        `mocks/feed.ts` shapes (no `playerId`/`liked`/`createdAt`, a display-only `timeAgo`
        instead) - since reshaping `mocks/feed.ts` itself would break every currently-compiling
        feed view (still on 3.8a-c's mock/local-only state, wired for real in 3.8e-h), the mock
        fixtures are adapted at the store boundary instead (`feedPostFromMock`/
        `feedCommentFromMock`/`savedItemFromMock`, synthesizing `createdAt`/`playerId`/`liked`
        stand-ins), leaving `mocks/feed.ts` untouched for now. `vue-tsc --build` and `eslint`
        both clean (only the same two pre-existing unrelated eslint errors noted since 3.1k).
  - [x] 3.8e Frontend: `FeedView.vue` + `FeedFollowingView.vue` wired to the new store —
        `onMounted` calls `fetchFeed`/`fetchFollowing`, list renders off `feedStore.posts`/
        `feedStore.following` instead of `mockFeedPosts`/`mockFollowingPosts`, `formatTimeAgo`
        (`utils/timeAgo.ts`, already used by reviews) turns the store's ISO `createdAt` into the
        mock's short display form since the real `FeedPost` type has no `timeAgo` field.
        `CreatePostModal.vue` now calls `feedStore.createPost({ text })` instead of unshifting
        onto `mockFeedPosts` directly, dropping the hardcoded `category: 'games'` so the
        backend's own default applies; file attachments stay visual-only (no upload endpoint
        exists yet, out of scope here). `FeedPostCard.vue` gained an optional `liked` prop +
        `toggle-like` emit - when `liked` is passed the like button is controlled and persists
        via `feedStore.toggleLike`, when omitted it falls back to its old local-only reactive
        toggle so `FeedSavedView.vue`/`PostDetailView.vue` (still mock-only until 3.8f/3.8g)
        keep working unchanged. Both views' follow toggle now calls `feedStore.toggleFollow`
        against `post.playerId`/`post.following` instead of a per-view local `following` map.
        Mutation failures (`toggleLike`/`toggleFollow`/`createPost`, none of which have a mock
        fallback) surface via `useToast`, matching `MyBookingsView.vue`'s `confirmCancel`
        pattern; the fetches themselves stay silent on failure since `fetchFeed`/`fetchFollowing`
        already fall back to mock fixtures. `vue-tsc --build` and `eslint` both clean (same two
        pre-existing unrelated eslint errors noted since 3.1k).
  - [x] 3.8f Frontend: `FeedSavedView.vue` wired to real `saved` state — `onMounted` calls
        `feedStore.fetchSaved()`, filters and both card branches (post/service) render off
        `feedStore.saved` instead of `mockSavedItems`. Post cards use `item.postId` (the actual
        post id `FeedPostCard`'s `router-link` needs) not `item.id` (the `saved_items` row id),
        `formatTimeAgo(item.createdAt)` in place of the mock's canned `savedAgo` string, and `??`
        fallbacks for the nullable `FeedSavedItem` fields (`author`/`handle`/`text`/`hasImage`/
        `likes`/`comments`) since the flat store type allows nulls the old discriminated-union
        mock type didn't. Both "Unsave" buttons (post and service branches) call a new `unsave()`
        that resolves `feedStore.toggleSaved(item.kind, item.postId ?? item.serviceId ?? item.id)`
        - toggleSaved deletes the existing row since `saved` is fetched fresh, so no re-save
        branch is reachable here - and surface failures via `useToast`, matching 3.8e's
        `toggleLike`/`toggleFollow` pattern. `FeedExploreView.vue` untouched, stays on its mock
        fixtures per 3.8a's note. `vue-tsc --build` clean; `eslint` clean on the touched files
        (same two pre-existing unrelated errors elsewhere, noted since 3.1k).
  - [x] 3.8g Frontend: `PostDetailView.vue` wired — real comments/replies via the store,
        `postComment()` persisted instead of pushing to a local `draftComments` array, like/follow
        state shared with the feed store rather than a separate local `following` ref. Post load
        follows `OrderDetailView.vue`'s `loadBooking` pattern exactly (3.8d's docstring already
        called `fetchPost` the `fetchBooking` counterpart): a new `feedStore.getPost` prefers a
        post already loaded by Feed/Following, then `GET /feed/posts/{id}` for a direct/deep link,
        then `findFeedPost` (mocks) adapted into a `FeedPost` via a local `postFromMockDetail`
        (same "adapt at the boundary" shape as the store's own `feedPostFromMock`, since
        `findFeedPost`'s return type is thinner and `feedPostFromMock` isn't exported). `liked`/
        `toggle-like` wiring on the post reuses 3.8e's `FeedPostCard` controlled-prop pattern
        unchanged. `FeedCommentItem.vue` was refactored from six scalar props to a single
        `comment: FeedComment` prop (store type, not the old mocks one) plus a `toggle-like` emit
        that bubbles a comment (including nested replies) up to `PostDetailView`, which calls the
        already-built `feedStore.toggleCommentLike` (added in 3.8d as a "straightforward
        extension" anticipating this) - the checklist text only names post like/follow, but
        leaving the comment heart button on its old component-local `reactive` toggle would've
        meant the real `comment.liked` field the backend now returns goes fetched-but-ignored, so
        it's wired the same way. Comment sort ('top'/'newest') now compares `likes`/`createdAt`
        directly instead of regex-parsing the old mock `timeAgo` display string (`parseHoursAgo`
        deleted). `postComment`/`toggleFollow`/`toggleLike`/`toggleCommentLike` all have no mock
        fallback (real mutations only) and surface failures via `useToast`, matching 3.8e/3.8f.
        `vue-tsc --build` and `eslint` both clean (same two pre-existing unrelated eslint errors
        noted since 3.1k).
  - [x] 3.8h Frontend + Backend: Player Profile Feed/Album/Wish tabs wired for real (DB-backed)
        profiles. New `GET /players/{id}/feed` (`routers/players.py`) reuses `feed.py`'s
        `PostOut`/`_POST_SELECT`/`_serialize_posts` rather than duplicating that 12-field shape,
        scoped to one Pal's own posts with the same per-viewer `liked`/`following` `feed.py`
        already computes for the main timeline - the first cross-router import in the routers
        package, one-directional (`players.py` → `feed.py`, no cycle) and ruff-clean on the
        leading-underscore names. `stores/players.ts` gained `fetchPlayerFeed`/`fetchPlayerAlbum`/
        `fetchPlayerWish` (same empty-on-404 convention as `fetchPlayerReviews`); its own `FeedPost`
        interface is gone in favor of importing `stores/feed.ts`'s (`PlayerProfile.feed` is now
        that richer shape) so `ProfileFeedsTab.vue` can reuse `feedStore.toggleLike` directly
        instead of duplicating the like mutation. `AlbumItem.label` / `WishItem.game`/`type`/
        `serviceId` widened to nullable per 3.8b's note on `AlbumItemOut`/`WishItemOut`; `Book`
        button on a wish card now guards on `serviceId` and the game/type line joins only the
        parts that exist. `usePlayerProfileData.ts` fetches reviews/feed/album/wish in parallel
        (`Promise.all`) and merges them into the `profile` computed the same way it already merged
        reviews; also exposes `isMockProfile` (`!fetchedDetail`) for the one place that still needs
        to know. Mock fallback (seed Pals `p1`..`p8`) unchanged in substance: authored feed entries
        in `mocks/playerProfiles.ts` keep their old minimal shape (`MockProfilePost`, no
        `playerId`/`liked`/`createdAt`) and get adapted into a real `FeedPost` in
        `feedPostFromMockEntry` (parsing the old `timeAgo` display string into an approximate ISO
        date) - same "adapt at the boundary" approach `stores/feed.ts`'s `feedPostFromMock` and
        `PostDetailView.vue`'s `postFromMockDetail` already use, rather than reshaping the mock
        literals themselves. `ProfileFeedsTab.vue`'s composer was a dead stub (no v-model, no
        click handler at all) - replaced with the exact same `CreatePostModal` trigger pattern
        `FeedView.vue` uses (readonly input + Photo/Clip/Emoji/Post buttons all open the modal),
        rather than inventing a second composer implementation; its like button now calls
        `feedStore.toggleLike` against a local reactive copy of the `feed` prop (the profile page's
        per-player feed isn't part of `feedStore`'s own `posts`/`following` arrays, so there's
        nothing for `patchPost` to patch in place otherwise) and a per-post tier badge now reads
        `post.tier` instead of a hardcoded "Pal 2". `ProfileWishTab.vue`'s heart toggle takes a new
        `mockToggle` prop (`PlayerProfileView.vue` passes `isMockProfile`): stays interactive
        against the mock fixtures, renders static (no mutation to call) against a DB-backed
        profile, per 3.8b's decision that `wish_items.saved` is Pal-authored state with no
        per-viewer save/unsave endpoint. `ProfileAlbumTab.vue` falls back to "Clip"/"Screenshot"
        when `label` is null. `vue-tsc --build` and `eslint` both clean (same two pre-existing
        unrelated eslint errors noted since 3.1k); `ruff check` clean; confirmed via
        `app.openapi()['paths']` that `/players/{player_id}/feed` registers correctly alongside
        the existing `/players/{player_id}` catch-all and `/album`/`/wish`, same "different path
        shape, no ordering conflict" already established for those two in 3.8b.
  - [x] 3.8i Verification: `vue-tsc --build` clean, `ruff check` clean (backend), `eslint` clean
        on every file touched by 3.8a-3.8h (only the same two pre-existing unrelated errors in
        `StepRates.vue`/`RefundModal.vue`, noted since 3.1k — untouched by this feature). Manual
        browser walkthrough skipped per standing instruction not to run the `run` skill in this
        project.
- [x] 3.9 Wallet & payouts: coin balance ledger, top-up, payout methods, withdrawal requests + connect to Wallet and Withdraw pages
  - [x] 3.9a Backend: `routers/wallet.py` (currently an empty skeleton from 2.1) — `GET /wallet/me`
        (balance from `users.coin_balance`, pending clearance derived from the caller's own
        `accepted`-but-not-`completed` bookings as a Pal, recent activity from `wallet_transactions`
        — mirrors `mockWalletActivity`'s shape), `GET /wallet/topup-packages` (public read of
        `topup_packages`), `POST /wallet/topup` (mock payment — credits `coin_balance` and writes a
        `wallet_transactions` row, `kind='topup'`), `GET /wallet/payout-methods` (Pal's own
        `payout_methods` rows), `GET /wallet/withdrawals` (Pal's own `withdrawals` history),
        `POST /wallet/withdrawals` (validates against balance minus pending clearance, computes
        `fee_coins` at a hardcoded platform-fee pct matching the frontend's existing
        `mockWithdrawalPlatformFeePct = 10`, decrements `coin_balance`, inserts a `withdrawals` row
        plus a `wallet_transactions` row `kind='payout'`). No payout-method create/delete endpoint —
        both pages' "+ Add payout method" stays a disabled stub, no form exists in any mockup, same
        convention as "Edit" in 3.1i.
  - [x] 3.9b Backend: migration seeding `topup_packages` with the 4 rows `mocks/wallet.ts`'s
        `mockTopUpPackages` already authors (495/990/2750/6000 coins) — the 2.3 migration created
        the table with no rows, so `GET /wallet/topup-packages` has nothing to read without this.
        Pushed to the linked project with `bunx supabase db push`.
  - [x] 3.9c Backend: live smoke test against the real Supabase project (a throwaway buyer user
        through real HTTP with a real bearer token against a local uvicorn: fresh
        `GET /wallet/me` is 0 balance/0 pending/empty activity, `GET /wallet/topup-packages`
        returns the 4 seeded rows with correct coins/price/bonus, two `POST /wallet/topup` calls
        credit `coin_balance` by coins+bonus and each writes an activity row with the passed
        payment label, a bogus package id 404s, a non-Pal hitting `GET /wallet/payout-methods`
        404s, no bearer token 401s. A throwaway Pal with 2 `accepted` + 1 `completed` + 1
        `pending` booking seeded directly via the service-role client: `pendingClearanceCoins`
        summed only the 2 `accepted` rows (800), a payout method seeded directly showed up on
        `GET /wallet/payout-methods`, a withdrawal over the available amount (balance minus
        pending) got 409, a bogus payout method id got 404, a withdrawal within the available
        amount got 201 with correct `feeCoins` (10%), debited `coin_balance` by the full
        withdrawal amount, landed both the `withdrawals` and `wallet_transactions` (`kind=payout`)
        rows, and showed up on `GET /wallet/withdrawals`; a 0-coin withdrawal got 422. 30/30
        checks passed with no bugs found. All rows/users cleaned up after, verified empty (no
        leftover `squadup-test.invalid` auth users).
  - [x] 3.9d Frontend: new `stores/wallet.ts` (`balance`/`pendingClearanceCoins`/`activity`/
        `topupPackages`/`payoutMethods`/`withdrawals` state, `fetchWallet`/`fetchTopupPackages`/
        `topUp`/`fetchPayoutMethods`/`fetchWithdrawals`/`requestWithdrawal` actions), same
        mock-fallback resilience convention as `stores/players.ts`/`bookings.ts`/etc. Types
        mirror the backend's camelCase shapes (`WalletActivity`/`TopupPackage`/`PayoutMethod`/
        `Withdrawal`), with `mocks/wallet.ts`'s fixtures adapted at the store boundary
        (`walletActivityFromMock`/etc., same "adapt at the boundary" approach `stores/feed.ts`
        uses) since the mock's `icon`-based `WalletActivity` shape predates real `kind`/`status`
        enum fields. `topUp`/`requestWithdrawal` are real mutations only (no mock fallback), same
        convention as `feedStore.createPost`; `requestWithdrawal` refetches the wallet afterward
        so balance/activity reflect the debit. `vue-tsc --build` and `eslint` both clean.
  - [x] 3.9e Frontend: `WalletView.vue` wired — balance/USD-equivalent and recent activity read from
        the store instead of `mockCurrentUser.coinBalance`/`mockWalletActivity`, "Confirm Top-Up"
        enabled and calls `walletStore.topUp(...)` with a loading/error toast state (was a disabled
        stub). Added a loading guard (was previously absent anywhere in this view) so the zero-balance
        `EmptyState` doesn't flash before the fetch resolves; the empty state's "Top up now" button
        also now purchases the base-rate package directly (no package grid to pick from there).
        Activity icon/color is now derived from the real `kind`/`status` fields via a small
        `activityIcon()`/`activityIconClass()` function pair (replacing the mock-era
        `WalletActivityIcon`-keyed lookup objects), with a new `payout` case (`PhArrowDown`) the mock
        shape never had.
  - [x] 3.9f Frontend: `WithdrawView.vue` wired — available/pending/payout methods/history from the
        store instead of `mocks/wallet.ts`, "Withdraw" enabled and calls
        `walletStore.requestWithdrawal(...)` with a loading/error toast state (was a disabled stub).
        "Available to withdraw" is now `balance - pendingClearanceCoins` (the mock version never
        subtracted pending, unlike the real backend's cap) so the page's own preview matches what
        `POST /wallet/withdrawals` will actually accept. `PlayerEarningsView.vue`'s "Available
        balance"/"Pending clearance"/payout method/history section (explicitly deferred to 3.9 in
        the 3.7e note) wired to the same store data, both "Withdraw" buttons now link to
        `/wallet/withdraw` instead of being disabled stubs; `payoutSchedule`/`nextPayoutDate`
        ("Weekly payout") has no real scheduling concept behind it, so that stays presentation-only
        off `mocks/dashboardStats.ts`, not a blocker for this task. "+ Add payout method" / "Change
        payout settings" stay disabled stubs on both pages, no add/edit form exists in any mockup,
        same convention as 3.1i's "Edit".
  - [x] 3.9g Verification: `vue-tsc --build`, `eslint` (only the same two pre-existing unrelated
        errors noted since 3.1k - `StepRates.vue`/`RefundModal.vue` unused vars), and `ruff check`
        all clean. Manual browser walkthrough skipped per standing instruction not to run the `run`
        skill in this project.
- [x] 3.10 Notifications endpoint (create on booking/message/review/payout events, mark read) + connect to header dropdown and Notifications page
  - [x] 3.10a Backend: new `core/notify.py` (`notify(user_id, type, message)`, a plain
        `notifications` insert) shared by `bookings.py`/`messages.py`/`reviews.py`/`wallet.py`
        rather than duplicating the insert shape in each, same "shared helper, one-directional
        import" approach as 3.8h's cross-router `players.py` → `feed.py` call. `follow`/`service`
        events (both already in the `notification_type` enum from 2.3) are out of scope per the
        checklist line naming only booking/message/review/payout; `gift`/`streak` have no real
        event source at all and stay mock-only in the frontend union.
  - [x] 3.10b Backend: `routers/notifications.py` rewritten from its 2.1 empty skeleton -
        `GET /notifications` (mine, newest first, capped at 50 same as `wallet.py`'s activity
        feed), `POST /notifications/read-all`, `POST /notifications/{id}/read` (404s on a
        notification that isn't the caller's, same ownership-check shape as every other
        `_get_owned_*` helper elsewhere).
  - [x] 3.10c Backend: event wiring. `bookings.py` - `players(display_name, avatar_url, user_id)`
        added to the shared `_SELECT` embed (a new `_booking_names()` helper reads pal
        name/buyer name/pal user_id/service name off it) so `create_booking` notifies the Pal,
        and `accept`/`decline`/`complete` notify the buyer; `cancel` notifies whichever party
        didn't initiate it. Seed-Pal bookings with no `players.user_id` (2.3 note) simply have
        nobody to notify, guarded by an `if pal_user_id` check. `messages.py` - `send_message`
        notifies the thread's other participant with a quoted, truncated (60-char) preview.
        `reviews.py` - `create_review` looks up the reviewed service's Pal `user_id` and notifies
        them. `wallet.py` - `create_withdrawal` notifies the Pal themself once the withdrawal
        lands (status stays `in_progress`, so the copy says "requested"/"processing" rather than
        claiming it's already paid out, unlike the mock fixture's "completed" wording).
  - [x] 3.10d Backend: live smoke test against the real Supabase project (a throwaway buyer + Pal
        through real HTTP with real bearer tokens against a local uvicorn, exercising every wired
        event in sequence: create booking → Pal notified, accept → buyer notified, complete →
        buyer notified, review → Pal notified, decline (2nd booking) → buyer notified, cancel by
        buyer (3rd booking) → Pal notified, send message → other participant notified, top-up +
        withdrawal → Pal notified with the real fee-adjusted coin amount, mark one read, mark all
        read, no-bearer-token 401, non-owner mark-read 404. 25/25 checks passed with no bugs
        found. Cleanup needed to delete each booking/service/player/thread row before the
        `auth.users` delete - confirms the 3.1e note that `auth.users` deletion doesn't cascade
        to `players`/`services`/`bookings` in this schema; not a new issue, just the first smoke
        test in this task to hit every one of those tables at once. All rows/users cleaned up
        after, verified empty.
  - [x] 3.10e Frontend: `stores/notifications.ts` rewritten around real
        `fetchNotifications`/`markAllRead`/`markRead` calls against `/notifications...`, mock
        fallback on `fetchNotifications` failure only (same resilience convention as
        `stores/players.ts`/etc.); the two mutations are real-only, matching
        `feedStore.toggleLike`'s convention. `AppNotification`'s shape (`id`/`type`/`message`/
        `createdAt`/`read`) needed no changes, it already matched `NotificationOut` exactly.
  - [x] 3.10f Frontend: `AppHeader.vue` now fetches notifications whenever a session is
        (re)established (`watch(() => authStore.user, ..., { immediate: true })`), since the bell
        badge/panel need real data across every authenticated page, not just `/notifications` -
        this is the one place in the app a global chrome component owns a fetch a specific view
        doesn't trigger itself. `NotificationsView.vue` additionally fetches on its own mount (a
        direct/deep link to `/notifications` shouldn't depend on header mount order), gained a
        loading guard so the empty state doesn't flash before the fetch resolves (same
        `WalletView.vue` convention from 3.9e), and its "Mark all read" link now awaits the real
        mutation with a toast on failure. `NotificationPanel.vue`'s "Mark all read" and per-row
        click-to-read both call the real mutations too; a failed per-row mark-read stays silent
        (no toast) since a stray unread dot on a dropdown row isn't worth interrupting the user
        for, "Mark all read" failing does surface a toast since it's a deliberate action.
  - [x] 3.10g Verification: `vue-tsc --build`, `eslint`, and `ruff check` all clean (the `eslint`
        run surfaces only the same two pre-existing unrelated errors noted since 3.1k -
        `StepRates.vue`/`RefundModal.vue` unused vars). Manual browser walkthrough skipped per
        standing instruction not to run the `run` skill in this project.
- [x] 3.11 Subscriptions endpoint: recurring buyer→Pal billing state, cancel/resubscribe + connect to Subscriptions page (cut if short)
  - [x] 3.11a Backend: `routers/subscriptions.py` (currently an empty skeleton from 2.1) —
        `GET /subscriptions/mine` (buyer's own `subscriptions` rows joined to `players` for
        `palName`/`rating`/`serviceLabel`, matching `mocks/subscriptions.ts`'s `Subscription`
        shape exactly), `POST /subscriptions` (the `SubscriptionModal` confirm action — body
        `playerId`/`serviceId?`/`billingCycle`; computes `price_coins` server-side off the
        service's price, or a flat default matching the modal's `monthlyPriceCoins = 990`
        fallback if no service/price is passed, with quarterly at the modal's already-established
        3x - 10% math; inserts `status='active'`, `renews_on` = today + 30/90 days), `POST
        /subscriptions/{id}/cancel` (owner-only 404 guard, sets `status='cancelled'`, leaves
        `renews_on` as-is since the frontend already reads it as "access until" once cancelled),
        `POST /subscriptions/{id}/resubscribe` (owner-only, sets `status='active'` and recomputes
        `renews_on` = today + cycle days, moving `SubscriptionsView.vue`'s current client-side
        `resubscribe()` logic server-side).
  - [x] 3.11b Backend: live smoke test against the real Supabase project (two throwaway buyer
        auth users + two throwaway `players` rows inserted directly via the service-role client,
        same pattern as 3.3b, since a Pal here needs no linked user per the 2.3 `user_id` nullable
        note - one Pal also got a `services`/`service_pricing_options` row to exercise the
        service-based price path) through real HTTP with real bearer tokens against a local
        uvicorn: subscribe monthly with a service -> price taken from `service_pricing_options`
        (not the 990 default) and appears correctly in `GET /subscriptions/mine`, subscribe
        quarterly to a second Pal with no service -> default-price 3x-10% math (990 -> 2673),
        cancel the first -> status flips to `cancelled`, `renewsOn` unchanged, resubscribe ->
        status flips back to `active` with a freshly recomputed `renewsOn`, a non-owner's
        cancel/resubscribe on someone else's subscription id both 404, three no-bearer-token
        calls (`GET /mine`, `POST /subscriptions`, cancel) all 401. 27/27 checks passed with no
        bugs found - `_subscription_out`'s price/renewsOn math and the owner-guard 404s were
        correct on the first live run. All rows/users cleaned up after, verified empty.
  - [x] 3.11c Frontend: new `stores/subscriptions.ts` (`list` state, `fetchSubscriptions`/
        `subscribe`/`cancelSubscription`/`resubscribe` actions against `/subscriptions/...`), same
        mock-fallback resilience convention as `stores/wallet.ts`/`notifications.ts`/etc.
        (3.9d/3.10e) — `mocks/subscriptions.ts`'s fixtures adapted at the store boundary on
        fetch failure only, mutations real-only. `Subscription` mirrors the backend's
        `SubscriptionOut` (lowercase `billingCycle`, `playerId`/`playerDisplayName`/`serviceId`
        instead of the mock's `palName` and no ids), so `subscriptionFromMock` adapts the old
        shape rather than reshaping `mocks/subscriptions.ts` itself — same convention as
        `walletActivityFromMock`. Mock-derived rows get `playerId: ''`/`serviceId: null` since
        there's nothing real behind them to cancel/resubscribe anyway. `vue-tsc --build` and
        `eslint` both clean.
  - [x] 3.11d Frontend: `SubscriptionsView.vue` wired to the store instead of its local
        `ref(mockSubscriptions...)` copy — fetch on mount with a loading guard (same
        `WalletView.vue`/`NotificationsView.vue` convention from 3.9e/3.10f), `confirmCancel`/
        `resubscribe` call the real mutations with toast-on-failure instead of mutating the local
        array directly. Also picked up the store's renamed/retyped fields the view hadn't caught
        up to yet: `sub.palName` → `sub.playerDisplayName`, `sub.rating` (string in the mock) is
        now `number | null` (formatted `rating.toFixed(1)` / `'--'`, same convention as
        `PlayerCard.vue`/`ProfileServicesTab.vue`/etc.), and `billingCycle` is lowercase
        (`'monthly' | 'quarterly'`) instead of the mock's capitalized strings — a new
        `billingCycleLabel()` helper capitalizes it for display (badge, Manage popover, and the
        `CancelSubscriptionModal` prop). Resubscribe gets a per-row `resubscribingId` loading
        state on its button, mirroring the per-row loading convention in `PlayerOrdersView.vue`/
        `MyBookingsView.vue`. `vue-tsc --build` and `eslint` both clean (same two pre-existing
        unrelated errors noted since 3.1k).
  - [x] 3.11e Frontend: `ProfileHeader.vue` + `SubscriptionModal.vue` wired — `confirmSubscribe`
        now calls `subscriptionsStore.subscribe(playerId, serviceId, plan)` directly (moved into
        the modal itself, which took on new `playerId`/`serviceId` props from `ProfileHeader`,
        plus a `submitting` guard on the Subscribe button and a toast on failure) instead of just
        emitting a local `subscribed = true` that reset on reload. `ProfileHeader.vue` fetches
        `subscriptionsStore.fetchSubscriptions()` `onMounted` and the button's subscribed state is
        now a computed checking `subscriptionsStore.list` for an active row matching
        `player.id`, replacing the old component-local ref entirely (the `@subscribe` emit was
        dropped since the store list update alone drives the button reactively). `serviceId` is
        passed as `profile.highlightedServiceId`.
  - [x] 3.11f Verification: `vue-tsc --build`, `eslint`, and `ruff check` all clean (same two
        pre-existing unrelated eslint errors noted since 3.1k, `StepRates.vue`/`RefundModal.vue`
        unused vars). Manual browser walkthrough skipped per standing instruction not to run the
        `run` skill in this project.
- [x] 3.12 Estars leaderboard: ranking query over players by category/period + connect to Estars page (cut if short)
  - [x] 3.12a Backend: new `routers/estars.py` (no skeleton exists from 2.1, unlike every other
        router) — `GET /estars/leaderboard`, ranking players by coins earned from `completed`
        bookings within a `period` param (`week`/`month`/`all_time`, rolling 7/30-day windows off
        `created_at`, `all_time`/anything else = no cutoff), with an optional `category` filter,
        aggregated in Python over one `bookings` fetch plus one batched `services` fetch (same
        aggregate-in-Python + batched-highlighted-service pattern as `_match_score`/
        `_compute_earnings`/`list_players`, 3.3a/3.7a/3.2a). No new table (per the 2.3 note this
        is derivable from `bookings`). `category` is each player's highlighted service's `name`
        (`category_by_service_id`, batched like `list_players`'s `services_by_id`); a player with
        no highlighted service or zero coins in the window is simply excluded from the ranking
        rather than shown with a null/zero row. `trend` has no historical rank snapshot to diff
        against, so it's always `'flat'` — same "no data to derive it from" call as 3.7d's dropped
        response-time stat, not dropped from the schema since the frontend type already expects it.
        Registered in `routers/__init__.py` + `routers` list; confirmed via `app.openapi()['paths']`
        that `/estars/leaderboard` registers correctly. `ruff check` clean.
  - [x] 3.12b Backend: live smoke test against the real Supabase project (one throwaway buyer
        user plus four throwaway players/services - Alice/Bob/Carol with `completed` bookings
        this-week/this-month(15d)/all-time(60d) and varying coin totals, Dave with a large
        `pending` booking to confirm non-`completed` bookings are excluded regardless of period).
        All 20 checks passed on the first run: week/month/all_time bucketing, coin-descending
        rank order, `trend` always `'flat'`, and case-insensitive `category` filtering (matching
        `.lower()` in `estars.py`) all matched hand-computed expectations. No bugs found. All
        rows and the throwaway auth user cleaned up after, verified empty.
  - [x] 3.12c Frontend: new `stores/estars.ts` (`fetchLeaderboard(period, category)` against
        `/estars/leaderboard`), same mock-fallback resilience convention as every other Phase 3
        store (`stores/bookings.ts`'s `fetchList`/`fetchIncoming`). No adapter function needed on
        fallback (unlike `stores/subscriptions.ts`'s `subscriptionFromMock`) since
        `mockEstarsLeaderboard`'s entries already satisfy the store's `EstarEntry` type as-is -
        its `category`/`rating` are just narrower (always non-null) than the backend's nullable
        fields. `vue-tsc --build` and `eslint` both clean.
  - [x] 3.12d Frontend: `EstarsLeaderboardView.vue` wired to the store instead of
        `mockEstarsLeaderboard` — period buttons and the category `USelect` trigger a refetch,
        loading guard before the top-three/rest layout renders. `periodParams` maps the UI's
        `'This week'/'This month'/'All time'` labels to the store's `week`/`month`/`all_time`
        values; `estarsCategories[0]` ("All categories") sends no `category` param, matching
        `stores/estars.ts`'s `fetchLeaderboard`. Rating/category are nullable on the real
        `EstarEntry` (unlike the mock type), so both render spots fall back to `'--'`/`'—'`,
        same convention as `SubscriptionsView.vue`'s rating fallback. `vue-tsc --build` and
        `eslint` both clean (same two pre-existing unrelated errors noted since 3.1k).
  - [x] 3.12e Verification: `vue-tsc --build`, `eslint`, and `ruff check` all clean (same two
        pre-existing unrelated eslint errors noted since 3.1k, `StepRates.vue`/`RefundModal.vue`
        unused vars). Manual browser walkthrough skipped per standing instruction not to run the
        `run` skill in this project.
- [x] 3.13 Settings backend: payment cards CRUD, active sessions/device list, account deletion
      (2FA enrollment stays a disabled stub, no backing OTP provider) + connect to Settings tabs
      and the Delete Account modal
  - [x] 3.13a Backend: new `routers/settings.py` — `GET /settings/payment-cards`,
        `PATCH /settings/payment-cards/{id}/default`, `DELETE /settings/payment-cards/{id}`.
        No `POST` reachable from the UI: `SettingsPaymentsTab.vue`'s "+ Add card" is a disabled
        stub with no card-capture form (real tokenization is Phase 4 payment integration, same
        boundary as `SettingsPaymentsTab.vue`'s "+ Add payout method"), so seed a couple of rows
        per throwaway user during the 3.13d smoke test instead of exposing create. Setting a
        default clears every other card's `is_default` for the caller first (two sequential
        updates - no DB constraint enforces "at most one default", the guard lives entirely in
        the handler), then flips the target row. Owner-guarded via a new `_get_owned_card`
        (`payment_cards.user_id = caller`, 404 on any mismatch), same shape as `players.py`'s
        `_get_owned_service`. `ruff check` clean; routes confirmed registered via
        `app.openapi()['paths']`.
  - [x] 3.13b Backend: active sessions — `GET /settings/sessions`, `DELETE
        /settings/sessions/{id}`, `POST /settings/sessions/sign-out-others`, owner-guarded the
        same way as payment cards (`_get_owned_session`). Resolved the write-path decision this
        line raised: added a fourth route, `POST /settings/sessions` (upsert), meant to be called
        from the frontend on auth init in 3.13g - "smoke-test-seeded only" would leave the list
        permanently empty for every real account forever, unlike payment cards where that's an
        acceptable Phase-4-boundary trade-off since a real add-card flow is coming later. Upserts
        by `(user_id, device)`, where `device` is parsed from the `User-Agent` header into a
        `"{Browser} · {OS}"` string (`_parse_device`, matching `mocks/settings.ts`'s
        `"Chrome · macOS"` format) since there's no per-machine client-generated id to key on;
        each touch also flips `is_current` on that row and clears it on every other session for
        the user. `location` stays null - no IP-geolocation service wired, same "column
        provisioned ahead of the feature that fills it" call the 2.4 storage-buckets note made for
        `rank_verification_url`. `sign-out-others` deletes every non-current row rather than
        calling Supabase's admin `sign_out(jwt, scope="others")` API - `active_sessions` is its
        own bookkeeping table decoupled from real GoTrue sessions (2.3 never linked the two), and
        1.14 already established this list as presentation-only ("'Sign out' removes a session
        from the local array"), so wiring real per-device JWT revocation here would be scope
        beyond what either this checklist line or the existing frontend behavior asks for. `ruff
        check` clean; routes confirmed registered via `app.openapi()['paths']`.
  - [x] 3.13c Backend: account deletion — `DELETE /users/me`
        (`routers/users.py`), calling `supabase.auth.admin.delete_user()` with no Python-side
        pre-cleanup. Resolved the 3.1e cascade gap via migration instead of Python: a new
        `supabase/migrations/20260825141921_account_deletion_cascade.sql` re-points every FK on
        the path from `auth.users` down (`players.user_id`, plus every `NO ACTION` edge that
        would've otherwise blocked the delete — `bookings`/`subscriptions`/`withdrawals`'s
        `player_id`, `bookings`/`subscriptions`/`message_threads`/`reviews`/`comments`/
        `order_cancellations`/`order_disputes`'s user-referencing columns) to `on delete
        cascade`, so one `delete_user()` call walks the whole graph — `auth.users` → `public.users`
        → `players` → `services` → everything already cascading from those two (pricing options,
        promotions, album/wish, posts, payout methods, admin flags, reviews, saved items) — in a
        single DB transaction. `admin_flags.reported_by` got `on delete set null` instead (it's
        nullable and a flag against a *different* player should outlive the reporter's account).
        Accepted tradeoff, documented in the migration: this also erases bookings/reviews/
        messages/subscriptions/disputes the deleted account was party to, including the
        counterparty's copy — no soft-delete/anonymization layer exists in this schema, and a
        hard delete is what "Delete Account" already promises in the Settings copy. Pushed to the
        linked project with `bunx supabase db push`, migration applied clean on the first try
        (confirms every guessed default constraint name — Postgres's `{table}_{column}_fkey`
        convention — was right). `ruff check` clean; `DELETE /users/me` confirmed registered via
        `app.openapi()['paths']`.
  - [x] 3.13d Backend: live smoke test against the real Supabase project (throwaway user through
        real HTTP with a real bearer token: seed + list + set-default + remove a payment card,
        seed + list a session + sign-out-one + sign-out-others, then delete the account and
        confirm the user/player/service rows are actually gone). All 35 checks passed on the
        first run, no bugs found - also exercised `POST /settings/sessions`'s upsert-by-device
        (touching twice with the same `User-Agent` reused the same row rather than duplicating
        it) and confirmed the 3.13c cascade migration: after `DELETE /users/me`, the seeded
        player/service/payment_cards/active_sessions rows and the `auth.users` row itself were
        all gone, not just `public.users`. Smoke script was a throwaway (real HTTP against a
        local uvicorn, admin client for seeding/teardown), not committed.
  - [x] 3.13e Frontend: new `stores/settings.ts` wired to `/settings/...` — `paymentCards`
        (list/set-default/remove) and `sessions` (list/sign-out-one/sign-out-others/`touchSession`
        upsert for 3.13g), each with its own loading/error state and mock fallback on failure,
        same convention as every other Phase 3 store. `PaymentCard` mirrors `PaymentCardOut`
        exactly, so `mockPaymentCards` spread-copies straight into it with no converter. `SessionOut`
        doesn't get the same treatment: it's raw-timestamp (`lastActiveAt`) and nullable
        (`device`/`location`), while `mocks/settings.ts`'s pre-existing `ActiveSession` already
        has friendly display fields (`lastActive`/`current`) that `SettingsSecurityTab.vue` (not
        yet wired, that's 3.13g) reads directly — kept that shape and added `sessionFromApi` to
        adapt at the store boundary (`isCurrent` → `'active now'` / `formatTimeAgo(lastActiveAt)`),
        same call `stores/wallet.ts`'s `walletActivityFromMock` made rather than reshaping the
        mock file itself.
  - [x] 3.13f Frontend: `SettingsPaymentsTab.vue` wired to the store for list/set-default/remove
        — `onMounted` calls `fetchPaymentCards()`, a loading line and "No payment methods yet"
        empty state cover the card list, and the "..." menu's Set default/Remove actions are now
        async with a per-card `busyCardId` (disables + spinners the trigger button, same
        `UButton` `loading` pattern as `PlayerServicesView.vue`) and a toast on failure. "+ Add
        card" and "+ Add payout method" stay disabled stubs (no change, see 3.13a). Payout
        method/schedule/currency/auto-top-up sections are untouched — they're the Squad Coin
        wallet, not `payment_cards`, out of this task's scope. `vue-tsc --build` clean; `eslint`
        clean (same two pre-existing unrelated errors noted since 3.1k —
        `StepRates.vue`/`RefundModal.vue` unused vars).
  - [x] 3.13g Frontend: `SettingsSecurityTab.vue` wired to the store — `onMounted` calls
        `fetchSessions()` with loading/"No active sessions" empty states (same convention as
        3.13f), "Sign out" gets a per-session `signingOutId` busy state and "Sign out of all
        other devices" its own busy flag, both with a toast on failure. `DeleteAccountModal`
        confirm calls a new `authStore.deleteAccount()` (`stores/auth.ts` — `DELETE /users/me`
        then `supabase.auth.signOut()` + `reset()`, since the account's refresh token is dead
        once the row is gone), guarded by a `deletingAccount` ref against double-fire (same
        pattern `PlayerServicesView.vue`'s `handleDelete` used, `ConfirmModal` has no built-in
        loading prop), then routes to `/`; a failure toasts instead and leaves the modal open.
        Also resolved `stores/settings.ts`'s `touchSession` upsert, left dangling since 3.13e:
        `stores/auth.ts`'s `init()` now calls it once after the initial session/user load so the
        Security tab's session list reflects real logins instead of staying empty forever.
        Two-factor authentication stays a disabled/inert toggle (`TwoFactorAuthModal` untouched,
        no backend call) since there's no OTP provider to back it, same boundary as the
        payment-card "+ Add" stubs. `SettingsAccountTab.vue`'s "Deactivate account" also stays a
        disabled stub, it's a separate action from deletion and out of this task's scope line.
  - [x] 3.13h Verification: `vue-tsc --build`, `eslint`, and `ruff check` all clean (same two
        pre-existing unrelated eslint errors noted since 3.1k — `StepRates.vue`/`RefundModal.vue`
        unused vars). Manual browser walkthrough skipped per standing instruction not to run the
        `run` skill in this project.
- [x] 3.14 Admin endpoints: player verification/flagging, dispute handling (using the `AdminFlaggedPlayer`/`AdminDispute` shapes in `mocks/admin.ts`) (cut if short)
  - [x] 3.14a Backend: new `routers/admin.py` (currently an empty stub) — `GET /admin/flagged-players`
        (join `admin_flags` → `players` for `displayName`/`avatarUrl`, and → `users` via
        `reported_by` for a display name, shape matches `AdminFlaggedPlayer`) and
        `PATCH /admin/flagged-players/{id}/status` (body: `status`, expected to be one of
        `flagged_player_status`'s four values, matching `AdminFlaggedPlayersPanel.vue`'s Dismiss/
        Reviewing/Take action buttons — not validated against the enum in Python, same
        pass-through-to-Postgres convention as `CancelIn.refund_option`/`DisputeIn.outcome` in
        `routers/bookings.py`). No auth dependency — `stores/admin.ts`'s mock-credential gate
        (`admin@squadup.gg`, session-only) is explicitly the only guard until real admin auth
        ships (per the 1.15 checkpoint note), so these routes stay open like the rest of the
        unauthenticated surface, not behind `get_current_user_id`.
  - [x] 3.14b Backend: `GET /admin/disputes` (join `order_disputes` → `bookings` → Pal `players`
        + buyer `users` for `orderNumber`/`buyerName`/`palName`/`serviceLabel`, shape matches
        `AdminDispute`) and `PATCH /admin/disputes/{id}/status` (one of `dispute_status`'s four
        values, pass-through-to-Postgres like `flagged-players/{id}/status`). `serviceLabel` is
        built from `bookings.service_type_label` + `quantity` (e.g. "Ranked Duo · 3 sessions") —
        `price_unit` (`/Game`, `/2 hr`, `/order`, ...) has no consistent pluralizable unit across
        service types, so "session(s)" is used generically rather than guessing one. Both
        `resolved`/`refunded` set `order_disputes.resolved_at`; "Refund buyer" only flips status
        (+ that timestamp) — no wallet crediting, matching the existing precedent that
        `order_cancellations`/`order_disputes`'s `refund_coins` is already just a recorded amount
        with no `wallet_transactions` write anywhere in the codebase (real payment/refund
        integration is Phase 4). Dispute creation itself already exists (`POST
        /bookings/{id}/dispute`, 2.3-era) — this task only adds the admin read/status-update side.
  - [x] 3.14c Backend: `GET /admin/overview` — `totalUsers`/`totalPals` (`count="exact", head=True`
        on `users`/`players`), `ordersToday` (`bookings` count where `created_at >=` today's UTC
        midnight), `coinsInEscrow` (in-flight defined as `status in ('pending', 'accepted')` —
        the two states where a booking is neither paid out (`completed`) nor never charged
        (`declined`) — `total_coins` fetched and summed in Python, same "aggregate in Python"
        convention as 3.3a's match scoring), `reportsThisWeek` (`admin_flags` fetched since 6 days
        ago, bucketed by `date.weekday()` into `M`/`T`/`W`/`T`/`F`/`S`/`S`, matching
        `mockAdminOverviewStats`'s shape exactly incl. duplicate `T`/`S` labels). Register
        `admin.router` stays as-is in `routers/__init__.py` (already wired). `vue-tsc --build`
        n/a (backend-only); `ruff check` clean.
  - [x] 3.14d Backend: live smoke test against the real Supabase project (throwaway flagged-player
        and dispute rows through real HTTP: list + status-update both endpoints, list overview,
        confirm numbers move), same shape as 3.13d. Throwaway script, not committed. Full chain
        (two throwaway auth users, a Pal `player`/`service`, a `completed` booking + a `pending`
        one, an `admin_flags` row, an `order_disputes` row) created via the service-role client,
        then exercised through real HTTP against a local uvicorn: `GET /admin/flagged-players`
        shows the joined `displayName`/`reportedBy`, `PATCH .../status` moves it to `reviewing`
        and 404s on an unknown id; `GET /admin/disputes` shows the joined `orderNumber`/
        `serviceLabel` ("Ranked Duo · 3 sessions")/`totalCoins`, `PATCH .../status` moves
        `investigating` → `refunded` (DB-level `resolved_at` stamped on the terminal status,
        confirmed directly since `AdminDisputeOut` intentionally has no `resolvedAt` field,
        matching `mocks/admin.ts`'s `AdminDispute` shape) and 404s on an unknown id; `GET
        /admin/overview` reflects `totalUsers`/`totalPals`/`ordersToday` and an independently
        DB-summed `coinsInEscrow` that correctly excludes the `completed` booking and includes
        the `pending` one, `reportsThisWeek` confirmed as a 7-day trailing window (not a
        calendar week) with today's count including the new flag. 31/31 checks passed, no bugs
        found - `admin.py`'s joins/status-transition logic were correct on the first live run.
        All rows/users cleaned up after, verified empty.
  - [x] 3.14e Frontend: extend `stores/admin.ts` with `flaggedPlayers`/`disputes`/`overview` state
        fetched from `/admin/...`, mock fallback on failure (same convention as every other Phase 3
        store) — the existing `isAuthenticated`/`login`/`logout` mock-credential gate is untouched,
        this task only adds data fetching once past that gate. Also added
        `updateFlaggedPlayerStatus`/`updateDisputeStatus` (`PATCH .../status`, patches the row back
        into the list in place) alongside the fetches, since 3.14f/g's panels need a store action to
        call rather than mutating their local mock-seeded refs directly. Response types are the
        existing `AdminFlaggedPlayer`/`AdminDispute`/`AdminOverviewStats` from `mocks/admin.ts`
        unchanged — `CamelModel`'s camelCase output lines up field-for-field with each, no separate
        API-response type or converter needed (confirmed against `routers/admin.py`'s
        `AdminFlaggedPlayerOut`/`AdminDisputeOut`/`AdminOverviewOut`). `vue-tsc --build` and `eslint`
        both clean (same two pre-existing unrelated eslint errors noted since 3.1k).
  - [x] 3.14f Frontend: `AdminFlaggedPlayersPanel.vue` wired to the store — `onMounted` fetch,
        loading/empty states (same pattern as 3.13f/g), Dismiss/Reviewing/Take action buttons call
        the store's status-update action with a busy state + toast on failure instead of mutating
        the local `flags` ref directly. `rows` now filters/sorts `adminStore.flaggedPlayers`
        directly rather than a locally-seeded copy; a single `statusUpdating` busy flag (not
        per-row, since only one row can be open in the review modal at a time) disables all three
        action buttons and shows `UButton`'s `loading` spinner during the `PATCH`, with a toast on
        failure. Loading/error states above the table follow the loading-text /
        `UEmpty`-with-Retry convention from `PlayerServicesView.vue` (3.1i) rather than 3.13f/g's
        plain-text-only version, since this panel already had a `UEmpty` for the zero-results case
        to be consistent with. `vue-tsc --build` and `eslint` both clean (same two pre-existing
        unrelated eslint errors noted since 3.1k).
  - [x] 3.14g Frontend: `AdminDisputesPanel.vue` wired the same way — Investigate/Resolve/Refund
        buyer call the store's status-update action, with loading/empty states and a single
        `statusUpdating` busy flag on the review modal's three buttons, matching 3.14f's
        `AdminFlaggedPlayersPanel.vue` pattern exactly. `vue-tsc --build` and `eslint` both clean.
  - [x] 3.14h Frontend: `AdminOverviewPanel.vue` wired to the store's `overview`/`flaggedPlayers`/
        `disputes` state instead of the `mocks/admin.ts` imports. `onMounted` fetches all three;
        the stat cards/reports-this-week chart gate on `overview` with the same loading-text /
        `UEmpty`-with-Retry convention as 3.14f/g, while the two "recent" lists (already capped
        to 3 items) read `flaggedPlayers`/`disputes` directly and just show a plain empty line
        when a list comes back empty, rather than duplicating three separate loading/error gates
        on one summary page.
  - [x] 3.14i Verification: `vue-tsc --build`, `eslint`, `ruff check` all clean; manual browser
        walkthrough skipped per standing instruction not to run the `run` skill in this project.
- [x] 3.15 Docker + Docker Compose for frontend + backend (match Niyay/PawMart setup)
  - [x] 3.15a `backend/Dockerfile` (`python:3.11-slim` + `uv`, two-stage `uv sync` - deps then
        project - for layer caching) + `backend/.dockerignore`, copied from PawMart's since
        squadup's backend already matches its `src/`-layout + `uv`/`pyproject.toml` shape exactly
        (`backend.main:app` entrypoint, no path changes needed).
  - [x] 3.15b `frontend/Dockerfile` (`oven/bun:1`, install-then-copy for layer caching) +
        `frontend/.dockerignore`, also copied from PawMart's (same bun/Vite setup).
  - [x] 3.15c Root `docker-compose.yml` - two services (`backend` on 8000, `frontend` on 5173),
        each bind-mounting its source dir for live reload (`uv run uvicorn --reload` /
        `bun run dev --host 0.0.0.0`) with a named volume over `.venv`/`node_modules` so the
        container's own install isn't shadowed by the host bind mount, `env_file` pointing at
        each app's existing `.env` (Supabase creds, `VITE_API_URL`, etc. - no new env vars
        needed, `VITE_API_URL=http://localhost:8000` already works since the frontend calls it
        from the browser, not container-to-container). Niyay has no Docker setup to match
        (frontend/backend only, no `docker-compose.yml` or Dockerfiles present), so PawMart was
        the sole reference.
  - [x] 3.15d Verification: `docker compose build` (both images built clean), `docker compose up
        -d` (both containers started, no errors in logs), confirmed `GET /health` on the backend
        (200 `{"status":"ok"}`) and `GET /` on the frontend (200, Vite dev server serving) both
        respond, then `docker compose down` to tear back down.
- [ ] 3.16 Clean out mock/demo data and fallback logic (do last, once every 3.x feature above is
      backend-wired)
  - [ ] 3.16a Audit every store's mock-fallback path (`stores/players.ts`, `bookings.ts`,
        `messages.ts`, etc. — the "same resilience convention as 3.1j/3.2d/3.4c/3.5d" pattern used
        throughout Phase 3) and remove the try/catch-to-mock branches now that each endpoint is
        real and stable
  - [ ] 3.16b Delete the now-unreferenced fixtures under `frontend/src/mocks/` (players, bookings,
        messages, admin, feed, etc.)
  - [ ] 3.16c Remove the client-side merge of seed Pals `p1`..`p8` into Browse Players/Player
        Profile (`PlayersView.vue`'s `allPlayers`) now that 3.17's seeded accounts are real DB rows
        instead
  - [ ] 3.16d Verify via `vue-tsc --build`/`eslint` plus a manual walkthrough that no page silently
        regresses to an empty state now that the mock fallback is gone
- [ ] 3.17 Seed script: populate the real Supabase project with realistic demo content so the
      marketplace looks alive (not test/throwaway rows — meant to stay through launch)
  - [ ] 3.17a Backend: a one-off script (e.g. `backend/scripts/seed_demo_data.py`) using the
        service-role client's admin API (`auth.admin.createUser`) to create a few hundred
        `auth.users` rows with placeholder (non-deliverable) emails — no real Gmail needed since
        these accounts are never meant to log in, just to exist as FK targets, same as the
        `on_auth_user_created` trigger from `auth_wiring.sql` handles for a real Google signup.
        Then create matching realistic `players`/`services`/`service_pricing_options`/
        `service_promotions` rows (varied games/ranks/roles/pricing) for each
  - [ ] 3.17b Seed a smaller number of `bookings`/reviews and `message_threads`/`messages` between
        seeded accounts so Player Dashboard/Order history/Messages thread lists have real
        history to show, not empty states — this is just for populated-looking history, not a
        substitute for the live two-way Realtime demo (that stays on the 2 real Gmail accounts
        signed in for that purpose)
  - [ ] 3.17c Make the script idempotent (safe to re-run without duplicating) or pair it with a
        teardown script that deletes every seeded row by a marker (e.g. a shared email domain
        suffix), so the seed set can be regenerated or wiped cleanly
  - [ ] 3.17d Verification: run against the linked Supabase project, spot-check row counts and
        relations, confirm Browse Players/Player Profile/Dashboard render populated real data end
        to end with no mock fallback needed

## Phase 4 — Payment: Stripe / Bakong KHQR (moved up ahead of 3.16/3.17, see Status)

**Scope call (2026-08-25):** real money enters the platform exclusively through **Wallet
Top-up** (buy Squad Coin with a card/QR); Checkout's booking payment stays **Squad Coin
balance only**. The previously-offered "Credit / debit card" option at Checkout is dropped
rather than wired to a second, direct per-booking charge — one money-in path, fits the
coin-economy design already established (mocks/wallet.ts's $1 = 99 SC rate, etc.). This
also means the old "payment status → booking confirmation" line (a booking flips to
confirmed once a checkout-time payment clears) doesn't apply the way it was originally
scoped; what actually needs wiring instead is real coin *ledger* movement on the booking
lifecycle itself (4.2 below), since Checkout never touches a payment processor at all.

**Integration pattern (revised same day):** first pass used Stripe-hosted Checkout (redirect)
+ a webhook to credit the wallet async. Switched to match the sibling PawMart project's
pattern instead: a `PaymentIntent` confirmed **client-side** with Stripe Elements (a card
form embedded on `/wallet`), then the backend **re-verifies it synchronously** against the
Stripe API (`stripe.PaymentIntent.retrieve`, checking `status`/`amount`/`metadata.user_id`)
in the same request that credits the wallet. No webhook, no `STRIPE_WEBHOOK_SECRET`, no
Stripe CLI needed for local dev — trades a bit of robustness against a dropped connection
between "card charged" and "wallet credited" for a much simpler setup, acceptable for this
project's scope. `wallet_transactions.stripe_session_id` (4.1b) was renamed to
`stripe_payment_intent_id` in a follow-up migration - same idempotency-key role, different
kind of Stripe id.

- [ ] 4.1 Stripe integration for Wallet Top-up (do first)
  - [x] 4.1a Backend: `stripe` dependency (`backend/pyproject.toml`, added via `uv add stripe`) +
        `Settings.stripe_secret_key` (`core/config.py`, a required `str` - empty string until
        filled in, not `Optional`, so a missing key fails loud the moment a Stripe call is
        attempted rather than silently). Placeholder in `backend/.env`/`backend/.env.example`
        (`STRIPE_SECRET_KEY`) - **the live test-mode secret key is filled into `backend/.env`**
        (user added it directly). No webhook secret needed, see the pattern note above.
  - [x] 4.1b Backend: `supabase/migrations/20260825160000_stripe_topup.sql` adds
        `wallet_transactions.stripe_session_id text unique` (nullable); a same-day follow-up
        `supabase/migrations/20260825163000_stripe_topup_payment_intent.sql` renames it to
        `stripe_payment_intent_id` once the pattern switched. Both pushed to the linked project
        with `bunx supabase db push`.
  - [x] 4.1c Backend: `POST /wallet/topup/payment-intent` (`routers/wallet.py`) - creates a
        Stripe `PaymentIntent` for the chosen `topup_package_id`'s dollar amount (in cents),
        `metadata` carries `user_id`/`package_id`, returns `{ clientSecret, paymentIntentId }`
        for the frontend to confirm client-side. Nothing is credited by this call itself -
        proving a client hit the endpoint proves nothing, which was the old mock `POST /topup`'s
        exact flaw.
  - [x] 4.1d Backend: `POST /wallet/topup` (`routers/wallet.py`) - the actual credit. Re-fetches
        the `PaymentIntent` from Stripe (`stripe.PaymentIntent.retrieve`) and checks
        `metadata.user_id` matches the caller, `status == 'succeeded'`, and `amount` matches the
        package price, before crediting `coin_balance` + writing the `wallet_transactions` row
        (`stripe_payment_intent_id` set). The unique constraint from 4.1b/the rename migration is
        the idempotency guard - a second `POST /topup` with the same `payment_intent_id` hits a
        DB conflict, caught and turned into a 400 "already been used", same shape as PawMart's
        `orders.py`.
  - [x] 4.1e Backend: the old direct-credit mock `POST /wallet/topup` is gone, replaced in place
        by 4.1c/d above (it was explicitly documented as "no real processor wired, that's
        Phase 4"; nothing else called it).
  - [x] 4.1f Backend: live smoke test in Stripe test mode against the real Supabase project and a
        running local uvicorn - a throwaway script created two real `auth.users` (buyer + a second
        user), signed in for real bearer tokens (via a separate anon-keyed client from the
        admin-key client, per 4.2d's lesson about `sign_out` revoking the token server-side rather
        than just clearing local state - hit that exact bug on the first run, fixed by dropping the
        `sign_out()` calls between sign-ins), then exercised `POST /wallet/topup/payment-intent` +
        `stripe.PaymentIntent.confirm(..., payment_method="pm_card_visa")` (Stripe's standard
        test-mode PaymentMethod id, no Stripe.js needed server-side) against `POST /wallet/topup`.
        All 9 checks passed: a nonexistent `payment_intent_id` 400s and leaves the balance
        untouched; a real PaymentIntent belonging to a different user 403s ("Not your payment") and
        leaves the balance untouched; a genuine confirmed payment 201s and credits exactly the
        package's `coins + bonus_coins`; replaying the same `payment_intent_id` 400s
        ("already been used") and does not double-credit. Throwaway users deleted after
        (`auth.admin.delete_user`) and verified cascaded cleanly - no leftover `auth.users` rows,
        no orphaned `wallet_transactions` rows.
  - [x] 4.1g Frontend: `@stripe/stripe-js` dependency (`bun add`) + `lib/stripe.ts`
        (`loadStripe(VITE_STRIPE_PUBLISHABLE_KEY)`, same shape as PawMart's), publishable-key
        placeholder in `frontend/.env`/`.env.example` - **still needs the real `pk_test_...` key
        from the user**, same Stripe dashboard page as the secret key.
  - [x] 4.1h Frontend: `stores/wallet.ts`'s `topUp` action split into `createTopupPaymentIntent`
        (calls `/wallet/topup/payment-intent`) and `confirmTopup` (calls `/wallet/topup`,
        updates `balance`/`pendingClearanceCoins`/`activity` from the response) - the split
        matches the two backend calls `WalletView.vue` now makes around the client-side
        `stripe.confirmCardPayment` step in between.
  - [x] 4.1i Frontend: `WalletView.vue` mounts a Stripe Card Element into an always-visible "Card
        details" box (same `mountCardElement`/`cardElement.on('change', ...)` pattern as
        PawMart's `CheckoutView.vue`, minus the multi-step wizard - this page has one step).
        "Confirm Top-Up" now: creates the PaymentIntent, calls `stripe.confirmCardPayment`,
        then `confirmTopup` on success, with a toast on any failure (declined card, backend
        rejection, etc.). Restructured the page so the package grid/card form/activity list
        render unconditionally instead of being swapped out entirely by the zero-balance
        `EmptyState` - the card form has to exist for a first-time top-up too, so only the
        balance-card-vs-empty-banner hero at the top still forks on `balance === 0`. The old
        "Pay with" card-brand `USelect` (`mockPaymentCards`) is gone - the real Stripe form
        replaced it.
  - [x] 4.1j Frontend: dropped Checkout's "Credit / debit card" button from `CheckoutView.vue`'s
        payment-method section per this task's scope call above (every booking pays with Squad
        Coin balance) — replaced with a static "Squad Coin balance" row (no longer a toggle,
        there's only one option) plus a link to Wallet Top-up for a short balance. `PaymentMethod`
        in `stores/bookings.ts` was **not** narrowed to `'coins'` — it stays `'coins' | 'card'`
        since one historical mock booking (`mocks/bookings.ts`) legitimately used `'card'` as a
        past order's record; only the picker UI is gone, the type still describes what a booking
        *was* paid with, not what's offered going forward.
  - [x] 4.1k Verification: `vue-tsc --build`, `eslint`, `ruff check` all clean (the only eslint
        hits are the same two pre-existing unrelated errors noted since 3.1k). Manual browser
        walkthrough (a real Stripe test-mode top-up) left to the user per standing instruction
        not to run the `run` skill in this project — also needs the frontend publishable key
        filled in first.
- [x] 4.2 Wire real Squad Coin ledger movement into the booking lifecycle — deduct the buyer's
      `coin_balance` when a booking is placed, credit the Pal's on completion. Also covers
      cancel/decline/dispute refund paths (`order_cancellations`/`order_disputes`'s
      `refund_coins`) actually crediting back.
  - [x] 4.2a Backend: `core/wallet.py` - new `get_coin_balance()`/`adjust_coin_balance()` shared
        helper (mirrors `core/notify.py`'s role for notifications) so every ledger movement does
        the same read-balance -> guard-against-negative -> update `coin_balance` -> insert
        `wallet_transactions` row in one place, with an optional `booking_id` (the column already
        existed on `wallet_transactions`, unused until now) linking the transaction back to its
        booking. Deliberately doesn't touch `routers/wallet.py`'s own topup/withdrawal
        read-modify-write - those insert the `wallet_transactions` row *before* crediting so a
        replayed Stripe `payment_intent_id`'s unique constraint blocks a double-credit, an
        ordering this new helper doesn't need (and would break) for booking events.
  - [x] 4.2b Backend: `routers/bookings.py` wired to the new helper - `create_booking` pre-checks
        the buyer's balance (so an underfunded buyer never gets an orphaned unpaid `pending` row)
        then debits `total_coins` (kind=`order`) once the booking row exists; `complete_booking`
        credits the Pal `total_coins` (kind=`order`) - no `players.user_id` lookup needed since
        `_require_pal_booking` already proved the caller *is* that Pal; `decline_booking` refunds
        the buyer in full (kind=`refund`) since a declined order was never fulfilled; `cancel_booking`
        credits the buyer exactly `payload.refund_coins` (kind=`refund`, skipped entirely when 0)
        rather than assuming a fixed refund amount, since the cancellation reason/refund-option
        logic living client-side in `CancelOrderModal` already computed that number.
  - [x] 4.2c Backend: `routers/admin.py`'s `update_dispute_status` wired so the Disputes tab's
        "Refund" button actually credits the buyer - only on the transition *into* `refunded`
        (guarded against a redundant re-click double-crediting), reading `refund_coins` off the
        `order_disputes` row (`dispute_booking`, 3.4a, only ever populates it for a `full_refund`
        request - a `partial_refund`/`reporting` dispute has nothing to credit yet, since no admin
        UI exists to enter a partial amount). A plain report (`POST /bookings/{id}/dispute`)
        still never credits anything on its own - only an admin's explicit `refunded` status does.
  - [x] 4.2d Backend: live smoke test against the real Supabase project (two throwaway users -
        buyer + Pal - through real HTTP with real bearer tokens against a local uvicorn: create ->
        buyer debited exactly `total_coins` with a `booking_id`-linked `order` transaction ->
        insufficient-balance booking rejected with 409 and balance left untouched -> accept ->
        complete -> Pal credited `total_coins` -> a second booking declined -> buyer refunded in
        full -> a third booking cancelled with a 40-coin partial refund -> buyer credited exactly
        40 -> a fourth cancelled with `refundCoins: 0` -> buyer credited nothing -> a fifth
        completed then disputed -> the report alone credits nothing -> admin sets `investigating`
        -> still nothing credited -> admin sets `refunded` -> buyer credited the full amount ->
        re-setting `refunded` a second time does not double-credit). All 27 checks passed on the
        first run; all throwaway users/rows cleaned up and verified empty after. Caught one bug
        only a live run surfaces: the smoke script's own first draft called `sign_in_with_password`
        on the same client used for `auth.admin.create_user`, which silently swapped that client's
        session onto the just-created user's own JWT and 403'd the *next* admin call - fixed by
        signing in through a separate anon-keyed client, unrelated to `bookings.py`/`admin.py`
        themselves (both were correct on the first pass).
  - [x] 4.2e Verification: `ruff check` clean across the backend. No frontend changes were needed
        for this task - `stores/bookings.ts`'s existing `placeOrder`/`declineBooking`/
        `cancelBooking`/`reportIssue` calls already hit these same endpoints and refetch the
        wallet-adjacent state (My Bookings/Orders lists) afterward, so the real balance movement
        is visible through the UI with no client-side changes.
- [x] 4.3 Manual platform commission tracking (%, recorded per booking — no escrow yet)
  - [x] 4.3a Backend: `Settings.platform_commission_pct` (`core/config.py`, env
        `PLATFORM_COMMISSION_PCT`, default `15.0` per recap_squadup.md's "e.g. 10-15%") +
        migration adding `bookings.commission_pct numeric` / `bookings.commission_coins integer`
        (both default 0, only ever populated once a booking completes). Pushed to the linked
        project with `bunx supabase db push`.
  - [x] 4.3b Backend: `complete_booking` (`routers/bookings.py`) computes
        `commission_coins = round(total_coins * commission_pct / 100)` off the configured rate and
        writes both columns alongside the `completed` status update; `BookingOut` exposes them.
        No coin balance touched by this - the Pal is still credited the full `total_coins`, this
        is tracking only (recap_squadup.md's "commission tracked manually", not real escrow - see
        4.5).
  - [x] 4.3c Backend: `/admin/overview` sums `commission_coins` across `completed` bookings into a
        new `total_commission_coins` field, giving admin a running platform-revenue figure.
  - [x] 4.3d Frontend: `AdminOverviewPanel.vue` + `mocks/admin.ts`'s `AdminOverviewStats` type
        (the shape `stores/admin.ts`'s `fetchOverview` already types the real response against)
        wired to render `totalCommissionCoins` as a 5th overview stat tile (grid widened to
        `lg:grid-cols-5`).
  - [x] 4.3e Verification: `ruff check` clean, `vue-tsc --build` clean, `eslint` clean apart from
        the same two pre-existing unrelated errors noted since 3.1k/4.1k
        (`StepRates.vue`/`RefundModal.vue`, untouched by this task).
- [ ] 4.4 Bakong KHQR integration (do last — scope/complexity TBD when we get there, including
      whether it plugs in at Wallet Top-up like Stripe or stays a Checkout-time payment method)
      — generate QR, MVP manual payment verification
- [ ] 4.5 Note in final report: proper escrow (user → platform → player) is a post-launch
      enhancement, not built for submission

---

## Cut list (only if time runs out)

- Admin panel (1.15, 3.14)
- Earnings tracker — fall back to plain booking history (3.7)
- Subscriptions backend — fall back to the static mock page as-is (3.11)
- Estars leaderboard backend — fall back to the static mock ranking as-is (3.12)
