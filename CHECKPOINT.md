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
- **2026-09-04 follow-up:** `mockCurrentUser.displayName`/`.email` reads in the header, feed
  sidebar, dashboard sidebar/greeting, create-post modal, and Settings' Profile/Account tabs now
  prefer `authStore.user?.displayName`/`.email` (falling back to the mock only when signed out),
  so a real Google account's name/email show instead of the "Dara Chan" placeholder. Other
  `mockCurrentUser` fields (`coinBalance`, `playerId` in a few spots) are still unmigrated —
  same pervasive-reads gap as above, left for 3.16 or further one-off follow-ups.

**Booking against a seed Pal (found 2026-09-04):** `POST /bookings` only works against a real
`services` row — seed Pals `p1`..`p8` (`mocks/playerProfiles.ts`) are demo-only fixtures with
hand-authored non-uuid ids (`"main"`, `"p2"`, ...), not real database rows, so Checkout's "Place
order" against one 500'd (`invalid input syntax for type uuid`). Fixed on both ends: a new
`utils/id.ts`'s `isRealId()` gates `stores/bookings.ts`'s `placeOrder()` (throws a clear error
instead of hitting the backend) and `CheckoutView.vue` (disables "Place order" up front with an
inline note) whenever the draft's `serviceId` isn't a real uuid. Real signed-up Pals are
unaffected. This surfaced 3.17 (seed script) being pulled forward — see below.

---

## Status

- **Current phase:** Phase 4 — Payment, moved up ahead of 3.16/3.17 per user direction
  (2026-08-25). 3.15 (Docker + Docker Compose) is done. **3.17 (seed script) was pulled forward
  out of order on 2026-09-04**, ahead of 4.4/4.5, so real Pals exist to test the booking flow
  against (seed Pals `p1`..`p8` have no real `players`/`services` row and can't be booked for
  real — see the "Booking against a seed Pal" note below). 3.16 (clean out mock/demo data) stays
  deferred until Phase 4 actually finishes, since it depends on every 3.x mock-fallback path
  being audited out, not just this one gap.
- **Next task:** 4.1 is fully done (4.1a-k, including 4.1f's live smoke test). 4.2 (Squad Coin
  ledger wiring) and 4.3 (manual platform commission tracking) are done. 3.17 is done (see below).
  **3.19 (Admin: Pal application review + ban, PIN gate) was pulled forward on 2026-09-05** per
  direct user request, and is now done (3.19a-i). **4.6 (DiceBear avatars everywhere)**, **4.7
  (Suggested Pals/Explore/Trending de-mocking)**, **4.8 (eStars avatar fix)**, **4.9 (Become a Pal
  prefill)**, **4.10 (auto-generated status posts on the Feed)**, and **4.11 (Feed composer image
  upload)** were all pulled forward on 2026-09-06 per direct user request and are now done. **4.4
  (Bakong KHQR integration) is now done on 2026-09-07**, descoped to a simulated "Scan to Pay" demo
  flow (4.4a-f) rather than a real Bakong integration. Next up is 4.5 (final-report escrow note),
  after which 3.16 resumes.
- **Last updated:** 2026-09-07

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
        total to keep in sync. `highlights`/`tipCoins` the modal collects stayed UI-only here,
        same "stays UI-only" convention as Create Service's Category field - `reviews` (2.3) had
        no highlights column, and tips needed the wallet ledger (3.9). Both landed later in 4.44. `bookings.py`'s `BookingOut`
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
  - [x] 3.16c Remove the client-side merge of seed Pals `p1`..`p8` into Browse Players/Home/
        Landing (`PlayersView.vue`/`HomeView.vue`'s `allPlayers`, `LandingView.vue`'s `topPlayers`)
        now that 3.17's seeded accounts are real DB rows instead. **Pulled forward on 2026-09-06**
        after the user noticed eStars Leaderboard entries had no avatar and asked where else the
        app still showed fake players instead of real ones — rest of 3.16 (a/b/d, the store
        fallback-to-mock branches and fixture deletion) stays deferred, scoped down to just this
        on the user's call. `LandingView.vue` previously had no player fetch at all (`topPlayers =
        mockPlayers`); now fetches real players on mount and sorts top 8 by rating, section hides
        when empty (same convention as 4.7's Suggested Pals).
  - [ ] 3.16d Verify via `vue-tsc --build`/`eslint` plus a manual walkthrough that no page silently
        regresses to an empty state now that the mock fallback is gone
- [x] 3.17 Seed script: populate the real Supabase project with realistic demo content so the
      marketplace looks alive (not test/throwaway rows — meant to stay through launch). **Pulled
      forward on 2026-09-04**, ahead of 4.4/4.5, to unblock testing the booking flow (see the
      "Booking against a seed Pal" note above) — 3.16 is still deferred.
  - [x] 3.17a Backend: `backend/scripts/seed_demo_data.py`, using the service-role client's admin
        API (`client.auth.admin.create_user`/`list_users`/`delete_user`) to create `auth.users`
        rows under a placeholder `@squadup-seed.test` domain (`.test` is IANA-reserved, guaranteed
        non-deliverable — no real Gmail needed, these never log in, just exist as FK targets, same
        role `on_auth_user_created` fills for a real Google signup) plus matching `players`/
        `services`/`service_pricing_options`/`service_promotions` rows. **Deviates from the
        "few hundred" scale named in the original scope line**: defaults to 24 Pals across 8 games
        (Valorant/LoL/MLBB/Dota 2/CS2/Overwatch 2/Apex/PUBG Mobile, each with its own rank
        ladder/role list) + 12 buyers — enough to make Browse Players/Player Profile look alive
        and give every game a few real, bookable listings without a multi-minute admin-API run;
        `--pals`/`--buyers` flags scale it up later if needed.
  - [x] 3.17b Seed a lighter slice of `bookings`/reviews (not `message_threads`/`messages` — left
        out to keep scope tight, and the 3.17b line already calls the Messages Realtime demo a
        job for 2 real Gmail accounts, not seed data) for roughly half of the seeded Pals: 1-3
        completed bookings each (real coin debit/credit via `core/wallet.py`'s
        `adjust_coin_balance`, `commission_pct`/`commission_coins` set like a real
        `complete_booking` call, ~85% get a review feeding the same rating-recompute helper
        `routers/reviews.py` uses) plus sometimes one still-`pending` booking, so Pal
        Dashboard/Orders/Earnings have real history instead of every seeded Pal looking brand new.
  - [x] 3.17c Idempotency: `seed` lists existing `@squadup-seed.test` accounts first and refuses
        to run if any exist, rather than merging into them — `teardown` (same file) deletes every
        seeded `auth.users` row by that domain marker, which cascades through
        `players`/`services`/`bookings`/`reviews`/`wallet_transactions` automatically (per
        `account_deletion_cascade.sql`), so reseeding is just `teardown` then `seed`.
  - [x] 3.17d Verification: ran against the real linked Supabase project (24 players, 24 services,
        40 bookings [33 completed / 7 pending], 30 reviews — row counts and relations spot-checked
        directly). Confirmed end to end through the actual API rather than the browser: local
        uvicorn's `GET /players` and `GET /players/{id}` return the seeded Pals with real uuid
        `id`/`serviceId` values, exactly the shape Browse Players/Service Detail/Checkout need,
        satisfying `isRealId()`'s guard. A full browser click-through placing a real order was
        **not** run — the natural next step (signing in as a seeded buyer to call `POST /bookings`
        live) needed setting a password on an account, which the permission classifier blocked as
        a credential-modification action; left for the user to verify by placing a real order
        against one of these Pals from Browse Players.
- [x] 3.18 Unify social graph: any account (not just Pals) can post and be followed, not just Pals
      — pulled forward on 2026-09-05 after wiring the Feed sidebar to `GET /players/me` surfaced
      that a plain buyer account has nowhere to keep post/follow counts and can't post at all
      (`create_post` 404s without a `players` row). Confirmed via a live read against the linked
      Supabase project that `posts`/`follows` are both empty and every `players` row has a
      non-null `user_id`, so the migration below has zero backfill risk. Scope boundary: only the
      social layer (posts/follows/likes/comments/saved-post display) moves to `author_id`/
      `followed_id` on `users`; services/bookings/reviews stay Pal-only.
  - [x] 3.18a Migration: `users` gains `posts_count`/`followers_count`/`following_count`;
        `posts.player_id` → `author_id references users(id)`; `follows.player_id` →
        `followed_id references users(id)` (+ `check (follower_id <> followed_id)`); `players`
        loses the now-redundant count columns. Pushed to the linked project
        (`supabase/migrations/20260905142123_unify_social_graph.sql`) via `bunx supabase db push`.
  - [x] 3.18b Backend: `routers/feed.py` posting/follow/comment-creator logic reworked around
        `author_id` (drops `_get_my_player_id`/`_get_player_row`, adds `_resolve_authors`/
        `_resolve_author` batch helpers replacing the old `players(...)` embeds, `PostOut.player_id`
        → `author_id`, `FollowOut.player_id` → `followed_id`, `follow_player`/`unfollow_player`
        renamed `follow_user`/`unfollow_user` keyed on any `users.id`). Comment `is_creator`
        resolution simplified to a direct `author_id` compare (no more double-hop
        `posts(players(user_id))` embed). `ruff check` clean.
  - [x] 3.18c Backend: `routers/players.py` surfaces the moved counts on Player Profile /
        `players/me` (`_with_social_counts`, merged in before `_serialize_player`) and
        `GET /players/{id}/feed` filters by the player's `user_id` instead of `player_id`. `ruff
        check` clean.
  - [x] 3.18d Frontend: `stores/auth.ts` (`AuthUser`/`loadAuthUser` gain
        `postsCount`/`followersCount`/`followingCount` off the same `users` row read) and
        `stores/feed.ts` (`FeedPost.playerId` → `authorId`, `toggleFollow`/`applyFollow` updated)
        renamed/extended.
  - [x] 3.18e Frontend: `FeedSidebar.vue` (new `stats` computed - Pal counts from
        `usePlayersStore().mine`, buyer counts from `authStore.user`, so the stat grid renders for
        any signed-in account while handle/tier stays Pal-only), `CreatePostModal.vue` (swapped its
        mock `myPlayerProfile` for the real `usePlayersStore().mine`, matching `FeedSidebar.vue`),
        `FeedPostCard.vue` (`handle` prop now nullable, no stray " · " for a buyer author),
        `FeedView.vue`/`PostDetailView.vue`/`FeedFollowingView.vue` wired to `authorId`.
  - [x] 3.18f Verification: `ruff check` and `vue-tsc --build` both clean; `eslint` clean on every
        touched file (only the 3 pre-existing unrelated errors elsewhere, noted since 3.1k). Live
        smoke test against the linked Supabase project, calling the real router functions directly
        (same approach as 3.8c): the confirmed-Pal-less buyer account
        (`sithisakleak001@gmail.com`) created a post (previously 404'd) → appeared in `GET /feed`
        with no handle/tier and `users.posts_count` incremented → followed a seeded Pal → followed
        a second plain buyer account → both targets' `users.followers_count` incremented, the
        acting buyer's `following_count` hit 2 → self-follow still rejected (400) →
        `players.py`'s player-profile fetch surfaced the same `followers_count` off `users`. 12/12
        checks passed; follow rows/post deleted and all four accounts' counts verified back to 0
        after.

- [x] 3.19 Admin: Pal application review + player ban, PIN-gated access (pulled forward on
      2026-09-05 per direct user request, ahead of 4.4/3.16 — replaces 1.15's mock email/password
      login on `/admin` with a single 4-digit code, `1234`; there is still exactly one admin
      "account" and no real admin auth, this is just a simpler gate)
  - [x] 3.19a Migration: `players` gains `status pal_application_status not null default
        'approved'` (new enum `pal_application_status` — `pending_review`/`approved`/`rejected`,
        existing rows default to `approved` so seeded/live Pals are unaffected) and `is_banned
        boolean not null default false`. Pushed with `bunx supabase db push`
        (`supabase/migrations/20260905160703_pal_application_status_and_ban.sql`).
  - [x] 3.19b Backend: `routers/players.py` — `create_my_player` now inserts `status:
        'pending_review'` instead of going live immediately; `list_players` (`GET /players`)
        filters to `status = 'approved' and is_banned = false` in the initial query, and
        `_fetch_player_by_id` gained a `public_only` flag (`get_player`/`GET /players/{id}` passes
        `True`, 404ing a pending/rejected/banned Pal) so a pending/rejected/banned Pal doesn't show
        up in Browse Players or a direct profile link. `GET /players/me` is untouched (a Pal can
        always see their own profile regardless of status — `_fetch_player_by_user_id` never sets
        `public_only`). `ruff check` clean. Not covered here: booking creation
        (`routers/bookings.py`) doesn't itself re-check a service's Pal's status/ban - a banned
        Pal's service just can't be discovered/booked through the normal browse/profile flow
        anymore, but a booking against a previously-bookmarked service URL for a since-banned Pal
        isn't blocked server-side. Small enough to leave as a follow-up rather than widen this
        task's scope.
  - [x] 3.19c Backend: `core/storage.py` gains `create_signed_url(bucket, path, expires_in)` for
        the private `id-documents` bucket (no signed-URL helper existed anywhere yet — `upload_file`
        only returns a bare path for private buckets). New `routers/admin.py` section: `GET
        /admin/pal-applications` (players with `status = 'pending_review'`, joined `users` for
        email, with `idFrontUrl`/`idBackUrl` swapped for 1-hour signed URLs so the admin can
        actually view the submitted ID photos) and `PATCH /admin/pal-applications/{id}/status`
        (`approved`/`rejected`, pass-through-to-Postgres like the existing flagged-players/disputes
        status endpoints). Also `PATCH /admin/players/{id}/ban` (body: `isBanned`) toggling the new
        column - returns the player's most recent `admin_flags` row (rejoined, same shape as
        `AdminFlaggedPlayerOut`) if one exists so the Flagged Players panel can patch it in place,
        or `null` if the banned player has no flag on file. `AdminFlaggedPlayerOut`/`_flag_out`
        extended with `isBanned` (joined off `players`) so the panel can show current ban state
        regardless of which endpoint last touched the row. Same no-auth-dependency posture as the
        rest of `admin.py`. `ruff check` clean, module imports clean.
  - [x] 3.19d Backend: live smoke test against the real Supabase project (two throwaway
        `pending_review` players, each with a real tiny file uploaded to the private
        `id-documents` bucket, through real HTTP against a local uvicorn): `GET
        /admin/pal-applications` listed both with the joined email and a usable signed
        `idFrontUrl` (`?token=...`) - approving one and rejecting the other both updated status
        and dropped them out of the pending-applications list; the approved one appeared in `GET
        /players` and `GET /players/{id}`, the rejected one 404'd on the profile and was absent
        from browse. `PATCH /admin/players/{id}/ban` on the now-approved player hid it from both
        `GET /players` and its profile despite `status = 'approved'` (confirming ban and status
        are independent gates), returned `null` with no flag on file, unbanning restored
        visibility, and banning again after creating a throwaway `admin_flags` row returned that
        flag re-joined with `isBanned: true`. 24/24 checks passed on the first run, no bugs found.
        All throwaway players/users/storage objects/flag rows cleaned up and verified empty after.
  - [x] 3.19e Frontend: `stores/admin.ts`'s mock email/password gate replaced with a single PIN
        check (`login(code)`, matches `'1234'`), same `sessionStorage`-only persistence as before.
        New `palApplications`/`palApplicationsLoading`/`palApplicationsError` state +
        `fetchPalApplications`/`updatePalApplicationStatus` actions (the latter removes the row
        from `palApplications` in place, since an approved/rejected application no longer shows up
        in a refetch) and a `banPlayer` action, mirroring the flagged-players fetch/update pattern.
        `mocks/admin.ts` gains `AdminPalApplication`/`PalApplicationStatus` types + two mock
        fallback applications, and `AdminFlaggedPlayer` gains `isBanned: boolean` (all five
        existing mock flags set to `false`).
  - [x] 3.19f Frontend: `AdminView.vue`'s login form is now a single PIN `UInput`
        (`type="password"`, `inputmode="numeric"`, `maxlength="4"`, centered/letter-spaced) instead
        of email+password, copy updated to "Enter the admin access code." New `tabs` entry `{ key:
        'applications', label: 'Pal applications' }` wired to a new `AdminPalApplicationsPanel`;
        the sidebar's hardcoded `admin@squadup.gg` line (no longer meaningful with a code-only
        gate) replaced with a plain "SquadUp moderation" label.
  - [x] 3.19g Frontend: `AdminPalApplicationsPanel.vue` — same structural pattern as
        `AdminFlaggedPlayersPanel.vue` (search + table + review `UModal`, loading/error/empty
        states), showing the applicant's games/rank/role/languages/tagline/payout schedule and
        links (new tab) to the signed ID-document URLs, with Approve/Reject buttons calling
        `updatePalApplicationStatus` and closing the modal on success (the row leaves the list
        rather than needing an updated status shown in place).
  - [x] 3.19h Frontend: `AdminFlaggedPlayersPanel.vue` - table row gets a small red "Banned" badge
        next to a banned Pal's name; the review modal gains a Ban/Unban row (own `banUpdating` busy
        state, separate from the existing Dismiss/Reviewing/Take action `statusUpdating` flag since
        it's a different endpoint) calling the new `banPlayer` action and reflecting/toggling
        `isBanned`.
  - [x] 3.19i Verification: `vue-tsc --build` clean; `eslint` clean apart from the same two
        pre-existing unrelated errors noted since 3.1k (`StepRates.vue`/`RefundModal.vue`,
        untouched by this task); `ruff check` clean across the backend. Manual browser walkthrough
        skipped per standing instruction not to run the `run` skill in this project.

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

- [x] 4.1 Stripe integration for Wallet Top-up (do first)
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
- [x] 4.4 Bakong KHQR integration - descoped to a simulated "Scan to Pay" demo flow instead of a
      real Bakong integration (registering for real KHQR API access wasn't worth it for a
      classroom demo; the judge/teacher explicitly OK'd faking the automation to look like a real
      KHQR scan-and-confirm). Plugs into Wallet Top-up next to the existing card flow.
  - [x] 4.4a Frontend: `qrcode` + `@types/qrcode` added (`bun add`) - renders the QR entirely
        client-side (no third-party QR image API), so nothing about the demo depends on network
        access to an external service.
  - [x] 4.4b Backend: `POST /wallet/topup/khqr` (`routers/wallet.py`) - creates an in-memory
        session (not a table; only needs to survive one demo run) for the chosen package's dollar
        amount, keyed by a UUID, holding a fake `KHQR|MERCHANT:...|AMOUNT:...|REF:...` payload.
  - [x] 4.4c Backend: `GET /wallet/topup/khqr/{id}/status` - the session flips `pending` ->
        `confirmed` on its own `KHQR_AUTO_CONFIRM_SECONDS` (5s) after creation, standing in for the
        real bank webhook a live KHQR integration would wait on; `-> expired` past
        `KHQR_SESSION_TTL_SECONDS` (120s) if the modal is left open.
  - [x] 4.4d Backend: `POST /wallet/topup/khqr/{id}/complete` - the actual credit, only once the
        session has reached `confirmed`, same verify-before-credit shape as 4.1d's Stripe
        re-check. Reuses `wallet_transactions.stripe_payment_intent_id` as the idempotency key
        (`khqr_<session_id>`) rather than adding a KHQR-specific column.
  - [x] 4.4e Frontend: `stores/wallet.ts` gains `createKhqrSession`/`getKhqrStatus`/
        `completeKhqrTopup`. `WalletView.vue`'s "QR Scan" dropdown item (previously a disabled
        stub) now switches the payment method and opens a "Scan to Pay" modal showing the QR,
        polling status every second, then auto-crediting and closing on `confirmed`.
  - [x] 4.4f Verification: `vue-tsc --build`, `eslint`, `ruff check` all clean (the same two
        pre-existing unrelated errors noted since 3.1k/4.1k, untouched by this task).
  - [x] 4.4g Polish requested after seeing the plain QR-on-white-square version: new
        `components/wallet/KhqrCard.vue` redraws `assets/KHQR_card.svg`'s card artwork (red
        header, dashed divider, rounded body) inline as SVG - rather than laying HTML text/an
        `<img>` over the flat asset - so the merchant name, amount, and generated QR `<image>`
        share the same 442x622 coordinate space as the original paths and stay pixel-aligned with
        it. Swapped in for the plain white QR box in `WalletView.vue`'s modal.
- [ ] 4.5 Note in final report: proper escrow (user → platform → player) is a post-launch
      enhancement, not built for submission
- [x] 4.6 DiceBear avatar integration across the app (ad-hoc UI polish, requested directly by the
      user on 2026-09-06 with a screenshot of dicebear.com's style picker; done ahead of 4.4/4.5
      since it's small and isolated — every `UAvatar` currently renders a hardcoded `PhUserCircle`
      icon regardless of data, so no avatar ever actually shows a face)
  - [x] 4.6a Frontend: new `utils/avatar.ts` — a curated list of DiceBear styles from its
        "Character" category only (dicebear.com groups styles into Minimalist/Character/Scene;
        per the user's explicit instruction, Minimalist and Scene styles are excluded), a seeded
        hash that picks one style per entity so the same id always renders the same style/art
        consistently across the app, `generatedAvatarUrl(seed)` building the
        `https://api.dicebear.com/9.x/{style}/svg?seed=...` URL, and `resolveAvatarUrl(seed,
        explicitUrl)` preferring a real uploaded photo (`avatarUrl`/`avatar_url`) when present and
        falling back to the generated one otherwise.
  - [x] 4.6b Frontend: mock data cleanup — replace the placeholder `i.pravatar.cc` stock-photo
        URLs in `mocks/players.ts`, `mocks/playerProfiles.ts`, `mocks/admin.ts`, `mocks/estars.ts`
        with `generatedAvatarUrl(...)` calls so demo Pals/leaderboard/admin rows showcase the
        mixed illustrated styles instead of stock stranger photos.
  - [x] 4.6c Frontend: wire every `UAvatar` across the ~34 components/views that render one to
        bind `:src="resolveAvatarUrl(...)"` off the best available stable id, instead of always
        falling through to the hardcoded icon — covers player cards/profiles, Pal + admin
        dashboards, feed (posts/comments/suggested Pals/right rail), messages (thread list + chat
        bubbles), settings, header, and booking/review/subscription modals.
  - [x] 4.6d Frontend: Become a Pal wizard's Account step (`StepAccount.vue`) shows a live
        generated-avatar preview before a real photo is uploaded, instead of a blank placeholder.
  - [x] 4.6e Verification: `vue-tsc --build` and `eslint` clean (same two pre-existing unrelated
        errors noted since 3.1k).
- [x] 4.7 Feed right rail's "Suggested Pals" wired to real data (was mock-only per 3.8a's decision
      to leave it that way "unless a later pass decides it's worth deriving from `posts`/
      `players`" — revisited after the user noticed the Follow button and profile link did nothing)
  - [x] 4.7a Backend: `GET /players/suggested` (`routers/players.py`) — a random sample (default
        4) of approved, account-linked Pals, excluding the viewer and anyone they already follow.
        Reuses `PlayerSummaryOut`/browse-card shape rather than a bespoke type; extracted the
        highlighted-service-listing lookup out of `list_players` into `_player_summaries` so both
        routes share it. Also added `user_id` to `PlayerSummaryOut`/`_player_summary` (and the
        frontend's `PlayerSummary`) since `follows` keys on `users.id`, not `players.id` - a
        browse card had no way to be followed before this.
  - [x] 4.7b Frontend: `stores/players.ts` gets `suggested`/`suggestedLoading`/`fetchSuggested()`
        (no mock fallback - empty is a normal state, same convention as the profile tabs).
        `FeedRightRail.vue` now renders `playersStore.suggested` instead of the hardcoded
        `mockSuggestedPals` (deleted, no other consumers): each row links to `/players/{id}`, and
        Follow calls `feedStore.toggleFollow` then drops the pal from the list on success. Section
        hides entirely when there's nothing to suggest.
  - [x] 4.7c Verification: `vue-tsc --build`, `eslint`, and `ruff check` all clean.
  - [x] 4.7d `FeedExploreView.vue`'s post grid was the same 3.8a mock-only gap (`mockExplorePosts`
        - 9 hardcoded tiles all authored by "Meowa" with fake "5.9k" like counts). Swapped for
        `feedStore.fetchFeed()`/`feedStore.posts` (the same real `GET /feed` data `FeedView.vue`
        already renders): category tabs filter on the post's real `category`, each tile links to
        `/feed/{id}` (Post Detail), avatar/likes use `resolveAvatarUrl`/the same `k`-suffix
        `formatCount` convention as `PlayerCard.vue`/`FeedSidebar.vue`. `exploreCategories` (the
        tab labels) stays as-is - it's curated UI copy, not fake data. Deleted the now-unused
        `ExplorePost`/`mockExplorePosts`. Caveat: real posts have no composer UI to tag a category
        yet (`CreatePostPayload.category` defaults to `"games"` server-side), so non-"Trending"
        tabs will look empty until that's wired up - not fixed here, out of scope for de-mocking
        the view.
  - [x] 4.7e `FeedRightRail.vue`'s "Trending now" was the same gap (`mockTrendingTopics` - 5
        hardcoded topics, dead buttons). Derived it from real data instead: groups
        `feedStore.posts` by `category`, top 5 by count, each row navigates to
        `/feed/explore?category=...` (which `FeedExploreView.vue` now reads on load and on
        in-place query changes to preselect that tab). Section hides when there are 0 posts,
        same as 4.7's Suggested Pals - correctly empty beats fake content. Deleted the
        now-unused `TrendingTopic`/`mockTrendingTopics`.
- [x] 4.8 eStars Leaderboard avatar fix (found 2026-09-06: the user noticed it was the only page
      with no avatars showing at all, real players included)
  - [x] 4.8a `EstarsLeaderboardView.vue` bound `entry.avatarUrl` raw on both `UAvatar`s instead of
        `resolveAvatarUrl(entry.id, entry.avatarUrl)` like every other component 4.6c covered - the
        one component that rollout missed. Real leaderboard entries (`GET /estars/leaderboard`)
        have `avatar_url = null` since no seed/signup path writes one, so this always fell through
        to the plain icon. Fixed to generate a DiceBear avatar the same way everywhere else does.
  - [x] 4.8b Audited the rest of the app for the same "mock rendered unconditionally instead of
        real data" class of bug (see 4.7's precedent). Found several around wallet balance/account
        settings (`SettingsPaymentsTab.vue`, `SettingsAccountTab.vue`, `SubscriptionModal.vue`,
        `CheckoutView.vue`, etc. reading `mockCurrentUser`/`mockPlayerProfiles.self` instead of
        `walletStore`/`authStore`) and confirmed two (`SettingsAccountTab.vue`'s phone/country/
        member-since, `SettingsPrivacyTab.vue`'s blocked-accounts count) have no backing DB field
        or endpoint at all yet. Scoped down to just 3.16c (player-list mock splices) on the user's
        call; the settings/wallet mock leaks and the two backend-gap fields are still open -
        tracked here, not fixed.

- [x] 4.9 Become a Pal step 1 prefill from the real account, phone/country closing the 4.8b gap
      (requested directly by the user on 2026-09-06)
  - [x] 4.9a Migration: `public.users` gets nullable `phone`/`country` columns (previously
        nowhere - `SettingsAccountTab.vue`'s inputs were mock-only, per 4.8b). Pushed live via
        `bunx supabase db push`.
  - [x] 4.9b Backend: `routers/users.py`'s `UserOut`/`UserUpdateIn` extended with `phone`/
        `country`, so the existing `GET`/`PATCH /users/me` cover them for free.
  - [x] 4.9c Frontend: `stores/auth.ts`'s `AuthUser` gets `phone`/`country` (read via
        `loadAuthUser`'s existing `users` select) plus a new `updateAccount()` action
        (`PATCH /users/me`) shared by the wizard and Settings.
  - [x] 4.9d Frontend: `BecomePlayerView.vue` seeds step 1's `accountData` from
        `authStore.user` instead of always-blank `createAccountStepData()` - a buyer who signed
        up first and becomes a Pal later sees their real display name/email/phone/country, a
        genuinely fresh signup sees empty phone/country same as before. `handleSubmit` now also
        calls `authStore.updateAccount()` so edits made in step 1 land on the account instead of
        vanishing (they previously weren't sent to `POST /players/me` at all). `StepAccount.vue`'s
        email input is locked (`disabled`) with a hint pointing at Settings - email stays
        Supabase-auth-backed and out of this form's reach.
  - [x] 4.9e Frontend: `SettingsAccountTab.vue` wired the same phone/country fields to
        `authStore.user`/`updateAccount()` with a "Save changes" button (`useToast` feedback,
        matching 3.13g's pattern) instead of the mock-only inputs 4.8b flagged; email input
        locked here too. `username`/`language`/`timezone` stay as before (player-profile fields,
        no account-level backing, out of scope here).
  - [x] 4.9f Verification: `vue-tsc --build`, `eslint`, `ruff check` all clean. Manual browser
        walkthrough not run by Claude, left to the user.

- [x] 4.10 Auto-generated "status" posts on the Feed (requested directly by the user on
      2026-09-06 - the Feed had no content unless someone opened the composer; agreed approach:
      real app events post short system-authored text updates, visually distinct from manual
      posts, no image/video pipeline needed)
  - [x] 4.10a Migration: `post_kind` enum (`user`/`status`) + `posts.kind` column, default
        `'user'` (`20260906090000_post_status_kind.sql`), pushed live via `bunx supabase db push`.
  - [x] 4.10b Backend: `core/feed_events.py`'s `post_status(user_id, text, category)` - inserts a
        `kind='status'` post, fire-and-forget, same convention as `core/notify.py`'s `notify()`.
        `feed.py`'s `PostOut`/`_post_out` now include `kind` so the frontend can distinguish them.
  - [x] 4.10c Backend: wired into four existing event sites, each posting from the account that
        experienced the event rather than inventing synthetic content: `bookings.py`'s
        `complete_booking` (buyer, "wrapped up a session with {pal} on {service}"), `reviews.py`'s
        `create_review` (reviewer, "rated a session with {pal} {n}⭐ on {service}" - also had to
        widen the existing `players` select to pull `display_name` alongside `user_id`),
        `feed.py`'s `follow_user` (follower, "started following {target}" - `_require_user_exists`
        now returns the row instead of just checking existence, to get the display name for free),
        and `admin.py`'s `update_pal_application_status` (new Pal, "Just got verified as a Pal on
        SquadUp!" when status transitions to `approved`). Leaderboard rank-change and
        withdrawal/streak triggers were considered but skipped - no history table to diff against
        yet, out of scope here.
  - [x] 4.10d Backend: live-verified directly against the real Supabase project (inserted +
        deleted a throwaway `kind='status'` row via `post_status` against a real user id, confirmed
        the enum/column round-trip); the four call sites themselves reuse the exact same
        insert/client pattern already proven live by `notify()`'s callers, not separately
        HTTP-smoke-tested.
  - [x] 4.10e Frontend: `FeedPost.kind` added (`stores/feed.ts`), all three `FeedPost`-constructing
        mock adapters (`feedPostFromMock`, `PostDetailView.vue`'s `postFromMockDetail`,
        `mocks/playerProfiles.ts`'s `feedPostFromMockEntry`) default it to `'user'`.
        `FeedPostCard.vue` gains a `kind` prop (default unset = `'user'` styling): a `'status'`
        post renders smaller/muted (compact avatar, no image slot, trimmed like/comment row with
        the share button dropped) so it reads as activity rather than fake user content. Wired
        through `FeedView.vue`, `FeedFollowingView.vue`, and `PostDetailView.vue` (the three
        store-backed consumers - `FeedSavedView.vue` stays as-is, `SavedItemOut` doesn't carry
        `kind`, out of scope).
  - [x] 4.10f Verification: `vue-tsc --build`, `eslint`, `ruff check` all clean (same two
        pre-existing unrelated eslint errors noted since 3.1k, one of them on
        `EstarsLeaderboardView.vue` which was already mid-edit by the user before this task
        started). Manual browser walkthrough not run by Claude, left to the user.
  - [x] 4.10g Polish requested after trying it live: the compact status card's like/comment icons
        bumped to match the regular row's size (user manually bumped the regular row to 24px in
        `FeedPostCard.vue`; the status row's followed to 20px to match), and the Follow button in
        `FeedView.vue`/`PostDetailView.vue`'s `#action` slot is now hidden on your own posts
        (`post.authorId !== currentUserId`) - it was rendering "Follow" on a status post about
        yourself, which is meaningless since you can't follow yourself. `FeedFollowingView.vue`
        didn't need the same fix, it only ever lists posts from accounts you follow.
  - [x] 4.10h Bug found after 4.10g: the like button felt unresponsive - `toggleLike`
        (`stores/feed.ts`) awaited the full like/unlike round trip before updating anything.
        Fixed with an optimistic `patchPost` before the request, reconciled with the server
        response after (reverted on failure).
  - [x] 4.10i Bug found after 4.10h: rapid double-clicking the like button produced impossible
        counts (liked with 0 likes, or 2 likes from one account). Two causes, both fixed: (1)
        backend - `_refresh_post`/`_refresh_comment` (`feed.py`) recomputed `likes_count` via a
        `SELECT` then a separate `UPDATE`, two round trips with no locking, so overlapping
        like/unlike calls on the same post could interleave and leave a permanently wrong count
        stored (not just a UI glitch) - replaced with atomic `refresh_post_likes_count`/
        `refresh_comment_likes_count` Postgres functions (`20260906100000_atomic_likes_count.sql`)
        that recompute-and-write in one statement, live-audited against the real project's
        existing rows (all counts were already correct, but the race window was real). (2)
        frontend - `toggleLike` fired each click as an independent request, so a fast double-click
        raced a like against an unlike and whichever response landed second won regardless of
        which was actually newer; fixed by chaining requests per post id
        (`likeRequestChains` in `stores/feed.ts`) so a queued second click's request only fires
        after the first resolves, and a stale response can no longer overwrite a newer one.

- [x] 4.11 Feed composer image upload (found 2026-09-06: the user attached a 187KB image to a
      post and it never appeared - the composer's `UFileUpload` had been visual-only since 1.6b,
      capturing a file but never sending it, and `POST /feed/posts` only ever accepted an
      `imageUrl` *string* with no upload endpoint or storage bucket behind it; `PostOut` also
      never exposed `image_url` at all, so `FeedPostCard.vue`/`ProfileFeedsTab.vue` could only
      ever render a blank gray placeholder for `hasImage`, never the real image)
  - [x] 4.11a New `post-images` public storage bucket (`20260906110000_post_images_bucket.sql`),
        pushed live via `bunx supabase db push`. Allowed mime type is just `image/webp` - every
        upload is re-encoded before it lands here (4.11b), so nothing else ever gets stored.
  - [x] 4.11b Backend: `core/storage.py` gains `upload_image_as_webp()` - downscales to fit
        1920px and re-encodes to WebP (Pillow, added as a dependency) before uploading, so a
        multi-MB phone photo doesn't get stored at full resolution for a feed-card thumbnail
        (live-verified: a 2.4MB test JPEG landed as a 4.4KB WebP). `routers/feed.py`'s
        `POST /feed/posts` switched from a JSON `PostCreateIn` body to multipart
        (`Form`/`File`, same convention as `players.py`'s service-cover upload), taking an
        optional `image` file alongside `text`/`category`. `PostOut` gains `image_url` (was
        `has_image` only - the frontend had no way to render the actual image even when one
        existed).
  - [x] 4.11c Frontend: `stores/feed.ts`'s `FeedPost` gains `imageUrl`, all three mock adapters
        (`feedPostFromMock`, `PostDetailView.vue`'s `postFromMockDetail`,
        `mocks/playerProfiles.ts`'s `feedPostFromMockEntry`) default it to `null`. `createPost`
        now builds `FormData` instead of a JSON body (same pattern as `CreateServiceView.vue`).
        `CreatePostModal.vue`'s file picker restricted to a single image (`multiple` dropped,
        `accept` narrowed to png/jpg/webp) since video/multi-image were never backed by the
        endpoint either - `canPost` now also allows an image-only post (backend already accepted
        that, the UI just never let you). `FeedPostCard.vue`/`ProfileFeedsTab.vue` render a real
        `<img>` when `imageUrl` is present, falling back to the old gray placeholder only for
        mock-fixture posts that carry `hasImage` with no real URL.
  - [x] 4.11d Backend: live-verified end-to-end against the real Supabase project (a throwaway
        auth user, `POST /feed/posts` via `TestClient` with a real multipart image, confirmed the
        response's `imageUrl` round-trips to a fetchable WebP object, then deleted the post row,
        storage object, and throwaway user).
  - [x] 4.11e Verification: `vue-tsc --build`, `eslint`, `ruff check` all clean. Manual browser
        walkthrough not run by Claude, left to the user.
  - [x] 4.10j Requested after seeing the feed load with no placeholder: new
        `components/feed/FeedPostSkeleton.vue` (avatar/name/text/like-row skeleton mirroring
        `FeedPostCard.vue`'s layout via `USkeleton`, the same primitive `HomeView.vue`/
        `NotificationsView.vue`/`FeedRightRail.vue` already use for loading states). Shown for 3
        placeholder cards while `feedStore.postsLoading`/`followingLoading` is true in
        `FeedView.vue`/`FeedFollowingView.vue`. `FeedFollowingView.vue` had a related latent bug
        this surfaced: its "Your feed is quiet" empty state rendered on `following.length === 0`
        with no loading check at all, so it flashed before every real fetch, not just when
        genuinely empty - fixed by gating it behind `v-else-if` after the new loading branch.
        `PostDetailView.vue` had the same gap the other direction (`post === null` showed "Post
        not found" while still loading, not just when actually missing) - added a `postLoading`
        ref set around `loadPost()` and a single skeleton shown ahead of the post/not-found
        branches.
  - [x] 4.10k Verification: `vue-tsc --build` and `ruff check` clean; `eslint` clean apart from the
        same two pre-existing unrelated errors.

- [x] 4.12 Stripped-down profile page for non-Pal users (found 2026-09-06 by the user: `FeedSidebar.vue`'s
      "Your profile" link and `AppHeader.vue`'s "Dashboard" button both send a non-Pal to
      `/dashboard/user`, which was a full-page "Become a Pal" upsell with no way to actually see
      your own profile - misleading and restrictive for a plain buyer)
  - [x] 4.12a Backend: `GET /feed` (`routers/feed.py`) gains an optional `author_id` query filter
        so a single account's own posts can be fetched without a new endpoint - reuses the
        existing `_serialize_posts` pipeline as-is.
  - [x] 4.12b Frontend: `stores/feed.ts` gains `fetchAuthorPosts(authorId)`, kept separate from
        `posts`/`following` state (no mock fallback - unlike `fetchFeed`, a failure here has no
        reasonable stand-in) so it doesn't clobber the shared Feed/Following views' state.
  - [x] 4.12c Frontend: `UserDashboardView.vue` rebuilt from a full-page CTA into an actual
        profile: avatar/name/email header with the real posts/followers/following counts
        (`authStore.user`, same source `FeedSidebar.vue` already used), a post composer + own
        post list (`FeedPostCard`/`FeedPostSkeleton`, `fetchAuthorPosts` + `toggleLike` wired the
        same way `ProfileFeedsTab.vue`/`FeedView.vue` already do it), with the Become-a-Pal pitch
        demoted to a compact banner + perk row rather than the entire page.
  - [x] 4.12d Requested after seeing it live: render inside the Feed page's center column instead
        of a standalone page. Route moved from `/dashboard/user` to `/feed/me`
        (`router/index.ts`), `UserDashboardView.vue` now renders through `FeedLayout.vue` (gained
        a `'profile'` `active` variant, mirrored onto `FeedSidebar.vue`'s prop type) so the
        sidebar/right rail stay visible same as Feed/Following/Explore/Saved.
        `FeedSidebar.vue`'s "Your profile" link and `AppHeader.vue`'s `dashboardPath` both repoint
        a non-Pal to `/feed/me`; a Pal still goes to `/dashboard/player`, unchanged.
  - [x] 4.12e Verification: `vue-tsc --build`, `eslint`, `ruff check` all clean. Manual browser
        walkthrough not run by Claude, left to the user.

- [x] 4.13 Editable posts (requested directly by the user on 2026-09-06 - the composer could
      create a post but there was no way to edit one afterward, anywhere it appeared)
  - [x] 4.13a Backend: `PATCH /feed/posts/{post_id}` (`routers/feed.py`) - author-only (403
        otherwise), text-only edit (image/category stay fixed once posted, same as the composer
        never let you change those on create either). Reuses `_get_post`/`_serialize_posts`
        as-is; a `PostUpdateIn` schema added alongside the existing `*In`/`*Out` models.
  - [x] 4.13b Frontend: `stores/feed.ts` gains `updatePost(postId, text)`, patched through the
        existing `patchPost` helper so `posts`/`following`/`current` all pick up the edit for
        free, same as `toggleLike`.
  - [x] 4.13c Frontend: `CreatePostModal.vue` gains an edit mode via an optional `post` prop -
        prefills the text, hides the image/tag/visibility controls (not editable), retitles to
        "Edit post" / "Save changes", and emits `updated` with the saved post for callers holding
        their own local copy outside `feedStore`'s lists. Wired into the three places a post
        renders via `FeedPostCard`: `FeedView.vue` and `PostDetailView.vue` (edit button replaces
        the Follow button's slot when `post.authorId === currentUserId`, same condition already
        used to hide Follow) and `UserDashboardView.vue`'s own-posts list (`/feed/me`, every post
        there is already the viewer's own). Hidden for `kind === 'status'` posts in all three -
        system-generated activity posts aren't user-authored text to edit.
  - [x] 4.13d Verification: `vue-tsc --build`, `eslint`, `ruff check` all clean. Manual browser
        walkthrough not run by Claude, left to the user.
  - [x] 4.13e Requested after seeing it live: the edit modal had no way to change a post's image
        at all, only text. `PATCH /feed/posts/{post_id}` (`routers/feed.py`) widened from a JSON
        `PostUpdateIn` body to multipart (`text`/`image`/`remove_image` `Form`/`File` params, same
        shape as `create_post`) - a new `image` replaces the existing one via
        `upload_image_as_webp`, `remove_image` clears it with no replacement, and the old
        `PostUpdateIn` schema was dropped as unused. `stores/feed.ts`'s `updatePost` takes the
        same `{ text, image?, removeImage? }` shape and posts `FormData` instead of JSON.
        `CreatePostModal.vue`'s edit mode now shows the existing image as a preview with a remove
        (✕) button, falling back to the same upload dropzone create mode uses once removed (or if
        there was never an image); `canPost` and the submit payload account for the image/removal
        state alongside text.

- [x] 4.14 Two bugs found by the user 2026-09-06: the feed avatar changes when you edit your
      display name, and Settings' "Username" field is captured in the form but never persisted or
      shown anywhere - the email leaks into that spot instead in a couple of places.
  - [x] 4.14a Feed avatar fix: `FeedPostCard.vue` seeded its avatar off the mutable `author`
        display-name string (`resolveAvatarUrl(props.author)`) instead of a stable id, so editing
        your display name changes which generated avatar you get. Added `authorId`/`avatarUrl`
        props and seeded `resolveAvatarUrl(props.authorId ?? props.author, props.avatarUrl)`
        instead (matches every other avatar call site in the app; falls back to the old
        name-seeded behavior only where a caller has no id, e.g. `FeedSavedView.vue`'s
        mock-fixture rows), and passed `:author-id`/`:avatar-url` from all 5 places a
        `FeedPostCard` renders (`FeedView.vue`, `FeedFollowingView.vue`, `FeedSavedView.vue`,
        `UserDashboardView.vue`, `FeedPostThread.vue`) - `FeedPost.avatarUrl`/`.authorId` already
        existed on the store type but were never wired through. `SavedItemOut`/`FeedSavedItem`
        gained `authorId`/`avatarUrl` too (`routers/feed.py`'s `_saved_item_out`) since a saved
        post had neither field to pass.
  - [x] 4.14b Backend: unify the Pal-only `players.handle` and the never-wired Settings
        "Username" into one `users.handle` column (user's choice - one handle everywhere, not two
        separate systems). Migration `20260906120000_users_handle.sql` adds `handle text unique`
        to `public.users`, backfills it from existing `players.handle` values, then drops
        `players.handle` - applied via `bunx supabase db push`. `routers/users.py`'s
        `UserOut`/`UserUpdateIn` gain `handle`, with a 409 (`postgrest.exceptions.APIError` code
        `23505`) on a uniqueness conflict.
  - [x] 4.14c Backend: `routers/players.py`'s `create_my_player` no longer writes its own random
        `@id`-style handle into the (now-gone) `players.handle` column - it ensures the account's
        `users.handle` is set (assigning the same auto-generated fallback only if the user has
        none yet) so a Pal's marketplace handle and their account username are the same value.
        `_with_social_counts` (already joining `users` for the social counts) pulls `handle`
        across too so `PlayerDetailOut.handle` keeps working unchanged from the frontend's
        perspective.
  - [x] 4.14d Backend: `routers/feed.py`'s `_resolve_authors` selects `handle` off `users`
        alongside `display_name`; `_post_out` and `_saved_item_out` read it off the resolved
        author instead of the player row.
  - [x] 4.14e Frontend: `stores/auth.ts`'s `AuthUser` gains `handle: string | null`,
        `loadAuthUser` maps it, and `updateAccount`'s payload type accepts `handle`.
  - [x] 4.14f Frontend: `SettingsAccountTab.vue`'s Username field now reads/writes
        `authStore.user?.handle` (dropping the old borrow-from-Pal-profile placeholder that never
        saved) and is actually included in the `updateAccount()` save call; a 409 surfaces as
        "Username already taken" through the existing save-error toast.
  - [x] 4.14g Frontend: replaced the email-as-username-stand-in spots - `FeedSidebar.vue`'s
        profile card and `UserDashboardView.vue`'s header now show `authStore.user?.handle`
        instead of `authStore.user?.email` (hidden entirely if the account has no handle set yet,
        rather than falling back to email again). Also fixed `ProfileFeedsTab.vue`'s post byline,
        which was fabricating `@{{ player.id }}` (a raw UUID) because its `player` prop is
        `PlayerSummary`-shaped (no handle) - added a dedicated `handle` prop, passed from
        `PlayerProfileView.vue` as `profile.handle` (the `PlayerProfile`-shaped sibling object
        that does carry it).
  - [x] 4.14h Verification: `bunx supabase db push`, `vue-tsc --build`, `eslint`, `ruff check` all
        clean (the 2 pre-existing `eslint` errors in `StepRates.vue`/`EstarsLeaderboardView.vue`
        are unrelated unused-import issues from earlier uncommitted work, untouched by this task).
        Manual browser walkthrough left to the user.

- [x] 4.15 A freshly-turned Pal (found 2026-09-06 by the user testing account `intmaster`) still
      got the plain-buyer experience everywhere `isPal` is checked: `AppHeader.vue`'s "Dashboard"
      button, "Become a Pal" nav link, and `MessagesView.vue`'s layout choice - all gated on
      `authStore.user?.playerId`, which turned out to always be `null`.
  - [x] 4.15a Root cause: `stores/auth.ts`'s `loadAuthUser` reads `players` directly with the
      signed-in user's own Supabase client to populate `playerId`, but `players` was left
      locked to `service_role` only when RLS was enabled (2.5's `auth_wiring.sql` deferred a
      self-access policy to "each Phase 3 feature" - nobody ever added one for `players`, unlike
      `users`). The query silently returned no rows for every account, Pal or not.
  - [x] 4.15b Migration `20260906170000_players_self_select.sql` adds a `players` select
        policy for `auth.uid() = user_id`, mirroring `users`' existing "view their own row"
        policy. Pushed live via `bunx supabase db push`. Fixes `AppHeader`/`MessagesView`'s
        `isPal` everywhere at the source - no frontend changes needed for those.
  - [x] 4.15c Frontend: `BecomePlayerView.vue`'s `handleSubmit` now sets `authStore.user.playerId`
        from the just-created profile's id right after `playersStore.createMine` succeeds, so
        `isPal` flips true immediately for the current session instead of waiting on the next
        page load/RLS round-trip.
  - [x] 4.15d Verification: `bunx supabase db push`, `vue-tsc --build`, `eslint` clean on the
        touched files (pre-existing errors in `StepGames.vue`/`mocks/playerProfiles.ts` from
        earlier uncommitted work are unrelated). Manual browser walkthrough left to the user.

- [x] 4.16 Pal avatar upload (found 2026-09-06 by the user on account `intmaster`: Settings'
      Profile tab "Change photo" button was `disabled` - a real photo could only ever be set
      once, during the Become a Pal wizard's Account step).
  - [x] 4.16a Backend: `PATCH /players/me/avatar` (`routers/players.py`, multipart `avatar`
        `File`) - re-encodes to WebP via `upload_image_as_webp` (same as feed/post images,
        unlike `create_my_player`'s raw upload for the wizard's one-off signup avatar), updates
        `players.avatar_url`, returns the refreshed `PlayerDetailOut`.
  - [x] 4.16b Frontend: `stores/players.ts` gains `updateAvatar(file)`, posting the multipart
        body and replacing `mine` with the response directly (no extra `fetchMine` round-trip) so
        every place already reading `playersStore.mine.avatarUrl` (feed sidebar, both
        dashboards, post composer) picks up the new photo at once.
  - [x] 4.16c Frontend: `SettingsProfileTab.vue`'s avatar preview now reads
        `playersStore.mine?.avatarUrl` (was unset, so it always fell back to the generated
        DiceBear avatar even after 4.6c wired every other `UAvatar` to real photos) and fetches
        `mine` on mount if not already loaded. "Change photo" opens a hidden file input
        (`StepAccount.vue`'s pattern) and calls `updateAvatar`, with a loading state and an
        error toast on failure.
  - [x] 4.16d Verification: `vue-tsc --build`, `eslint`, `ruff check` all clean; FastAPI app
        imports clean. Manual browser walkthrough left to the user.

- [x] 4.17 Two more spots missed by 4.6c's avatar wiring pass (found 2026-09-07 by the user after
      4.16: uploading a new Pal photo updated it everywhere except the navbar, and it would
      intermittently still show the generated DiceBear avatar on a refresh).
  - [x] 4.17a `AppHeader.vue` and `DashboardSidebar.vue` both called `resolveAvatarUrl` with only
        the seed argument, never the real `avatarUrl` - so the navbar and the Pal dashboard's own
        sidebar always rendered the generated fallback, upload or not.
  - [x] 4.17b The intermittent case on other components (which do pass `playersStore.mine?.avatarUrl`
        correctly): nothing fetches `playersStore.mine` globally, only specific views do
        (`FeedSidebar.vue`, `PlayerDashboardView.vue`, etc.) on their own mount - so a refresh
        landing on a page that never fetches it (`/wallet`, `/messages` as a buyer, `/bookings`,
        ...) left `mine` unpopulated for that whole page load. `AppHeader.vue` (mounted on every
        authenticated page) now calls `playersStore.fetchMine()` in its existing session-established
        `watch` block, alongside the notifications/wallet fetches it already did there.
  - [x] 4.17c `DashboardSidebar.vue`'s tier line was also still reading a stale
        `mockPlayerProfiles` lookup keyed off `mockCurrentUser.playerId` (same rendered-mock
        class of bug as 4.8b) - switched to `playersStore.mine?.tier`, dropping both mock imports
        now that nothing in the file uses them.
  - [x] 4.17d Verification: `vue-tsc --build` and `eslint` clean on the touched files. Manual
        browser walkthrough left to the user.

- [x] 4.18 Navigation feel: preconnect to the real backend origins (requested directly by the
      user, who found page/profile navigation jarring; researched an article on hard-navigation
      browser APIs first). Speculation Rules API / prerendering don't apply here since all
      internal nav is client-side routed by vue-router (no document reload) - preconnect is the
      one technique from that research that's real for this app. Hover/intent prefetch of route
      chunks + data, `<Transition>` on `router-view`, and `KeepAlive` for the nav tabs are the
      separate follow-up for the actual soft-nav jank, not yet implemented.
  - [x] 4.18a `frontend/index.html` now preconnects to `%VITE_SUPABASE_URL%` and `%VITE_API_URL%`
        (Vite's built-in HTML env interpolation) alongside the existing Google Fonts preconnects,
        shaving the DNS/TLS/TCP handshake off the first Supabase/API request per page load.
  - [x] 4.18b Verification: visual review only - `bun run dev`/browser check left to the user per
        [[feedback_no_build_or_run_skill]].

- [x] 4.19 Soft-nav smoothing for the 6 top-nav links (Discover/Feed/Games/eStars/Become a
      Pal/Help) - the actual fix for the jarring feeling 4.18 didn't touch, since that nav is
      all client-side routed with no document reload.
  - [x] 4.19a `App.vue`: bare `<router-view />` replaced with the scoped-slot form -
        `<transition name="route-fade" mode="out-in">` wrapping a `<keep-alive
        :include="cachedViewNames">`, `cachedViewNames` listing the 6 nav views by their
        `<script setup>`-inferred component name. Fade CSS respects `prefers-reduced-motion`.
  - [x] 4.19b KeepAlive changes each of those views' lifecycle contract - `onMounted` doesn't
        re-fire on revisit, but `onActivated` does (on first mount too). Moved the fetch/query
        logic that needs to rerun on revisit from `onMounted` to `onActivated` in `FeedView.vue`
        (`feedStore.fetchFeed()`), `EstarsLeaderboardView.vue` (`refetch`), and
        `AllServicesView.vue` (the `route.query.tab` auto-open-drawer read). `HomeView.vue`,
        `BecomeAPalView.vue`, `HelpCenterView.vue` needed no change (already length-guarded or
        fully static).
  - [x] 4.19c New `frontend/src/composables/useNavPrefetch.ts`: on hover-intent (~120ms
        debounce), touchstart, or focus of a nav link, re-invokes that route's lazy `()  =>
        import(...)` loader (safe/free once Vite's cached the chunk promise) and, for
        `/home`/`/feed`/`/estars`, calls the same store fetch the destination view calls by
        default so the data's already in flight by the time it mounts. Wired onto
        `AppHeader.vue`'s `navLinks` loop.
  - [x] 4.19d Dedup guard: hover-prefetch firing then the view's own `onActivated` firing
        moments later would otherwise double-fetch. Added `if (loading.value) return` as the
        first line of `feedStore.fetchFeed`, `estarsStore.fetchLeaderboard`,
        `playersStore.fetchList`, and `playersStore.fetchGameCounts` (which had no `loading`
        ref before now - added one, same convention every other fetch in that store already
        uses) - the same in-flight call still updates state, so nothing is lost.
  - [x] 4.19e Verification: `vue-tsc --build` and `eslint` clean on all 9 touched files (2
        pre-existing, unrelated errors elsewhere left alone). Manual browser walkthrough (hover
        a nav link and watch Network tab, then bounce between tabs) left to the user per
        [[feedback_no_build_or_run_skill]].

- [x] 4.20 "My Profile" nav item (requested 2026-09-11 by the user off the account dropdown
      screenshot) plus a self-view mode wherever it can land, so viewing your own profile never
      offers follow/chat/book/report against yourself.
  - [x] 4.20a `AppHeader.vue`: added "My Profile" as the first item in the account dropdown and
        the mobile slide-over menu. Pals go to `/players/{playerId}` (their full profile, in the
        4.20b self-view); everyone else to the new `/profile/me`.
  - [x] 4.20b `PlayerProfileView.vue` / `ProfileHeader.vue` / `ProfileServicesTab.vue`: added an
        `isOwnProfile` computed (route `id` === `authStore.user.playerId`) and threaded it down
        as a prop - hides Follow, Subscribe, and the Report/Block menu in the header, and the
        whole Chat/Book card in the Services tab, when a Pal is looking at their own profile.
  - [x] 4.20c New `MyProfileView.vue` at `/profile/me` - the non-Pal half of "My Profile", laid
        out like the Pal profile page rather than like the feed (same `max-w-4/5` shell, 24-unit
        avatar header, `UTabs variant="link"` row) since that layout was the actual ask. Header
        carries name/handle/post+follower+following counts, Copy username, and Edit profile (no
        Follow/Subscribe/Chat/Book - it's you). Tabs are Feeds (real posts via
        `feedStore.fetchAuthorPosts`) plus Album/Wish as `EmptyState` placeholders per 4.20e.
        Redirects to `/players/{playerId}` if the account is a Pal, so there's one canonical
        own-profile page per user.
        - First attempt reused `PublicProfileView.vue` instead of building this, which the user
          rejected on sight: that view renders inside `FeedLayout` (the 3-column feed shell with
          sidebar + right rail), so it read as "still the feed page" and looked nothing like the
          referenced Pal profile screenshot. Reusing a page for its data while ignoring that its
          *chrome* is the thing being asked about is the mistake to avoid repeating.
  - [x] 4.20d `PublicProfileView.vue` (`/feed/u/:id`) still redirects your own id away, but now
        to `my-profile` instead of the `/feed/me` dashboard. `/feed/me` is untouched and still
        reachable as its own sidebar-nav dashboard, per the user's call not to merge the two.
        `ProfileFeedsTab.vue`'s `player` prop narrowed to
        `Pick<PlayerSummary, 'id' | 'displayName' | 'avatarUrl'>` (the only fields it renders) so
        the buyer page, which has no player row, can reuse it; added an `isOwnProfile` prop for
        the "You haven't posted anything yet" empty copy. `CreatePostModal.vue` now also emits
        `created` (it only emitted `updated`, on edits), so a post made from the composer on
        either profile page appears immediately instead of after a reload.
  - [x] 4.20e Scoped out of this pass: giving the buyer profile real Album/Wish tabs like a Pal's.
        Investigated first - `album_items`/`wish_items` are `player_id`-scoped with **no**
        create/update/delete endpoint at all today, for Pals or buyers (seed-data only), so this
        isn't a quick re-scope to `user_id`, it's building Album/Wish CRUD from scratch. Logged
        in the cut list as its own item; the tabs ship as empty-state placeholders meanwhile.
  - [x] 4.20f `ProfileFeedsTab.vue`'s "Share something with your squad..." composer (and its
        `CreatePostModal`) now render only when `isOwnProfile` - it used to show to every viewer,
        so you could compose from someone else's Pal profile and have the post land on your own
        feed. Surfaced as a finding during 4.20d, fixed on the user's go-ahead.
  - [x] 4.20g Verification: `vue-tsc --noEmit` and `eslint` clean on all 7 touched/added files.
        Manual browser walkthrough left to the user per [[feedback_no_build_or_run_skill]].

- [x] 4.21 Feed navigation re-rendered the whole page (reported 2026-09-11 by the user with a
      screenshot of the feed): 4.19's transitions/KeepAlive/prefetch made the *top* nav smooth,
      but moving between feed tabs still faded and remounted the left sidebar and right rail
      along with the posts. The user asked for the Next.js app-router shape instead — a layout
      that stays mounted, with only the centre content swapping.
  - [x] 4.21a Root cause: every `/feed` route was its own top-level view and each one rendered
        `FeedLayout` itself, so the 3-column shell (with `FeedSidebar` + `FeedRightRail`) was
        torn down and rebuilt on every navigation — hence the avatar/stats flash, the repeated
        `fetchMine`/`fetchSuggested` calls, and the sidebar fading with the posts under
        `App.vue`'s route transition.
  - [x] 4.21b New `views/FeedShellView.vue` replaces `components/feed/FeedLayout.vue` (deleted):
        same grid markup, but it owns the two rails and renders a nested `<router-view>` in the
        centre cell. The fade transition now lives here and wraps only that cell.
  - [x] 4.21c `router/index.ts`: `/feed`, `/feed/following`, `/feed/explore`, `/feed/saved`,
        `/feed/me` and `/feed/u/:id` became children of one `/feed` shell record. Route names are
        unchanged, so every existing link/`router.push` still resolves. `/feed/:postId` stays a
        top-level route on purpose — the single-post page is full-width with no feed chrome — and
        still matches, since static child segments outrank a param.
  - [x] 4.21d The sidebar can no longer take `active`/`show-create-post` from the child view (it
        sits above it now), so both moved to route `meta` as `feedTab` and `feedCreatePost`, typed
        in the `RouteMeta` augmentation and read by the shell.
  - [x] 4.21e The six child views dropped their `FeedLayout` wrapper; each one's root is now the
        centre column itself (`flex min-w-0 flex-col gap-4`) — a single root, which the shell's
        `<transition>` requires.
  - [x] 4.21f The four fixed tabs are kept alive inside the shell so switching between them is
        instant and their filter state survives; `/feed/me` and `/feed/u/:id` stay uncached so a
        param change never shows another account's data. Same lifecycle contract as 4.19b:
        `FeedFollowingView` / `FeedExploreView` / `FeedSavedView` moved `onMounted` to
        `onActivated` (which also fires on first mount) so a revisit still refreshes.
  - [x] 4.21g `App.vue`'s `cachedViewNames` now lists `FeedShellView` instead of `FeedView` —
        the whole feed shell, inner cached tabs included, survives a trip to another top-nav tab.
  - [x] 4.21h Verification: `vue-tsc --noEmit` and `eslint` clean on all 9 touched files. Manual
        browser walkthrough left to the user per [[feedback_no_build_or_run_skill]].
  - [x] 4.27e User reported (2026-09-19) that "Apply crop" did nothing. Root cause: applying set
        `files` to the cropped File, which re-fired 4.27c's `watch(files)` - by the time the
        watcher flushed, `cropping` was already back to `false` and the File was not
        `originalFile`, so it treated the crop's own output as a fresh pick and reopened the
        cropper on it. The modal now remembers the File it wrote itself in `appliedFile` and the
        watcher ignores that identity. Same commit: dropped the Portrait (4:5) preset at the
        user's request, leaving Wide and Square.
  - [x] 4.27f User reported (2026-09-19) the composer's "+ Add" tag button did nothing. It never
        had a handler - it was placeholder markup - and, separately, the selected tags were never
        sent: `createPost` accepted a `category` the modal never passed, so every post landed on
        the backend's `"games"` default. Fixed both: "Add" is now a `USelectMenu` over
        `data/games.ts`'s catalog (filtered to games not already offered as a chip) that appends
        the picked game as a chip and selects it, and the chosen tag rides along as `category`.
        The row is single-select now (`selectedTag`, was a `selectedTags` array) because a post
        carries exactly one `category` server-side - it is what `FeedRightRail.vue` counts as a
        trending topic and what `/feed/explore?category=` filters on. The row is also no longer
        hidden when the account offers no services, since "Add" works without any.
  - [x] 4.27g Composer textarea (user request, 2026-09-19): `resize-none` kills the browser's
        drag handle, and `autoresize` with `:rows="5"` / `:maxrows="14"` holds it at five rows
        until the text actually wraps past them, then grows a line at a time and scrolls beyond
        fourteen instead of pushing the modal's footer off screen.
  - [x] 4.27h `POST /feed/posts` 500'd on the tag from 4.27f: `invalid input value for enum
        feed_category: "Bloodborne"`. 4.27f sent the picked tag as `category`, but `posts.category`
        is the `feed_category` enum ('games' | 'chilling' | 'clips') - a post *type*, not a topic -
        so a game name can never live there. Tags got their own nullable `posts.tag text` column
        (`20260919090000_post_tag.sql`, plus a partial index on non-null tags), applied via
        `bunx supabase db push`. Backend: `create_post` takes `tag: str | None = Form(None)`
        (stripped, empty means null), `PostOut` and `_post_out` carry it; `category` keeps its
        old meaning and `"games"` default. Frontend: `FeedPost.tag` / `CreatePostPayload.tag`,
        the composer sends `tag`, and `FeedPostCard.vue` renders it as a `#tag` chip under the
        post that deep-links to Explore.
  - [x] 4.27i Made the new tag reachable once posted: `FeedRightRail.vue`'s "Trending now" counts
        a post under its `tag` when it has one and its `category` otherwise (a game name is the
        more useful topic than the enum), and `FeedExploreView.vue` matches both fields for the
        `?category=` filter and the search box, so the card's `#tag` link lands on something.
        `ruff check` clean on the backend file, `vue-tsc`/`oxlint` clean on the frontend ones
        (the type-check errors that remain are the same pre-existing four from 4.27d).

- [x] 4.28 Several images per post, laid out like Facebook (requested 2026-09-19 by the user,
      with a screenshot of a five-image Facebook post as the target).
  - [x] 4.28a Schema: `posts.image_urls text[] not null default '{}'`
        (`20260919100000_post_image_urls.sql`), backfilled from `image_url`. `image_url` stays and
        always holds the first image, so everything already reading it (saved items,
        `has_image`, older rows, the mock-backed views) keeps working untouched. Applied via
        `bunx supabase db push`.
  - [x] 4.28b Backend: `create_post` takes a repeated `images` field (`list[UploadFile]`) next to
        the old single `image`, both funneled through a new `_collect_uploads` helper that drops
        the empty-filename entry a blank multipart field arrives as and caps the set at
        `_MAX_POST_IMAGES` (10). `update_post` gained `manage_images` + `keep_image_urls`: with
        the flag, `keep_image_urls` is the authoritative list of surviving images in display
        order and `images` is appended to it, so an empty list clears them. Without the flag the
        old single-image behavior (`image` replaces, `remove_image` clears) is untouched, which
        is why the flag exists at all - an omitted repeated field and an empty one are
        indistinguishable in multipart. `PostOut`/`_post_out` carry `image_urls`.
  - [x] 4.28c Composer: one `attachments` list drives both modes, each entry either `existing`
        (a URL the edit keeps) or `new` (a File that uploads), so create and edit share all the
        add/remove/crop plumbing. A lone first pick still opens the cropper by itself; a
        multi-pick lands as a thumbnail grid with per-photo crop and remove buttons, and
        `autoCropId` marks the auto-opened crop so cancelling *that* discards the photo while
        cancelling a crop the user asked for keeps it. Cropping an `existing` image converts it
        to a `new` one (what uploads is the cropped output) and re-crops still run off the
        untouched source.
  - [x] 4.28d `ImageCropper.vue` gained an `error` emit and `crossorigin="anonymous"`: an image
        already on the post is a Supabase Storage URL, which taints the canvas without a CORS
        opt-in and makes `toBlob` throw. Verified the bucket answers with
        `access-control-allow-origin: *`, so the anonymous request is enough; the emit means a
        failure surfaces as a toast instead of a dead button.
  - [x] 4.28e `FeedPostCard.vue` collage, sized off `photos` (`imageUrls`, falling back to the
        single `imageUrl`): two side by side, a tall one beside a stacked pair for three, a 2x2
        for four, and for five or more a row of two over a row of three with a "+N" cover on the
        last tile (a 6-column grid is the smallest that divides into both halves and thirds).
        The lightbox now tracks an index with prev/next buttons, a counter and arrow-key nav off
        a window listener (the modal's content isn't focused on open). `:image-urls` passed
        through all six store-backed call sites; `FeedSavedView` stays on its mock single image.
  - [x] 4.28f Verification: `ruff check` clean on the backend file, `vue-tsc --build` and
        `oxlint` clean across `src` (same four pre-existing type errors as 4.27d). Manual
        browser walkthrough left to the user per [[feedback_no_build_or_run_skill]].

- [x] 4.22 Own Posts/Following counts never moved until something happened to refetch (surfaced
      2026-09-11 as a side effect of 4.21, fixed on the user's go-ahead). Pre-existing, not new:
      `createPost` only unshifted the post and `toggleFollow` only flipped the card's flag, so
      the sidebar's tallies were wrong from the moment you acted. 4.21 only removed the accident
      that hid it — remounting `FeedSidebar` on every feed navigation refetched `GET /players/me`
      and the number silently caught up. The user chose fixing the counts at the source over
      re-buying that refetch.
  - [x] 4.22a `stores/feed.ts` gains `bumpMyCounts({ posts, following })`, called after
        `createPost` and after `toggleFollow`. It writes to both `auth.user` and `players.mine`,
        since every surface showing these reads one or the other (`FeedSidebar` prefers `mine`
        and falls back to `auth.user`; `/feed/me` reads `auth.user`). Floors at 0. Both stores
        are resolved inside the call, not at import time.
  - [x] 4.22b `followersCount` is deliberately left alone: it only changes when *someone else*
        follows you, which no action on this client can observe. `PublicProfileView` already
        applies the `followersCount` the follow endpoint returns for the profile being viewed —
        that's the target's count, not your own, and is untouched by this.
  - [x] 4.22c Every follow button in the app already routes through `feedStore.toggleFollow`
        (feed cards, post thread, right rail, `FollowListPanel`, `ProfileHeader`,
        `PublicProfileView`), so one call site covers all of them. There is no delete-post
        action yet, so `postsCount` only ever goes up.
  - [x] 4.22d `MyProfileView.vue` reads its own `PublicProfile` copy rather than the stores, so
        the store bump can't reach its header. `ProfileFeedsTab.vue` (which owns the composer,
        but not the header) now re-emits `created`, and the page bumps its own `postsCount`.
        Harmless for `PlayerProfileView`, the tab's other consumer, which shows followers rather
        than posts in its header.
  - [x] 4.22e Verification: `vue-tsc --noEmit` and `eslint` clean on all 3 touched files. Manual
        browser walkthrough left to the user per [[feedback_no_build_or_run_skill]].
  - [x] 4.27e User reported (2026-09-19) that "Apply crop" did nothing. Root cause: applying set
        `files` to the cropped File, which re-fired 4.27c's `watch(files)` - by the time the
        watcher flushed, `cropping` was already back to `false` and the File was not
        `originalFile`, so it treated the crop's own output as a fresh pick and reopened the
        cropper on it. The modal now remembers the File it wrote itself in `appliedFile` and the
        watcher ignores that identity. Same commit: dropped the Portrait (4:5) preset at the
        user's request, leaving Wide and Square.
  - [x] 4.27f User reported (2026-09-19) the composer's "+ Add" tag button did nothing. It never
        had a handler - it was placeholder markup - and, separately, the selected tags were never
        sent: `createPost` accepted a `category` the modal never passed, so every post landed on
        the backend's `"games"` default. Fixed both: "Add" is now a `USelectMenu` over
        `data/games.ts`'s catalog (filtered to games not already offered as a chip) that appends
        the picked game as a chip and selects it, and the chosen tag rides along as `category`.
        The row is single-select now (`selectedTag`, was a `selectedTags` array) because a post
        carries exactly one `category` server-side - it is what `FeedRightRail.vue` counts as a
        trending topic and what `/feed/explore?category=` filters on. The row is also no longer
        hidden when the account offers no services, since "Add" works without any.
  - [x] 4.27g Composer textarea (user request, 2026-09-19): `resize-none` kills the browser's
        drag handle, and `autoresize` with `:rows="5"` / `:maxrows="14"` holds it at five rows
        until the text actually wraps past them, then grows a line at a time and scrolls beyond
        fourteen instead of pushing the modal's footer off screen.
  - [x] 4.27h `POST /feed/posts` 500'd on the tag from 4.27f: `invalid input value for enum
        feed_category: "Bloodborne"`. 4.27f sent the picked tag as `category`, but `posts.category`
        is the `feed_category` enum ('games' | 'chilling' | 'clips') - a post *type*, not a topic -
        so a game name can never live there. Tags got their own nullable `posts.tag text` column
        (`20260919090000_post_tag.sql`, plus a partial index on non-null tags), applied via
        `bunx supabase db push`. Backend: `create_post` takes `tag: str | None = Form(None)`
        (stripped, empty means null), `PostOut` and `_post_out` carry it; `category` keeps its
        old meaning and `"games"` default. Frontend: `FeedPost.tag` / `CreatePostPayload.tag`,
        the composer sends `tag`, and `FeedPostCard.vue` renders it as a `#tag` chip under the
        post that deep-links to Explore.
  - [x] 4.27i Made the new tag reachable once posted: `FeedRightRail.vue`'s "Trending now" counts
        a post under its `tag` when it has one and its `category` otherwise (a game name is the
        more useful topic than the enum), and `FeedExploreView.vue` matches both fields for the
        `?category=` filter and the search box, so the card's `#tag` link lands on something.
        `ruff check` clean on the backend file, `vue-tsc`/`oxlint` clean on the frontend ones
        (the type-check errors that remain are the same pre-existing four from 4.27d).

- [x] 4.23 Settings page's top-right "Save changes" button (reported 2026-09-11 by the user: it
      was disabled for both Pal and non-Pal accounts, while the Account tab's own Save button
      worked fine).
  - [x] 4.23a Root cause: `SettingsView.vue`'s header button was a static placeholder in both
        layout branches - `<UButton disabled>Save changes</UButton>` with no click handler and no
        dirty-state tracking, so it could never enable. It also had nothing consistent to save:
        Account and Payments/Security persist through real store/API calls, but Notifications and
        Privacy are plain local `ref()`s with no backend behind them at all.
  - [x] 4.23b User chose removing the dead button over wiring it up (which would first require
        adding persistence to the Notifications and Privacy tabs). Deleted it from both branches
        of `SettingsView.vue` and unwrapped the now-single-child header flex row. Each tab keeps
        its own working save/action controls, matching the pattern that already works.
  - [x] 4.23c Verification: `eslint` clean. Manual browser walkthrough left to the user per
        [[feedback_no_build_or_run_skill]].
  - [x] 4.23d Noted, not fixed: Account tab's Save doesn't include the `language`/`timezone`
        selects in its `updateAccount` payload, so those two fields don't persist despite the
        button working. Left for the user to prioritize.

- [x] 4.24 Messages page cleanup + per-chat mute/delete (requested directly by the user
      2026-09-13, off a screenshot of the Messages page).
  - [x] 4.24a Frontend: removed `MessagesPanel.vue`'s disabled "New chat" button (dead placeholder,
        `PhPlus` import dropped) and the conversation header's Call button (`PhPhone` import
        dropped) - both were non-functional per the user, "it's not needed"/"it's useless". Each
        chat-list row's outer `<button>` became a `role="button"` `<div>` so a per-row 3-dot
        (`PhDotsThree`) `UDropdownMenu` could sit inside without an invalid nested-button; the
        button uses `@click.stop` so opening the menu doesn't also select the thread. Menu offers
        Mute/Unmute and Delete, revealed on row hover/focus via `group-hover`.
  - [x] 4.24b Initial pass was frontend-only (local `ref` `Set`s for muted/hidden thread ids, no
        persistence) since no backend existed yet - the user then asked to wire it up for real.
  - [x] 4.24c Backend: new `message_thread_states` table (migration
        `20260913050000_message_thread_states.sql`) - one row per `(thread_id, user_id)` since
        mute/delete are per-participant, not shared like `message_threads` itself; `deleted_at` is
        a soft hide so the other participant's copy of the thread/messages is unaffected. RLS
        enabled with no policies (consistent with every table `routers/messages.py`'s
        service-role client is the only reader/writer of - no frontend-direct Supabase access
        needed here, unlike 3.5b's realtime tables). Applied via `bunx supabase db push`.
  - [x] 4.24d Backend: `routers/messages.py` - `PATCH /messages/threads/{id}/mute` and
        `DELETE /messages/threads/{id}` (204, soft-hide only), both scoped to the caller via the
        existing `_get_thread` membership check. `ThreadOut` gained a `muted` field; `list_threads`
        now batch-fetches state rows alongside threads/messages (same batching convention as
        3.5a) and filters out threads the caller has hidden. Deleting a thread you're still
        chatting in isn't permanent: `start_thread` un-hides it if you message that participant
        again, and `send_message` un-hides it for the *recipient* too, so a chat you deleted
        doesn't silently swallow a message the other person sends you later.
  - [x] 4.24e Frontend: `stores/messages.ts` - `MessageThread` gained `muted: boolean` (mocks
        updated to match); new `muteThread(threadId, muted)`/`deleteThread(threadId)` actions
        calling the new endpoints, updating/removing the thread locally on success rather than
        refetching the whole list. `MessagesPanel.vue`'s menu items and mute indicator now read
        `thread.muted` from the store instead of local state, with a toast on failure (same
        pattern as `handleSend`).
  - [x] 4.24f Verification: `ruff check` and `vue-tsc --noEmit` both clean, `eslint` clean on the
        changed files. Manual browser walkthrough left to the user per
        [[feedback_no_build_or_run_skill]].
  - [x] 4.24g Perf fix (reported 2026-09-13 by the user: mute/unmute felt slow). Root cause: the
        mute endpoint chained 4 sequential Supabase round trips - a joined `_get_thread` fetch,
        the state upsert, then `_full_thread_out` re-fetching *every message in the thread*
        (unbounded) plus a redundant state re-read, all just to hand back a `ThreadOut` the
        frontend immediately overwrote in place. Not a Realtime problem - Realtime pushes DB
        changes to *other* viewers, it doesn't speed up the round trip for your own write.
        Trimmed `set_thread_muted`/`delete_thread` to one cheap membership check
        (`_require_membership`, no display-name join) plus the upsert; mute now returns a minimal
        `{id, muted}` (`MuteThreadOut`) instead of a recomputed `ThreadOut`. `_full_thread_out`
        deleted as dead code. Frontend `stores/messages.ts`'s `muteThread`/`deleteThread` are now
        optimistic - flip/remove the thread locally before the request resolves, roll back on
        failure - so the click feels instant regardless of network latency.

- [x] 4.25 Player dashboard navigation re-rendered the whole page too (reported 2026-09-13 by the
      user with a screenshot of the Dashboard page - same complaint as 4.21, but for
      `/dashboard/player/*`, `/messages` and `/settings`): moving between Dashboard/Orders/My
      services/Earnings/Messages/Settings tore down and rebuilt `DashboardSidebar` on every nav.
  - [x] 4.25a Root cause: `/dashboard/player`, `/orders`, `/services`, `/earnings` were four
        separate top-level routes, each rendering `DashboardLayout` (and its `DashboardSidebar`)
        itself; `/messages` and `/settings` did the same conditionally for Pal accounts.
  - [x] 4.25b New `views/PlayerDashboardShellView.vue`: owns `DashboardLayout`/`DashboardSidebar`
        once, with a nested `<router-view>` (fade transition + `keep-alive`) in the content slot.
  - [x] 4.25c `router/index.ts`: those four dashboard routes became children of one
        `/dashboard/player` shell record. `/messages` and `/settings` were pulled in too via
        absolute child paths (`path: '/messages'`/`'/settings'`) so they nest under the same
        shell for rendering while keeping their existing top-level URLs - vue-router supports
        this (a child path starting with `/` skips the parent's URL prefix but keeps the parent
        component nesting, confirmed with a throwaway `router.resolve()` script). `.../services/new`
        stays a top-level sibling route on purpose - the create-service flow is full-width, with
        no sidebar.
  - [x] 4.25d Active nav item moved from a prop (`active`) to route `meta.dashboardTab`, since
        the sidebar sits above the child view now (same pattern as 4.21d's `feedTab`).
  - [x] 4.25e The six child views dropped their own `DashboardLayout` wrapper. `MessagesView`/
        `SettingsView` keep their `isPal` branch for buyer-facing content differences, but the
        Pal branch no longer wraps itself in `DashboardLayout` - the shell only renders that
        chrome `v-if="isPal"` and hands buyers straight through via a plain `v-else`
        `<router-view>`, so buyers still see their existing full-bleed layout untouched.
  - [x] 4.25f All six child views are kept alive inside the shell so switching tabs is instant
        and preserves scroll/selection/filter state.
  - [x] 4.25g Verification: `vue-tsc --noEmit` and `eslint` clean on all touched files. Manual
        browser walkthrough left to the user per [[feedback_no_build_or_run_skill]].
  - [x] 4.27e User reported (2026-09-19) that "Apply crop" did nothing. Root cause: applying set
        `files` to the cropped File, which re-fired 4.27c's `watch(files)` - by the time the
        watcher flushed, `cropping` was already back to `false` and the File was not
        `originalFile`, so it treated the crop's own output as a fresh pick and reopened the
        cropper on it. The modal now remembers the File it wrote itself in `appliedFile` and the
        watcher ignores that identity. Same commit: dropped the Portrait (4:5) preset at the
        user's request, leaving Wide and Square.
  - [x] 4.27f User reported (2026-09-19) the composer's "+ Add" tag button did nothing. It never
        had a handler - it was placeholder markup - and, separately, the selected tags were never
        sent: `createPost` accepted a `category` the modal never passed, so every post landed on
        the backend's `"games"` default. Fixed both: "Add" is now a `USelectMenu` over
        `data/games.ts`'s catalog (filtered to games not already offered as a chip) that appends
        the picked game as a chip and selects it, and the chosen tag rides along as `category`.
        The row is single-select now (`selectedTag`, was a `selectedTags` array) because a post
        carries exactly one `category` server-side - it is what `FeedRightRail.vue` counts as a
        trending topic and what `/feed/explore?category=` filters on. The row is also no longer
        hidden when the account offers no services, since "Add" works without any.
  - [x] 4.27g Composer textarea (user request, 2026-09-19): `resize-none` kills the browser's
        drag handle, and `autoresize` with `:rows="5"` / `:maxrows="14"` holds it at five rows
        until the text actually wraps past them, then grows a line at a time and scrolls beyond
        fourteen instead of pushing the modal's footer off screen.
  - [x] 4.27h `POST /feed/posts` 500'd on the tag from 4.27f: `invalid input value for enum
        feed_category: "Bloodborne"`. 4.27f sent the picked tag as `category`, but `posts.category`
        is the `feed_category` enum ('games' | 'chilling' | 'clips') - a post *type*, not a topic -
        so a game name can never live there. Tags got their own nullable `posts.tag text` column
        (`20260919090000_post_tag.sql`, plus a partial index on non-null tags), applied via
        `bunx supabase db push`. Backend: `create_post` takes `tag: str | None = Form(None)`
        (stripped, empty means null), `PostOut` and `_post_out` carry it; `category` keeps its
        old meaning and `"games"` default. Frontend: `FeedPost.tag` / `CreatePostPayload.tag`,
        the composer sends `tag`, and `FeedPostCard.vue` renders it as a `#tag` chip under the
        post that deep-links to Explore.
  - [x] 4.27i Made the new tag reachable once posted: `FeedRightRail.vue`'s "Trending now" counts
        a post under its `tag` when it has one and its `category` otherwise (a game name is the
        more useful topic than the enum), and `FeedExploreView.vue` matches both fields for the
        `?category=` filter and the search box, so the card's `#tag` link lands on something.
        `ruff check` clean on the backend file, `vue-tsc`/`oxlint` clean on the frontend ones
        (the type-check errors that remain are the same pre-existing four from 4.27d).

- [x] 4.26 Notification panel: clicking a "message" notification opens that conversation
      (requested 2026-09-13 by the user off a screenshot of the notification dropdown).
  - [x] 4.26a Root issue: `AppNotification` only carried a pre-rendered `message` string with no
        id back to the conversation it came from, so there was nothing to route to. Added a
        `thread_id` column to `notifications` (migration `20260913060000_notification_thread_id.sql`,
        nullable/`on delete set null` since only "message" notifications use it) and threaded it
        through: `core/notify.py`'s `notify()` takes an optional `thread_id`; `routers/messages.py`'s
        `send_message` passes the thread's id; `NotificationOut` gained `thread_id`. Applied via
        `bunx supabase db push`.
  - [x] 4.26b Frontend: `stores/notifications.ts`'s `AppNotification` gained `threadId?: string`
        (mock data updated to match). `NotificationPanel.vue`'s row click now marks the
        notification read *and*, for `type: 'message'` with a `threadId`, closes the popover and
        navigates to `{ name: 'messages', query: { thread: threadId } }` - other notification
        types keep the old mark-read-only behavior.
  - [x] 4.26c `MessagesPanel.vue` had no way to open a specific thread from outside itself - it
        always defaulted to the first thread on mount. Added `openThreadFromQuery()`, reading
        `?thread=` and selecting that thread if it's in the caller's thread list, falling back to
        the old first-thread default otherwise; a `watch` on the query re-runs it too, since
        clicking a notification while already on `/messages` reuses the mounted component
        (`onMounted` won't fire again).
  - [x] 4.26d Verification: `ruff check` clean on the backend files, `vue-tsc --noEmit` and
        `eslint` clean on the frontend files. Manual browser walkthrough left to the user per
        [[feedback_no_build_or_run_skill]].
  - [x] 4.26e User reported clicking a notification still only marked it read, no redirect.
        Root cause: the new `thread_id` column only gets populated by *new* sends -
        pre-existing "message" notifications (created before 4.26a) still had it `null`, so
        `NotificationPanel.vue`'s click handler correctly no-opped on the redirect for them.
        Backfill migration (`20260913062000_backfill_notification_thread_id.sql`) matches each
        null-`thread_id` notification to the message that triggered it, by closest `created_at`
        (within 10s - `notify()` runs right after the message insert in the same request) within
        a thread the notified user actually belongs to. Applied via `bunx supabase db push`;
        spot-checked all pre-existing rows now have a non-null `thread_id`.

- [x] 4.27 Crop the photo before posting (requested 2026-09-19 by the user, off a screenshot of
      the Create post modal: picked images went up untouched, and the feed renders every post
      image `aspect-video object-cover`, so tall photos got center-cropped by the browser with no
      say in what stayed in frame).
  - [x] 4.27a New `components/common/ImageCropper.vue`, dependency-free (no new package): the
        image is drawn at `max(frameW/naturalW, frameH/naturalH) * zoom`, so it always covers the
        frame and panning can never expose an empty edge; offsets are clamped to that on every
        drag, zoom and aspect change. Pointer-capture drag, cursor-anchored wheel zoom sharing one
        `zoomTo(next, anchorX, anchorY)` path with the slider, arrow-key nudge (shift = 32px),
        `+`/`-` zoom, rule-of-thirds overlay, and Wide (16:9, the default since that is what the
        feed shows) / Square / Portrait presets plus Reset.
  - [x] 4.27b Export crops from the *source* pixels, not the on-screen preview: the visible frame
        maps back through `scale` to `drawImage(img, sx, sy, sourceW, sourceH, ...)`, capped at
        1600px on the long edge, encoded at quality 0.92. Output mime follows the upload when it
        is one canvas can encode (png/webp/jpeg), else jpeg, so a PNG keeps its alpha.
  - [x] 4.27c `CreatePostModal.vue` wiring: a `watch` on `files` sends a fresh pick straight into
        the cropper (body swaps to the cropper, title becomes "Crop photo"). The untouched pick is
        kept in `originalFile`/`originalUrl` so re-cropping never compounds quality loss, while
        `files` holds the cropped `File` that actually uploads. Applying shows a preview with
        Crop/Remove buttons in place of the dropzone; cancelling the *first* crop detaches the
        image entirely (nothing was ever chosen), cancelling a re-crop keeps the current one.
        Object URLs are revoked on replace, clear, modal close and unmount; `canPost` is false
        while cropping so the footer cannot fire mid-crop.
  - [x] 4.27d Verification: `vue-tsc --build` and `oxlint` clean on both files (the type-check
        errors it does report are all pre-existing, in `mocks/playerProfiles.ts`,
        `stores/players.ts`, `stores/messages.ts` and `become-player/StepGames.vue`). Manual
        browser walkthrough left to the user per [[feedback_no_build_or_run_skill]].
  - [x] 4.27e User reported (2026-09-19) that "Apply crop" did nothing. Root cause: applying set
        `files` to the cropped File, which re-fired 4.27c's `watch(files)` - by the time the
        watcher flushed, `cropping` was already back to `false` and the File was not
        `originalFile`, so it treated the crop's own output as a fresh pick and reopened the
        cropper on it. The modal now remembers the File it wrote itself in `appliedFile` and the
        watcher ignores that identity. Same commit: dropped the Portrait (4:5) preset at the
        user's request, leaving Wide and Square.
  - [x] 4.27f User reported (2026-09-19) the composer's "+ Add" tag button did nothing. It never
        had a handler - it was placeholder markup - and, separately, the selected tags were never
        sent: `createPost` accepted a `category` the modal never passed, so every post landed on
        the backend's `"games"` default. Fixed both: "Add" is now a `USelectMenu` over
        `data/games.ts`'s catalog (filtered to games not already offered as a chip) that appends
        the picked game as a chip and selects it, and the chosen tag rides along as `category`.
        The row is single-select now (`selectedTag`, was a `selectedTags` array) because a post
        carries exactly one `category` server-side - it is what `FeedRightRail.vue` counts as a
        trending topic and what `/feed/explore?category=` filters on. The row is also no longer
        hidden when the account offers no services, since "Add" works without any.
  - [x] 4.27g Composer textarea (user request, 2026-09-19): `resize-none` kills the browser's
        drag handle, and `autoresize` with `:rows="5"` / `:maxrows="14"` holds it at five rows
        until the text actually wraps past them, then grows a line at a time and scrolls beyond
        fourteen instead of pushing the modal's footer off screen.
  - [x] 4.27h `POST /feed/posts` 500'd on the tag from 4.27f: `invalid input value for enum
        feed_category: "Bloodborne"`. 4.27f sent the picked tag as `category`, but `posts.category`
        is the `feed_category` enum ('games' | 'chilling' | 'clips') - a post *type*, not a topic -
        so a game name can never live there. Tags got their own nullable `posts.tag text` column
        (`20260919090000_post_tag.sql`, plus a partial index on non-null tags), applied via
        `bunx supabase db push`. Backend: `create_post` takes `tag: str | None = Form(None)`
        (stripped, empty means null), `PostOut` and `_post_out` carry it; `category` keeps its
        old meaning and `"games"` default. Frontend: `FeedPost.tag` / `CreatePostPayload.tag`,
        the composer sends `tag`, and `FeedPostCard.vue` renders it as a `#tag` chip under the
        post that deep-links to Explore.
  - [x] 4.27i Made the new tag reachable once posted: `FeedRightRail.vue`'s "Trending now" counts
        a post under its `tag` when it has one and its `category` otherwise (a game name is the
        more useful topic than the enum), and `FeedExploreView.vue` matches both fields for the
        `?category=` filter and the search box, so the card's `#tag` link lands on something.
        `ruff check` clean on the backend file, `vue-tsc`/`oxlint` clean on the frontend ones
        (the type-check errors that remain are the same pre-existing four from 4.27d).

  - [x] 4.28 Top-up repricing (90 SC/$) + withdrawal approval flow (user request, 2026-09-19)
  - [x] 4.28a Repriced the four `topup_packages` tiers to a flat 90 SC per dollar with small flat
        bonuses: $5 = 450, $10 = 900 (base rate), $25 = 2,250 + 100 bonus, $50 = 4,500 + 200 bonus
        (`20260919110000_topup_reprice.sql`, updates in place so ids already referenced by an open
        PaymentIntent/KHQR session still resolve). `mocks/wallet.ts`'s fallback rows match, and
        `WithdrawView.vue`'s `COINS_PER_USD` went 99 -> 90 since it was pinned to the old base rate.
  - [x] 4.28b Payout queue schema: `withdrawal_status` gained `requested` (the new default) and
        `rejected`, plus `withdrawals.reviewed_at` and a status index. Postgres will not let a
        freshly added enum value be used in the same transaction, so the default flip lives in its
        own follow-up migration (`20260919120000` then `20260919130000`). `in_progress` kept its
        name but changed meaning: it used to be "requested and never touched again", it now means
        an admin approved it and the transfer is with the provider.
  - [x] 4.28c `WITHDRAWAL_FEE_PCT` 10 -> 20 in `routers/wallet.py` (and
        `mockWithdrawalPlatformFeePct` to match), so a payout is an 80/20 split: the Pal keeps 80%,
        SquadUp takes 20%. `create_withdrawal` inserts as `requested` and its notification says the
        request is awaiting review rather than already processing.
  - [x] 4.28d Admin endpoints: `GET /admin/withdrawals` (every Pal's request, joined to
        `players`/`payout_methods`, with the 80% `payout_coins` computed server-side) and
        `PATCH /admin/withdrawals/{id}/status`. Approve marks `paid`, `in_progress` is the optional
        "with the provider" step, and `rejected` credits the full amount back via
        `adjust_coin_balance` - the 20% fee is only earned on a payout that actually goes out. A
        row that already reached `paid`/`rejected` 409s rather than being reviewed twice.
        `wallet_transactions` gained a nullable `withdrawal_id`
        (`20260919140000_wallet_txn_withdrawal_id.sql`) so the decision settles the exact `pending`
        payout row the request logged - matching it back by user + kind + coins is ambiguous once a
        Pal has two same-sized requests open.
  - [x] 4.28e Frontend: new `AdminWithdrawalsPanel.vue` + a "Payouts" tab in `AdminView.vue`,
        defaulting to the Awaiting-review filter with a pending count on the chip; the table breaks
        each request into requested / SquadUp 20% / Pal receives 80%, and the review modal carries
        Processing / Approve / Decline. `stores/admin.ts` gained the fetch/patch pair with the usual
        `mocks/admin.ts` fallback, and `stores/wallet.ts`'s `Withdrawal.status` widened to the full
        four-value enum so `WithdrawView.vue` can label a Pal's own request "Awaiting review".
  - [x] 4.28f Verification: `ruff check` clean on both backend files, `oxlint` clean on all changed
        frontend files, `vue-tsc --build` reporting only the pre-existing errors (`playerProfiles.ts`,
        `stores/players.ts`, `stores/messages.ts`, `become-player/StepGames.vue`). Migrations applied
        with `bunx supabase db push`; the live `topup_packages` rows read back at the new prices. End
        to end against the real DB: a seeded `requested` row listed with `payoutCoins` 800 of 1,000,
        approving set `paid` + `reviewed_at`, a second approve 409'd, and the test rows were deleted
        afterwards. Manual browser walkthrough left to the user per [[feedback_no_build_or_run_skill]].

  - [x] 4.29 Payout methods became addable (user report, 2026-09-19: "the payment method is
        disabled")
  - [x] 4.29a Root cause: `payout_methods` was deliberately read-only - "+ Add payout method" was
        a disabled stub on both the Withdraw page and Settings > Payments, on the 3.1i convention
        of not building a form no mockup showed. But `WithdrawView.vue` disables the Withdraw
        button when the list is empty, so any Pal without a seeded row could never withdraw at
        all. With 4.28 making withdrawals real, that stub had to become a form.
  - [x] 4.29b Backend: `POST /wallet/payout-methods`, `PATCH /wallet/payout-methods/{id}/default`
        and `DELETE /wallet/payout-methods/{id}`, same shape as `routers/settings.py`'s payment
        cards. Brand is `paypal` or `bank`; the raw account never lands in the table, only the
        masked `(label, detail)` pair `_mask_account` builds ("Paypal" / "ryun••••@gmail.com",
        "ABA Bank" / "•••• 6789") - nothing reads the full value back, so storing it would be
        keeping a secret for no reader. The first method a Pal adds is forced to be the default
        (otherwise the page still has nothing selected), and deleting the default promotes the
        oldest remaining one. A queued withdrawal pointing at a deleted method keeps its row via
        the existing `on delete set null`, so the admin Payouts tab degrades to "No payout
        method" instead of losing the request.
  - [x] 4.29c Frontend: shared `modals/AddPayoutMethodModal.vue` (brand picker, PayPal email or
        bank name + account number, validation mirroring the backend's so the button is only live
        for input that would be accepted, fields reset on each open). Wired into `WithdrawView.vue`
        - which selects the new method immediately on `added`, since a first method comes back as
        the default - and into `SettingsPaymentsTab.vue`, where the hardcoded stub row gave way to
        the real list with a per-row Set-as-default / Remove menu. `stores/wallet.ts` gained
        `addPayoutMethod`/`setDefaultPayoutMethod`/`removePayoutMethod`; the remove path refetches
        rather than guessing which row was promoted.
  - [x] 4.29d Verification: `ruff check` clean, `oxlint` clean, `vue-tsc --build` adding no new
        errors (same pre-existing four files). Smoke-tested against the real DB with the auth
        dependency overridden: PayPal add auto-defaulted and masked, bank add masked to last four,
        a malformed PayPal email 422'd, setting the bank as default demoted the PayPal row,
        deleting the default promoted the survivor, and both test rows were removed afterwards.
        Manual browser walkthrough left to the user per [[feedback_no_build_or_run_skill]].

  - [x] 4.30 Payout methods narrowed to Card + ABA bank transfer (user request, 2026-09-19)
  - [x] 4.30a Brands went from `('paypal', 'bank')` to `('card', 'bank')`, and bank transfer means
        ABA only, so the bank is no longer a free-text field - `PayoutMethodCreateIn` dropped its
        `bank_name` and `_ABA_BANK_NAME` is a backend constant. `_mask_account` now stores only the
        last four digits for both brands ("Card" / "•••• 4242", "ABA Bank" / "•••• 3456") instead
        of 4.29b's per-brand masking, and a new `_digits` helper strips the spaces and dashes
        people actually type before validating or masking. Validation: 12-19 digits for a card,
        at least 6 for an ABA account. No data migration needed - `payout_methods` had no rows.
  - [x] 4.30b Frontend followed: `AddPayoutMethodModal.vue`'s picker is Card / Bank transfer (ABA)
        with one numeric field and no bank-name input, `mocks/wallet.ts`'s `PayoutMethod.brand`
        union and fallback rows match, and both the Withdraw page and Settings > Payments render
        the Visa asset for a card and `PhBank` for ABA. `mocks/admin.ts`'s Payouts rows lost their
        PayPal labels too, so the admin table does not advertise a brand the app no longer accepts.
  - [x] 4.30c Verification: `ruff check` clean, `oxlint` clean, `vue-tsc --build` adding no new
        errors. Against the real DB: a spaced card number stored as "•••• 4242", a dashed ABA
        number as "•••• 3456", and a too-short card, a too-short ABA account and a now-removed
        `paypal` brand each 422'd. Test rows deleted afterwards. Manual browser walkthrough left to
        the user per [[feedback_no_build_or_run_skill]].

  - [x] 4.31 Payouts are an honest simulation: request -> admin approves -> coins leave the Pal
        wallet (user request, 2026-09-19, after establishing no real rail exists)
  - [x] 4.31a Why there is no real rail, so nobody re-litigates it later: the Stripe key is
        `sk_test_` with `charges_enabled: false`, `payouts_enabled: false` and no capabilities;
        creating a connected account fails with "you've signed up for Connect"; and Stripe's own
        country spec for `KH` reports `supported_bank_account_currencies: {}` (vs a populated map
        for `US`), so Cambodia is a cross-border transfer *recipient* only and has no local payout
        currency. Card payouts would additionally need Elements tokenization - the add-method form
        posts a raw number to our backend, which is not something Stripe would accept from a
        server even in sandbox. So the simulation is the design, not a shortcut.
  - [x] 4.31b The debit moved from request time to approval time, which is the whole point - the
        approval is now the moment money visibly leaves. `create_withdrawal` no longer touches
        `coin_balance`; it logs the payout row as `pending` and the coins go *on hold* instead.
        `_locked_payout_coins` sums undecided (`requested`/`in_progress`) withdrawals and
        `WalletOut` carries it as `locked_payout_coins`, separate from order escrow's
        `pending_clearance_coins`. Without that hold a Pal could queue five full-balance requests,
        or spend the coins out from under a queued one, and approval would then debit money that
        is no longer there.
  - [x] 4.31c `update_withdrawal_status` debits on the first move out of `requested` (so approving
        straight to `paid` and approving via `in_progress` each take the coins exactly once), and
        deletes the `pending` hold row rather than completing it - otherwise the Pal's activity
        would show the same coins leaving twice, once as the hold and once as the real debit.
        Declining now has nothing to refund: it just releases the hold and marks the row `blocked`.
        That is strictly simpler than 4.28d's credit-back, which only existed because the debit
        used to happen too early.
  - [x] 4.31d Detail that sells it: every payout gets a quotable `PO-XXXXXXXX` reference
        (`20260919150000_withdrawal_reference.sql`, unique-indexed), shown in the Pal's withdrawal
        history, used as the admin review modal's title, searchable in the Payouts tab, and named
        in every notification ("PO-D5A09FAB: 800 SC is on its way to your payout method"). The
        Withdraw page splits escrow from the payout hold, and the admin modal states the
        consequence before the click ("Approving debits 1,000 SC from ...'s wallet. Declining
        releases the hold and takes nothing.").
  - [x] 4.31e Verification: `ruff check` and `oxlint` clean, `vue-tsc --build` adding no new
        errors. Full lifecycle against the real DB on a seeded 5,000 SC balance: requesting 1,000
        left the balance at 5,000 with 1,000 locked; approving dropped it to 4,000, released the
        lock and left exactly one activity row ("PO-D5A09FAB approved", -1,000, completed);
        declining a second request left the balance untouched; and a second 3,000 request against
        1,000 of remaining headroom 409'd. All test rows deleted and the balance restored.
        Caught in review: the admin modal's new "approving debits" note was first written as a
        `v-else-if`, which broke the `v-if`/`v-else` chain and hid the action buttons for exactly
        the `requested` payouts they were for. Manual browser walkthrough left to the user per
        [[feedback_no_build_or_run_skill]].

  - [x] 4.32 Card numbers get a Luhn check and real network detection (user request, 2026-09-19,
        after asking whether the number was random - it was: `1111 1111 1111 1111` was accepted)
  - [x] 4.32a Backend: `_luhn_ok` (the check digit every real card carries) now gates
        `create_payout_method` alongside the 12-19 digit length rule, and `_card_network` reads the
        issuer prefix - `4` for Visa, `51-55` or `2221-2720` for Mastercard. It catches a typo or an
        invented number; it cannot prove a card exists, and nothing here can, since no network is
        ever contacted (see [[4.31a]]'s note on there being no rail).
  - [x] 4.32b `payout_methods.brand` now stores the detected network for a card ('visa',
        'mastercard', or the generic 'card') rather than the literal category the client asked for,
        which matches `payment_cards.brand`'s existing 'visa'-style values. `_mask_account` returns
        a `(stored_brand, label, detail)` triple; the request body's `brand` stays the two-value
        category the picker offers. Only Visa and Mastercard have an icon in `assets/`, so every
        other network - Amex included, which passes Luhn fine - stores 'card' and renders the
        `PhCreditCard` fallback rather than being mislabelled as one of the two.
  - [x] 4.32c Frontend: new `utils/card.ts` mirrors the backend's Luhn and prefix rules so the form
        only enables the button for input the API would accept. The modal swaps the scheme mark in
        the field's trailing slot while you type, reflows the number into groups of four, and shows
        "That card number is not valid." only once twelve digits are in - flagging it at the fourth
        would be noise. The Withdraw page and Settings > Payments pick their icon off the stored
        brand via a shared `brandIcon` helper.
  - [x] 4.32d Verification: `ruff check`, `oxlint` and `vue-tsc --build` clean (no new errors).
        Against the real DB, seven numbers through `POST /wallet/payout-methods`: the Visa,
        Mastercard and 2-series Mastercard test numbers stored with the right network and label,
        Amex stored as generic 'card', and `1111…`, `1234…` and a valid Visa with one digit changed
        all 422'd. The same seven run through `utils/card.ts` agree with the backend case for case,
        so the form cannot accept what the API rejects. Manual browser walkthrough left to the user
        per [[feedback_no_build_or_run_skill]].

  - [x] 4.33 One coin-to-USD rate instead of five copies (user report, 2026-09-19: a 900 SC
        balance read "≈ $9.09" right after a $10 top-up)
  - [x] 4.33a Root cause, and it was 4.28a's fault: `COINS_PER_USD` was copy-pasted into five
        views, and the reprice only changed `WithdrawView.vue`. `WalletView.vue`,
        `SubscriptionsView.vue` and `PlayerDashboardView.vue` kept dividing by the old 99, so the
        wallet valued a 900 SC balance at $9.09 instead of the $10 that had just been paid for it.
        Subscriptions and the Pal dashboard were quietly understating their USD figures the same
        way; nobody had noticed because those numbers have no receipt sitting next to them.
  - [x] 4.33b Fix: `utils/coins.ts` owns `COINS_PER_USD` and a `coinsToUsd` helper, and all five
        call sites import it - the duplication was the actual defect, so changing the five copies
        to 90 would have left the next reprice to half-land the same way. Display only: nothing is
        charged at this rate (`topup_packages.price_usd` is the real price) and payouts move no
        money at all (4.31).
  - [x] 4.33c Verification: `oxlint` and `vue-tsc --build` clean (no new errors), and the helper
        checked directly - 900 SC now reads $10.00 and 450 SC reads $5.00, matching the $10 and $5
        tiers exactly. No backend change: the rate was never duplicated there, since the server
        works in coins and reads real prices from `topup_packages`. Manual browser walkthrough left
        to the user per [[feedback_no_build_or_run_skill]].

  - [x] 4.34 Dropped the "Squad Coin Wallet" stub from Settings > Payments (user request,
        2026-09-19). It was a hardcoded row from the mock era - `mockPlayerProfiles.self.handle`
        plus `mockCurrentUser.coinBalance`, never the signed-in account - permanently badged
        "Default". Once 4.29c put the real payout methods above it, the section showed two Default
        badges at once and a balance that did not match the wallet. Removing it made
        `coinIcon`/`mockCurrentUser`/`mockPlayerProfiles` and the `profile` const dead, so those
        went too. The stub had been standing in for the section's empty state, so a Pal with no
        methods would have been left with a bare heading - it now reads "No payout method on file
        yet.", matching `WithdrawView.vue`'s wording. `oxlint` and `vue-tsc --build` clean.

  - [x] 4.35 "Your profile" in the feed sidebar pointed a Pal at `/dashboard/player`, duplicating
        the navbar's Dashboard button. It now links to their public Pal page
        (`/players/{id}`); non-Pals still go to `/feed/me`. `AppHeader.vue`'s Dashboard link is
        unchanged, so the two no longer overlap.

  - [x] 4.36 Per-tab layout on the Pal profile page (user request, 2026-09-19). The page shell
        hardcoded `lg:grid-cols-[280px_1fr]` with `ProfileServiceSidebar` rendered outside the tab
        `v-if` chain, so the service picker sat next to Feeds, Album and Wish, where it means
        nothing and steals a column.
    - [x] 4.36a Sidebar moved inside `ProfileServicesTab.vue`, which now owns the whole
          `[280px_1fr_320px]` grid and takes `services` + a `select` emit. It cannot leak into
          another tab any more. Sticky on scroll.
    - [x] 4.36b Album and Wish are full width now - both are card grids that were being squeezed
          into `1fr` for no reason.
    - [x] 4.36c Feeds keeps a left rail, but a useful one: new `ProfileAboutCard.vue` (tagline,
          the three counts, timezone, languages, rating, price, plus Chat/Book). The sidebar's
          real value was keeping the CTA reachable, so replacing it beat deleting it. Passed via a
          new optional `#aside` slot on `ProfileFeedsTab`, which `MyProfileView.vue` (no player
          row) simply doesn't fill.
    - [x] 4.36d The Chat button's sign-in redirect / seed-Pal / thread-creation logic was about to
          be copy-pasted into the About card, so it went to `composables/usePalChat.ts` first and
          both call sites import it - 4.33a's lesson.
    - [x] 4.36e Sidebar hidden when the Pal has no services (it was rendering an empty search box
          over blank space), and Book hidden in the About card for the same case.
    - [x] 4.36f Active tab now lives in the URL (`?tab=feeds`), so a shared link lands where it was
          copied from and a refresh stops bouncing to Services.
    - [x] 4.36g Verification: `vue-tsc --build` reports no new errors in any touched file (the
          remaining output is the pre-existing `coverImageUrl`/`FeedPost` drift in
          `mocks/playerProfiles.ts` and `stores/players.ts`). Manual browser walkthrough left to
          the user per [[feedback_no_build_or_run_skill]].

  - [x] 4.37 Share button on a feed post did nothing (user request, 2026-09-19). It now shares the
        post's permalink, and that permalink works for a signed-out visitor.
    - [x] 4.37a The share icon opens a small dropdown with one item, "Copy link", which copies
          the permalink and toasts "Link copied" (`composables/useSharePost.ts`). A first pass
          reached for `navigator.share` with a clipboard fallback; the user asked for the plain
          popout instead, so the share-sheet path is gone.
    - [x] 4.37b No new route needed: `/feed/{postId}` (`post-detail`) already existed with no
          `requiresAuth`, and both `GET /feed/posts/{id}` and its comments endpoint already take
          an optional bearer token, so an anonymous request returns the post with `liked`/
          `following` simply false. The permalink was already public - nothing pointed at it.
    - [x] 4.37c What was missing was the signed-out *state* of that page. `FeedPostThread.vue`
          fell back to `mockCurrentUser.id`, so a logged-out visitor saw a Follow button and a
          comment composer that would have 401'd. Like, follow, comment and comment-like now run
          through a `requireAuth()` that redirects to `/login?redirect=...`, the composer is
          replaced by a "Log in to like, comment and follow." prompt, and the Follow/Edit action
          slot is hidden.
    - [x] 4.37d Verification: `vue-tsc --build` and `oxlint` clean on every touched file. Manual
          browser walkthrough (share sheet, copy fallback, incognito permalink) left to the user
          per [[feedback_no_build_or_run_skill]].

  - [x] 4.38 Report Player never reached the admin moderation queue (user request, 2026-09-19).
    - [x] 4.38a Root cause: there was no submit path at all. `ReportProfileModal.vue` emitted
          `submit` and closed itself; `ProfileHeader.vue`'s handler read only `alsoBlock`, set a
          local `blocked` ref and dropped the report. No endpoint existed either - `admin_flags`
          has been in the schema since the initial migration and `GET /admin/flagged-players`
          has always read it, but nothing wrote to it outside seed data.
    - [x] 4.38b `POST /players/{id}/report` (`routers/players.py`, auth required) writes the
          `admin_flags` row. Reports for the same Pal and reason collapse onto one pending row
          and bump `report_count` - that column's whole point, and it keeps the queue readable
          ("3 reports of harassment", not three near-identical cards). A reporter repeating their
          own reason doesn't move the count; a later reporter's details fill an empty details
          field rather than overwriting the first account. Self-reports 400, unknown players 404.
    - [x] 4.38c `playersStore.reportPlayer` + `ProfileHeader.submitReport` file the report and
          toast the result. The modal no longer closes itself: it takes a `submitting` prop and
          the parent closes it only on success, so a failed request keeps the reason and details
          the person typed. Anonymous viewers get the login redirect instead of a 401 toast.
    - [x] 4.38d Dropped the two em dashes in the modal's copy while in there
          ([[feedback_no_em_dashes_ui_copy]]).
    - [x] 4.38e Known gap at the time, fixed in 4.39: "Also block" was still local-only. There is no `blocks`
          table, no endpoint and no enforcement anywhere (messaging, booking, profile reads), and
          `ProfileHeader`'s `blocked` ref is written but never read. The toggle and the separate
          Block menu item both claim an effect they don't have. Real blocking is its own feature -
          flagged to the user rather than half-built here.
    - [x] 4.38f Verification: `ruff` clean, the route registers as
          `POST /players/{player_id}/report`, `vue-tsc --build` and `oxlint` clean on every
          touched file. Submitting a real report and seeing it in the admin queue is left to the
          user per [[feedback_no_build_or_run_skill]].

  - [x] 4.39 Real blocking, closing 4.38e (user request, 2026-09-19). "Also block" and the Block
        menu item both claimed an effect nothing implemented: no table, no endpoint, no
        enforcement, and a `blocked` ref that was written and never read.
    - [x] 4.39a `user_blocks` table (migration `20260919160000_user_blocks.sql`, applied via
          `bunx supabase db push`). One row per direction with a unique (blocker, blocked) pair
          and a no-self check. Stored one-directional so only the person who blocked can lift it;
          enforced both ways everywhere else.
    - [x] 4.39b `core/blocks.py` holds the three shapes every caller needs - `blocked_user_ids`
          (the set to filter lists by), `has_blocked` (direction matters for reads),
          `require_not_blocked` (403 guard for writes). Put in `core/` rather than a router
          because five routers need it; same reasoning as 4.33's `utils/coins.ts`.
    - [x] 4.39c Enforcement, matching what the modal copy promises. Messaging: `start_thread` and
          `send_message` 403, and a blocked account's thread drops out of `list_threads` for both
          sides (rows are kept, so unblocking restores the history). Booking: `create_booking`
          403s before the balance check, so a blocked buyer gets the real reason instead of an
          insufficient-funds message. Profiles: `GET /users/{id}/profile` and `GET /players/{id}`
          403 for the person who was blocked, but stay readable to the blocker - that is where
          Unblock lives. Feed: `/feed` and `/feed/following` filter both directions out. Follows:
          blocking drops the follow both ways and resyncs the counts, and `follow_user` 403s.
    - [x] 4.39d Endpoints: `POST`/`DELETE /users/blocks/{target_id}` and `GET /users/me/blocks`.
          `PublicProfileOut`/`PlayerDetailOut` gained a `blocked` flag so the profile menu knows
          to offer Unblock.
    - [x] 4.39e Frontend: the profile menu flips Block/Unblock, `BlockProfileModal` confirms a
          real call, and the report modal's "Also block" now actually blocks. Blocking hides the
          Follow button and the Chat/Book cards on both the Services tab and the About card
          (4.36c), lifted through a `blocked-change` emit so it lands immediately rather than on
          the next fetch. The Pal profile page shows an "unavailable" empty state on a 403 -
          `usePlayerProfileData` used to fall through to the mock fixtures on any error, which
          would have handed a blocked viewer a fake profile.
    - [x] 4.39f Settings > Privacy > Blocked accounts is real: live count from
          `GET /users/me/blocks` and a Manage modal that lists them with Unblock. The block
          modal has always said "you can unblock them anytime from settings" - now that is true.
          `mockBlockedAccountsCount` deleted.
    - [x] 4.39g Verification: `ruff` clean across `src/backend`, `vue-tsc --build` and `oxlint`
          clean on the frontend (only the pre-existing `coverImageUrl`/`FeedPost` drift remains),
          migration applied and confirmed as the only pending one. End-to-end walkthrough (block,
          check messaging/booking/profile/feed from the other account, unblock) left to the user
          per [[feedback_no_build_or_run_skill]].

  - [x] 4.40 "Take action" now does something (user request, 2026-09-19). Dismiss / Reviewing /
        Take action were all the same `PATCH .../status` call writing a queue label - nothing
        reached the Pal, so the red button that read as an enforcement action enforced nothing.
    - [x] 4.40a "Take action" became a dropdown of the concrete things moderation can do: Send a
          warning (built), Suspend for 7 days (disabled), Ban/Unban player (routes to the ban
          call that was already there, below in the same modal). Suspension stays visibly
          disabled rather than pretending - that was 4.38e's mistake.
    - [x] 4.40b `POST /admin/flagged-players/{id}/warn` sends the Pal a `moderation` notification
          and marks the flag `actioned` in the same call, so the queue can't drift from what was
          actually done. The admin gets an editable message prefilled from the report's reason.
          New `moderation` value on the `notification_type` enum (migration
          `20260919170000_moderation_notification.sql`, applied via `bunx supabase db push`) with
          a `PhWarning` icon; none of the existing types fit. A seed Pal with no linked account
          400s - there is nobody to notify.
    - [x] 4.40c Report attribution: the review modal named the reporter unconditionally, but
          `reported_by` only ever holds whoever filed first (4.38b's dedup), so "5 reports ·
          reported by intmaster" read as one person reporting five times. It names the reporter
          only for a single report and shows the count alone past that.
    - [x] 4.40d Empty details no longer render as a blank card - a reporter who left the box empty
          was giving the modal an empty grey rectangle.
    - [x] 4.40e Verification: `ruff`, `vue-tsc --build` and `oxlint` clean; migration applied.
          Sending a real warning and seeing it arrive in the Pal's notifications left to the user
          per [[feedback_no_build_or_run_skill]].

  - [x] 4.41 Admin Overview's "Commission earned" undercounted and showed coins only (user
        request, 2026-09-19). The user's platform had taken exactly one payout fee and the tile
        read as if nothing had been earned.
    - [x] 4.41a Root cause, and it was not a stub: the figure was real, just one of two streams.
          It summed `bookings.commission_coins` on completed bookings (15% per
          `platform_commission_pct`) and ignored the 20% withheld on every approved payout
          (`wallet.py`'s `WITHDRAWAL_FEE_PCT` → `withdrawals.fee_coins`), which on a platform
          with no completed bookings yet is the only revenue there is.
    - [x] 4.41b `GET /admin/overview` now returns `bookingCommissionCoins` and `payoutFeeCoins`
          alongside their total. Payout fees count only for `in_progress`/`paid` withdrawals -
          `requested` is still awaiting review and `rejected` gave the coins back (4.28b), so
          neither has earned anything.
    - [x] 4.41c The tile shows the USD equivalent next to the coin figure via `coinsToUsd`
          (4.33's single definition, 90 SC = $1) and a breakdown line underneath, so "where did
          this come from" doesn't need a query to answer.
    - [x] 4.41d Dropped the mock fallback on `fetchOverview`. The other admin lists fall back to
          fixtures on a failed request, but a fabricated "41,600 earned" standing in for a failed
          load is worse than the error state the panel already renders - and it is exactly the
          number that made this tile look fake. `mockAdminOverviewStats` deleted with it.
    - [x] 4.41e Verification: `ruff`, `vue-tsc --build` and `oxlint` clean. No migration needed -
          both figures were already stored. Confirming the payout fee now shows against the real
          withdrawal is left to the user per [[feedback_no_build_or_run_skill]].

  - [x] 4.42 Notification dropdown pass, with a "Clear" beside "Mark all read" (user request,
        2026-09-19). The panel could only ever mark things read, so a list of stale payout and
        message rows had no way off the screen, and every row wore the same green circle.
    - [x] 4.42a Backend: `routers/notifications.py` gained `DELETE /notifications/{id}` (per-row
          dismiss) and `DELETE /notifications` (clear all). Both scope the delete by `user_id`,
          since the service-role client bypasses RLS - the per-row one 404s on another account's
          id rather than silently deleting nothing. No migration needed, the rows already exist.
    - [x] 4.42b `stores/notifications.ts` gained `dismiss(id)` and `clearAll()`. Both mutate local
          state only after the request lands, and neither falls back to mocks, matching the
          `markAllRead`/`markRead` convention from 3.10e.
    - [x] 4.42c `utils/notifications.ts` gained `notificationTone`, a per-type icon tint (money
          green, conversation blue, social violet, moderation red) so the list is scannable by
          colour before it is read. Applied in both the panel and `NotificationsView.vue`, which
          had the same uniform `bg-brand-600` circle.
    - [x] 4.42d `NotificationPanel.vue`: "Clear" sits next to "Mark all read", behind a two-step
          inline confirm (the action row swaps to Cancel / Clear all with a one-line warning),
          because a mis-click is unrecoverable. "Mark all read" now disables at zero unread, the
          unread count moved up beside the title, and switching tabs disarms a pending confirm.
    - [x] 4.42e Rows: unread ones get a tinted background plus a brand left edge and bolder text
          instead of relying on one 8px dot, read ones dim to `text-slate-300`, and each row has a
          hover/focus X that dismisses just that notification. The row is now a `div` wrapper
          around the click target so the X is not a button nested inside a button. Added the
          skeleton the panel never had, an unread-specific empty state, and a "(N more)" count on
          "See all notifications".
    - [x] 4.42f Verification: `ruff check` clean and `vue-tsc --build`/`oxlint` clean for the four
          touched files (`vue-tsc` reports pre-existing errors in `mocks/playerProfiles.ts`,
          `stores/players.ts`, `stores/messages.ts` and `StepGames.vue` from the in-flight service
          cover-image work, none in these files). Deliberately did not run `ruff format` on the
          router: the repo is written at 100 cols with no ruff config, so the default 88 reflows
          untouched code. Clicking through the real dropdown left to the user per
          [[feedback_no_build_or_run_skill]].

  - [x] 4.43 Service Detail page hero (user request, 2026-09-19). A service with no uploaded
        cover rendered a 640px-tall empty picture frame above the fold, and the title card
        underneath repeated the same header a second time.
    - [x] 4.43a `lib/covers.ts` gained `gameCoverForName(name)`, so a service with no uploaded
          cover falls back to its game's cover art. Service titles are the game name the Pal
          picked during onboarding, so the slug + CDN manifest lookup already used by the game
          rails works unchanged. Replaces the copy of that lookup in `ProfileServicesTab.vue`
          and the one added to `PlayerServicesView.vue` (My services had the same empty-frame
          problem on its cards).
    - [x] 4.43b `ServiceDetailView.vue`: the cover and the title card are one banner now, the
          header overlaid on a bottom-weighted scrim when there is art and sitting on the plain
          panel when there isn't - so no cover means no empty frame at all, rather than an
          empty frame. Banner is `h-64 sm:h-80 lg:h-96`.
    - [x] 4.43c Same file, empty states the page had no handling for: the real avatar renders
          via `resolveAvatarUrl` (it was a hardcoded grey `div`), "About this service" hides
          when the description is empty, "Avg response" hides when there is no value, and the
          tag row drops the tag that just repeats the title.
    - [x] 4.43d Verification: `vue-tsc --build` and `oxlint` clean for the touched files
          (`vue-tsc`'s pre-existing errors in `mocks/playerProfiles.ts`, `stores/players.ts`,
          `stores/messages.ts` and `StepGames.vue` are unchanged). Seeing it in the real app is
          left to the user per [[feedback_no_build_or_run_skill]].

  - [x] 4.44 Review highlights + tips stop being UI-only (user request, 2026-09-19). 3.6a parked
        both as "collected by the modal, dropped on submit", which meant a buyer could pick a
        200 SC tip and watch it silently vanish. Reviews themselves stay read-only on the service
        page: `POST /reviews` needs a completed booking, so there is nothing valid a visitor
        could submit from there.
    - [x] 4.44a Migration `20260919180000_review_highlights_tip.sql`: `reviews` gains
          `highlights text[]` and `tip_coins integer`, and `wallet_transaction_kind` gains
          `tip` so a tip is its own ledger line rather than masquerading as an `order`.
    - [x] 4.44b Backend `routers/reviews.py`: `ReviewCreateIn` accepts `highlights`/`tipCoins`.
          Highlights are validated against the modal's six options (unknown values 422 rather
          than storing arbitrary text that the profile then renders). A tip debits the buyer and
          credits the Pal through `adjust_coin_balance`, both keyed to the booking; the balance
          is checked before the review is inserted so a buyer who can't afford the tip doesn't
          end up with a review and no tip. Tipping a seed Pal with no linked account is a 409.
    - [x] 4.44c Backend: `ReviewOut` returns both fields, and the Pal's notification names the
          tip when there is one.
    - [x] 4.44d Frontend: `PlayerReview`/`ReviewApiOut` carry `highlights`/`tipCoins`
          (`stores/players.ts`), `ReviewPayload` carries them too (`stores/bookings.ts`), and
          `MyBookingsView`'s `confirmReview` stops dropping them on the floor.
    - [x] 4.44e Frontend `ServiceReviewsPanel.vue`: a review renders its highlight chips and a
          tip badge, and the empty state explains that reviews come from completed orders
          instead of just saying "No reviews yet."
    - [x] 4.44f Verification: `ruff check` clean, `vue-tsc --build`/`oxlint`/`eslint` clean for
          the touched files (`vue-tsc`'s pre-existing errors listed in 4.42f are unchanged).
          `20260919180000` is written but NOT pushed - applying it to the linked project is the
          user's call, and until it lands `POST /reviews` will fail on the two new columns.
          Live smoke test (tip debits the buyer, credits the Pal, shows as `tip` in Wallet) is
          left to the user per [[feedback_no_build_or_run_skill]], as is 3.6b's replay.
    - [x] 4.44g Not in scope, noted while here: a tip credits the Pal in full, no
          `platform_commission_pct` taken, unlike a completed booking. That reads like the right
          default for a tip but it was never decided anywhere, so it's recorded rather than
          assumed. `LeaveReviewModal` also doesn't show the buyer's coin balance, so an
          unaffordable tip is only caught on submit (recoverable now - the modal stays open).

  - [x] 4.45 Chat alerts move off the notification bell (user request, 2026-09-19). A new
        message was producing a `message` notification in the dropdown while the messages button
        sat there silent, so the same event was reported in the wrong place.
    - [x] 4.45a Frontend `stores/notifications.ts`: an `isChat` split - the exported
          `notifications`/`unread`/`unreadCount` now cover everything except `message`, and a new
          `messageUnreadCount` counts the chat ones. `markThreadRead(threadId)` retires a
          conversation's chat alerts.
    - [x] 4.45b Backend `routers/notifications.py`: `POST /notifications/read-all` and
          `DELETE /notifications` take an optional `exclude_type` (the dropdown passes `message`,
          so "Mark all read"/"Clear" no longer wipe the messages badge), plus
          `POST /notifications/threads/{thread_id}/read` behind 4.45a's `markThreadRead`.
    - [x] 4.45c Frontend `AppHeader.vue`: the messages button carries the unread count badge
          (9+ cap, matching ring treatment as the bell dot) and an aria-label that names the
          count; the mobile menu's Messages link gets the same count.
    - [x] 4.45d Frontend `stores/messages.ts`: `selectThread` calls `markThreadRead` so opening
          the conversation is what clears the badge. Best-effort - a failed call leaves the badge
          up rather than surfacing a toast. `NotificationPanel`'s row click loses its now-dead
          message/threadId branch.
    - [x] 4.45e Verification: `ruff check` clean, `vue-tsc` shows no new errors (the
          pre-existing set from 4.42f/4.44f is unchanged). Not run live per
          [[feedback_no_build_or_run_skill]].

  - [x] 4.46 Chat failures stop showing raw error text (user report, 2026-09-19). Clicking
        "Chat" surfaced `useNotificationsStore(...).markThreadRead is not a function` in a toast
        - a stale HMR module instance, but the copy would have been unreadable for any internal
        error, and badge bookkeeping should never have been able to fail the action at all.
    - [x] 4.46a Frontend `stores/messages.ts`: `selectThread`'s 4.45d `markThreadRead` call is
          wrapped in try/catch and no longer awaited, so a throw there can't reject
          `selectThread`/`startThread` and abort opening the chat.
    - [x] 4.46b Frontend `utils/errors.ts` (new): `userErrorMessage(err, fallback)` passes
          through an `ApiError` detail under 500 (those are written for a person - "You already
          have a booking with this Pal") and swaps anything else for the fallback.
    - [x] 4.46c Frontend: all four "Couldn't start chat" sites use it - `usePalChat.ts`,
          `ServiceDetailView`, `OrderDetailView`, `MyBookingsView`.
    - [x] 4.46d Verification: `vue-tsc` shows no new errors, `oxlint`/`eslint` clean on the
          touched files. Not run live per [[feedback_no_build_or_run_skill]].
    - [ ] 4.46e Not done: the same `err instanceof Error ? err.message` pattern is used by
          roughly every other toast in the app (bookings, wallet, admin, settings). Left alone
          rather than swept in one pass - worth a dedicated pass if the copy matters.

  - [x] 4.47 "Chat" opens Messages immediately (user report, 2026-09-19). Clicking Chat sat on
        the old page through `POST /messages/threads` and then a full message fetch before it
        navigated, and `MessagesPanel` then refetched the inbox and re-selected a thread on
        arrival - four sequential round trips, two of them with no feedback at all. Worse, the
        panel landed on `threads[0]`, not necessarily the Pal just clicked.
    - [x] 4.47a Frontend `composables/usePalChat.ts`: no network at all now - it keeps the
          sign-in redirect and the seed-Pal guard (both local) and pushes
          `/messages?with=<user id>`. Navigation is instant.
    - [x] 4.47b Frontend `MessagesPanel.vue`: takes `?with=`, does the find-or-create itself
          under an "Opening chat..." pane, then `router.replace`s to `?thread=<id>` so a reload
          or Back doesn't re-post. `onMounted` no longer awaits `fetchThreads` before opening
          the requested conversation - the inbox loads alongside it. `openThreadFromQuery` skips
          a thread that is already active, so the `?with=` -> `?thread=` rewrite doesn't fetch
          the conversation twice.
    - [x] 4.47c Frontend `stores/messages.ts`: `fetchThreads` keeps the active thread if the
          response doesn't contain it. 4.47b runs the inbox fetch and the thread creation
          concurrently, so a thread created after the server read the list would otherwise
          disappear the moment the list landed, taking the open conversation with it.
    - [x] 4.47d Frontend: the duplicated `handleMessage` in `ServiceDetailView`,
          `OrderDetailView` and `MyBookingsView` is gone - all three call `usePalChat` (the
          copies predate it). Two buttons that only ever pushed `/messages` and dumped you in
          whatever chat was first now open the right one: `ServiceDetailView`'s "Chat first" and
          `OrderConfirmationView`'s "Message your Pal".
    - [x] 4.47e Verification: `vue-tsc` shows no new errors, `eslint`/`oxlint` clean on the
          touched files. Not run live per [[feedback_no_build_or_run_skill]].

  - [x] 4.48 Authors can delete their own posts (user request, 2026-09-19). The own-post action
        was an edit pencil only, so a post could be rewritten but never removed.
    - [x] 4.48a Backend `routers/feed.py`: `DELETE /feed/posts/{post_id}`, author-only (403
          otherwise), 204. Comments, likes and saved rows cascade off the `posts` foreign keys,
          so the only explicit follow-up is `_refresh_posts_count`. Bucket images are left
          behind, same as an edit that drops one.
    - [x] 4.48b Frontend `stores/feed.ts`: `deletePost(postId)` drops the post from `posts`,
          `following`, `saved` and `current`, clears its cached comments and decrements the
          signed-in account's posts tally via `bumpMyCounts`.
    - [x] 4.48c Frontend `components/feed/PostAuthorMenu.vue` (new): the pencil becomes a kebab
          menu with "Edit post" and a red "Delete post" behind `ConfirmModal`, since the delete
          takes the comments and likes with it.
    - [x] 4.48d Frontend: wired into all three own-post surfaces - `FeedView`,
          `UserDashboardView` and `FeedPostThread` (the thread also emits `deleted` and then
          `back`, so the permalink view routes away and the parents holding their own post list
          - `UserDashboardView`, `PublicProfileView`, `ProfileFeedsTab` - prune their copy).
    - [x] 4.48e Verification: `vue-tsc` shows no new errors, `oxlint`/`prettier` clean on the
          touched files. Not run live per [[feedback_no_build_or_run_skill]].

  - [x] 4.49 Chat composer cleanup, image messages and Messages load-speed pass (user request,
        2026-09-20). The composer's emoji button and the conversation header's kebab were both
        dead decoration, the paperclip did nothing, and both Messages endpoints read far more
        rows than the page renders.
    - [x] 4.49a Migration `20260920090000_message_images.sql`: `messages.image_url` (nullable)
          plus a relaxed `body` so an image-only message is a real row, a public
          `message-images` bucket (webp only, same posture as `post-images`), and the two
          indexes the summaries RPC needs - `(thread_id, created_at desc)` and a partial unread
          index.
    - [x] 4.49b Migration `20260920091000_message_thread_summaries.sql`: RPC collapsing
          `GET /messages/threads`' four round-trips (threads, per-user states, blocks, every
          message ever sent in any of them) into one - `distinct on` for each thread's last
          message and a grouped count for unread, with the deleted/blocked filtering done in
          SQL.
    - [x] 4.49c Backend `routers/messages.py`: `list_threads` runs the RPC; `list_messages`
          takes `limit`/`before` and returns the newest page in chronological order, checks
          membership without the display-name join, and defers the read-marking UPDATE to a
          background task; `send_message` becomes multipart so an image can ride along, storing
          it as WebP via `upload_image_as_webp`.
    - [x] 4.49d Frontend `utils/image.ts` (new): canvas downscale + re-encode before upload, so
          a phone photo leaves the device at roughly its display size instead of several MB.
    - [x] 4.49e Frontend `stores/messages.ts`: `sendMessage({ body, image })` posts multipart,
          `fetchMessages` pages, `loadEarlier` prepends, `selectThread` keeps the cached
          conversation on screen while it refreshes, and realtime carries `imageUrl`.
    - [x] 4.49f Frontend `components/messages/MessagesPanel.vue`: emoji button and header kebab
          removed, paperclip opens a real picker with a removable preview, image bubbles render
          in the transcript, the pane auto-scrolls to the newest message and a "Load earlier
          messages" button sits above the first one.
    - [x] 4.49g Verification: both migrations applied with `bunx supabase db push` and the RPC
          smoke-tested against the live project through the service-role client (one thread
          back, correct preview and unread count); the FastAPI app imports and its OpenAPI
          shows the multipart POST plus the new `limit`/`before` query params. `vue-tsc` shows
          the same 16 pre-existing errors and no new ones, `oxlint`/`prettier` clean on the
          touched frontend files, `ruff` clean on `routers/messages.py`. Not run live per
          [[feedback_no_build_or_run_skill]].

  - [x] 4.50 Settings rename propagation and the Profile/Account tab overlap (user request,
        2026-09-20). Renaming on the Account tab left the Pal profile page showing the old name,
        and the Profile tab repeated the same "Display name" input with no Save button under it.
    - [x] 4.50a Backend `routers/users.py`: `PATCH /users/me` mirrors a `display_name` change
          onto the Pal's `players` row. `players.display_name` is a second copy that browse
          cards, search and the profile header all read directly, so a rename that only touched
          `users` never reached the marketplace. `handle` needs no mirror - it was unified onto
          `users` back in 4.14.
    - [x] 4.50b Migration `20260920140000_players_bio.sql`: `players.bio`, the longer About
          paragraph. Settings has shown a Bio textarea since Phase 1 with no column behind it -
          `tagline` stays the one-liner on browse cards, `bio` is the paragraph under it.
    - [x] 4.50c Backend `routers/players.py`: `PATCH /players/me` (tagline, bio, languages) for
          the Profile tab's save; `display_name` is deliberately not accepted, so renaming has
          exactly one home. A `languages` edit re-derives the legacy singular `language` column
          the About card and browse filters still read, same as creation does.
    - [x] 4.50d Frontend `stores/players.ts`: `bio` on `MyPlayerProfile`/`PlayerProfile` and
          `updateMine()`, which replaces `mine` from the response like `updateAvatar` does.
          `ProfileAboutCard.vue` renders the bio under the tagline.
    - [x] 4.50e Frontend `SettingsProfileTab.vue`: rebuilt as the public-profile editor only -
          photo, headline, bio, languages (add/remove chips) and a Save changes button that is
          disabled until something actually changes. The duplicate Display name input is gone,
          replaced by a line pointing at the Account tab (`@navigate` up to `SettingsView.vue`).
          The Preferences card (online status, email/push notifications - already owned by the
          Privacy and Notifications tabs) and the Account & security card (email, region,
          password, 2FA - already owned by Account and Security) both go; "Instant booking" went
          with them, never having been wired to anything.
    - [x] 4.50f Frontend `SettingsAccountTab.vue`: the mock-only "Language" select is dropped
          now that the Profile tab owns languages for real; Timezone moves up into the grid.
    - [x] 4.50g Verification: migration applied with `bunx supabase db push`; OpenAPI shows
          `PATCH /players/me` and `bio` on `PlayerDetailOut`; `ruff` clean on both routers;
          `vue-tsc` shows the same 16 pre-existing errors and no new ones;
          `oxlint`/`prettier` clean on the touched frontend files. Not run live per
          [[feedback_no_build_or_run_skill]].

  - [x] 4.51 "Change payout settings" was a dead disabled button, and the payout schedule next
        to it was mock text (user request, 2026-09-20).
    - [x] 4.51a Frontend `views/SettingsView.vue`: the open tab moved from a local `ref` into
          `?tab=`, so other pages can deep-link into it. Unknown keys and keys the current user
          has no tab for fall back to the first tab; switching uses `router.replace` so tabs
          don't pile up in history.
    - [x] 4.51b Frontend `views/PlayerEarningsView.vue`: the button is enabled and points at
          `/settings?tab=payments`, which has had a full payout-method manager (add, set
          default, remove) since 4.32.
    - [x] 4.51c Backend `routers/players.py`: `_normalize_payout_schedule` maps the hyphenated
          "bi-weekly" the wizard and the Settings select speak onto the `payout_schedule` enum's
          `bi_weekly`. This also fixes Become-a-Pal: picking Bi-weekly sent a value the enum
          rejects, so the insert failed. No migration - `players.payout_schedule` has existed
          since the initial schema, nothing had ever read it back.
    - [x] 4.51d Backend `routers/players.py`: `PATCH /players/me` accepts `payout_schedule`, and
          `EarningsOut` carries `payout_schedule` plus the `next_payout_date` it implies
          (`_next_payout_date`: Mondays for weekly, even-ISO-week Mondays for bi-weekly, the 1st
          for monthly). The date is derived backend-side so the Dashboard and Earnings pages
          can't drift. It stays off `PlayerDetailOut` deliberately - that shape is also the
          public `GET /players/{id}` response.
    - [x] 4.51e Frontend `stores/players.ts`: `payoutSchedule`/`nextPayoutDate` on
          `PlayerEarnings`, and `updateMine()` takes `payoutSchedule` and refetches earnings
          after one (the next payout date moves with it).
    - [x] 4.51f Frontend `SettingsPaymentsTab.vue`: the Payout schedule select reads through to
          the saved value instead of a hardcoded "Weekly" and persists on change with a toast on
          either outcome. The "Daily" option is gone - the enum has no such value.
          `PlayerEarningsView.vue`'s Schedule and Next payout rows now read the API instead of
          `mocks/dashboardStats.ts`, which this page no longer imports.
    - [x] 4.51g Verification: `_next_payout_date`/`_normalize_payout_schedule` smoke-tested
          directly over all three schedules either side of a Monday; `ruff` clean on
          `routers/players.py`; `vue-tsc` shows the same 16 pre-existing errors and no new ones;
          `oxlint`/`prettier` clean on the touched frontend files (`PlayerEarningsView.vue` was
          not prettier-clean at HEAD, so its diff carries a whole-file reindent). Not run live
          per [[feedback_no_build_or_run_skill]].

  - [x] 4.52 Account deletion left every uploaded file behind in Storage (user request,
        2026-09-20). `DELETE /users/me` relied entirely on the 3.13c FK cascade, which is
        complete for rows but never reaches `storage.objects`.
    - [x] 4.52a Audit first: every FK into `users`/`players` across all migrations does cascade
          (or `set null` on `admin_flags.reported_by`, deliberately), and `auth.admin.delete_user`
          defaults to a hard delete, so the row side needed no change. The gap was five buckets -
          `avatars`, `post-images`, `message-images`, `service-covers` (all public, so their URLs
          kept serving after the account was gone) and the private `id-documents`, which holds
          the KYC ID scans.
    - [x] 4.52b Backend `core/storage.py`: `remove_prefix(bucket, prefix)` deletes everything one
          level under `prefix/` and returns the count. Every upload path in the app is
          `{owner_id}/{file}`, so one listing per prefix covers it; it re-lists after each batch
          because Storage caps a listing at 100 rows. An empty prefix or one containing `/` is a
          `ValueError` - the empty prefix would list the bucket root and delete every account's
          files, so that can't be reachable by accident.
    - [x] 4.52c Backend `routers/users.py`: `delete_me` sweeps the four user-keyed buckets plus
          `service-covers` under the Pal's `player_id` (covers belong to the player row, not the
          account), then deletes the auth user. Per-bucket failures are logged and skipped rather
          than raised - being unable to delete your account because of one stray file is the
          worse outcome, and the rows naming those files are gone either way.
    - [x] 4.52d No other account is affected: only `{owner_id}/` prefixes are ever passed in, and
          every file removed is one whose owning row (post, message, service, player) the cascade
          deletes in the same request, so nothing that survives can point at a missing image.
    - [x] 4.52e Verification: `remove_prefix` exercised live against the `avatars` bucket on the
          linked project with a throwaway `zz-selftest-<uuid>` prefix - 3 files uploaded, 3
          removed, prefix empty afterwards, and both guard cases (`''`, `'a/b'`) raise. OpenAPI
          still shows `DELETE /users/me`; `ruff` clean on `core/storage.py` and `routers/users.py`.
          Not run live in the app per [[feedback_no_build_or_run_skill]].

  - [ ] 4.53 A tip was taken from the buyer and never paid to the Pal (user report, 2026-09-20).
        `POST /reviews` did the submission as eight separate PostgREST round-trips and a dropped
        Supabase connection landed between the debit and the credit. Booking 934cc068 got its
        review and lost the buyer 200 SC; Lucid was never paid; and with a review on record the
        buyer's retry could only ever come back "This order has already been reviewed".
    - [x] 4.53a Root cause, two layers. The handler was non-atomic - review insert, two rating
          recomputes, then debit and credit as separate calls, with no way to undo the ones that
          had already committed. Underneath it, `httpx.RemoteProtocolError: Server disconnected`:
          the `lru_cache`d Supabase client pools HTTP/2 connections with no keepalive bound, and
          postgrest-py's `send_with_retry` only retries on response *status* codes, so a socket
          the server had already closed raises straight out of the call site.
    - [x] 4.53b Migration `20260920150000_review_tip_atomic.sql`: `submit_review(...)` does the
          whole submission in one transaction - `select ... for update` on the booking to
          serialise concurrent submits, the ownership/completed/already-reviewed checks, the
          insert, both rating recomputes, and both sides of the tip with the buyer's row locked
          for the balance check. Custom SQLSTATEs (SU404/409/410/411/412) carry the failure
          reasons out so the router maps to HTTP without matching message strings. Plus a unique
          index on `reviews (booking_id)` - the read-then-insert check could be raced.
    - [x] 4.53c Backend `routers/reviews.py`: `create_review` now reads only what the
          notification text and the tip's ledger `detail` need, then calls the RPC and translates
          `APIError.code` through `RPC_ERROR_STATUS`. `_recompute_after_review`/`_recompute_rating`
          are gone (now SQL) and the handler no longer touches `core/wallet.py`. The notify call
          moved after the commit and is wrapped: past that point the coins have moved, so a
          dropped connection there must not come back as a failed submission the buyer retries
          into a 409. It logs and the review still returns 201; a lost notification is cheaper.
    - [x] 4.53d Backend `core/supabase.py`: one shared `httpx.Client` with
          `keepalive_expiry=15s`, so pooled connections are retired well inside the server's idle
          window, and `_RetryOnDisconnectTransport`, which replays `RemoteProtocolError`/
          `ReadError`/`WriteError` for GET/HEAD/OPTIONS only. POSTs deliberately fail loudly -
          with 4.53b every write that matters is one transaction, so the caller retrying is
          correct and silent replay could double one that actually committed. The client also
          now backs Storage and Auth, so its 60s timeout replaces PostgREST's 120s and Storage's
          20s: room for an image upload, still a cap on a hung query.
    - [x] 4.53e Frontend: `stores/bookings.ts` marks the order reviewed on a 409 too (otherwise
          the row keeps offering "Leave review" for an order that can never take one) and
          refetches the wallet after a tip so the header balance moves, same convention as
          `wallet.ts`'s `requestWithdrawal`. `LeaveReviewModal.vue` takes a `submitting` prop
          that locks Submit and Skip while the request is in flight, and `MyBookingsView.vue`
          drives it and closes the modal on an already-reviewed 409.
    - [ ] 4.53f Outstanding: booking 934cc068's 200 SC is still stranded - Levi was debited,
          Lucid was not credited. The repair (credit 200 SC to Lucid plus the matching
          `wallet_transactions` row) was written but blocked by the sandbox as a live-data write,
          so it needs the user to run or approve it.
    - [x] 4.53g Verification: migration pushed to the linked project with `bunx supabase db push`.
          Error paths exercised live against it - already-reviewed returns SU410, another user's
          booking and an unknown id both SU404, all arriving as `APIError.code`. Atomicity proven
          on a real completed unreviewed booking by requesting a tip larger than the buyer's
          balance: SU412 raised, and the review count for that booking and the buyer's balance
          were both unchanged afterwards, so the insert and recomputes rolled back with the tip.
          `ruff check` clean on both backend files (the repo has no ruff config, and `ruff format`
          at its default 88 columns would reflow most of the file, so it stays unrun as before);
          `vue-tsc` shows the same 16 pre-existing errors and no new ones; `oxlint` clean. All
          three touched frontend files were already prettier-unclean at HEAD, so they are left
          as-is rather than carrying a whole-file reindent. Not run live in the app per
          [[feedback_no_build_or_run_skill]].

  - [x] 4.54 Admin alerts bell (user request, 2026-09-20). The Admin panel had no way to learn
        that anything had arrived: every queue only showed its count once you opened its tab, so
        a report, a dispute, a payout request or a Pal application sat unseen until the admin
        happened to click through all five tabs.
    - [x] 4.54a Backend `routers/admin.py`: `GET /admin/notifications` merges four queries into
          one time-ordered feed - pending flags, open disputes, `requested` withdrawals and
          `pending_review` players - each capped at 25 rows. Deliberately only the states nobody
          has picked up: `reviewing`/`investigating`/`in_progress` are already in someone's
          hands, and alerting on them would make the bell a second copy of the tabs. Deciding an
          item is therefore what retires its alert, so the feed can't drift from the work. Ids
          are source-prefixed (`flag:`, `dispute:`, `withdrawal:`, `application:`) so the four id
          spaces can share one read set. Same no-auth posture as the rest of the router.
    - [x] 4.54b Frontend `stores/admin.ts` + `mocks/admin.ts`: `fetchNotifications` with the
          usual mock fallback, plus `unreadNotifications`/`unreadNotificationCount` and
          mark-read. Read state lives in `localStorage` under `squadup-admin-read-alerts`: the
          feed is derived, not stored, and there is no admin account to hang a `read` column off.
          It outlives the session on purpose - a reload should not make yesterday's queue look
          new. Every fetch drops ids the feed no longer carries, so the key can't grow forever.
    - [x] 4.54c Frontend `components/admin/AdminNotificationPanel.vue`: the bell's dropdown,
          built to the same shape as the user-facing `NotificationPanel.vue` (skeleton rows,
          unread tint plus left rail, "Mark all read"), with one icon and tint per source. A row
          click marks it read and opens the tab that resolves it.
    - [x] 4.54d Frontend `views/AdminView.vue`: a header bar above the content column carrying
          the bell with an unread dot, and the brand link on mobile where the sidebar is hidden.
          The feed is fetched on login and polled every 60s - the admin sits on this screen while
          the work arrives elsewhere. `SettingsNav.vue` grew an optional `badge` per tab (unused
          by Settings), so each queue also shows its own unread count in the sidebar and in the
          mobile tab strip.
    - [x] 4.54e Verification: the handler run live against the linked project returns `[]` and
          all four selects (including the `bookings(order_number, users(display_name))` embed)
          execute - the database currently holds no pending flags, open disputes, `requested`
          withdrawals or `pending_review` players, which is exactly the empty state. `ruff check`
          clean on `routers/admin.py`; `vue-tsc` shows the same 16 pre-existing errors and no new
          ones; `oxlint` clean on all five frontend files. Not run live in the app per
          [[feedback_no_build_or_run_skill]].

  - [x] 4.55 Chilling service covers (user request, 2026-09-22). The Chilling tab of All Services
        drew every card as a bare tinted box: the art existed in `assets/chilling/` but nothing
        referenced it, so nine services shipped with no cover at all.
    - [x] 4.55a `views/AllServicesView.vue`: each `chillingSections` item carries an `image`, and
          the card renders it under the same bottom-up gradient the Pal cards use, so the label
          and caption stay readable over a bright cover. Hover moved to `group-hover` on the
          overlay now that the image, not the card background, is what tints.
    - [x] 4.55b The three top-level service cards (Hobbies Talk, E-Chat, Watch Together) now read
          from `assets/chilling/` too, and the older root-level `hobbies.jpg`/`echat.jpg`/
          `watch_together.jpg` imports are gone. One folder is the source of truth per service,
          so a service can't end up with two different covers on one screen.

  - [x] 4.56 Footer pages: Report, Customer Service, About Us, Update Log (user request,
        2026-09-22). Four footer links rendered as plain `<span>`s because they had no route
        behind them, and a fifth (Business Inquiry) was never going to get one.
    - [x] 4.56a `views/ReportView.vue` + `/report`: routes a report to the flow that can actually
          carry it - a profile report needs the profile (the existing `POST /players/{id}/report`
          is player-scoped), an order dispute needs the booking, a post needs the post. A standalone
          form would have had nowhere to post to, so the page triages instead of collecting.
          Carries the same confidentiality line as `ReportProfileModal.vue` plus an emergency block.
    - [x] 4.56b `views/CustomerServiceView.vue` + `/support`: contact channels (in-app order help,
          email, Help Center), common-request shortcuts into `/bookings` and `/faq`, and stated
          response times. No fake contact form for the same reason as 4.56a.
    - [x] 4.56c `views/AboutView.vue` + `/about`: mission, stats, values, milestones, and a
          Become a Pal call to action. Static content, in line with the other marketing pages.
    - [x] 4.56d `views/ChangelogView.vue` + `/changelog`: release list built from the real recent
          work (4.54 admin alerts, atomic reviews, KHQR, feed uploads, wallet), tagged
          New/Improved/Fixed.
    - [x] 4.56e `components/layout/AppFooter.vue`: the four links now carry `to`, Business Inquiry
          is removed. Every footer link resolves to a route; the `<span>` fallback branch stays for
          the bottom-row language label.
    - [x] 4.56f Verification: `oxlint` clean on all six touched frontend files; `vue-tsc` shows the
          same 16 pre-existing errors and no new ones. Not run live in the app per
          [[feedback_no_build_or_run_skill]].
  - [x] 4.57 ABA PayWay replaces Stripe for card top-ups (user request, 2026-09-26). Ported from
        Niyey's PayWay checkout (`niyey/backend/src/backend/services/payway.py`,
        `routers/payway.py`, `frontend/src/utils/payway.ts`). Card details are typed into PayWay's
        own popup (`checkout2-0.js`), never into SquadUp. A top-up is only credited after PayWay's
        signed Check Transaction API reports it `APPROVED` for the right amount. KHQR stays the
        4.4 simulated flow, only the card path moves.
    - [x] 4.57a Backend: `core/payway.py` (HMAC-SHA512 signing, signed card popup fields,
          Check Transaction) + `PAYWAY_*` settings replace `STRIPE_SECRET_KEY`; `stripe` dependency
          removed.
    - [x] 4.57b Migration: `payway_topups` table (one row per card attempt, keyed by `tran_id`) and
          `wallet_transactions.stripe_payment_intent_id` renamed to `payment_reference`.
    - [x] 4.57c Backend: `POST /wallet/topup/card`, `GET /wallet/topup/card/{tran_id}` (settles on
          poll) and the public `POST /wallet/topup/card/callback` pushback replace
          `/topup/payment-intent` + `/topup`. A conditional pending-to-paid update makes a racing
          poll and callback credit exactly once.
    - [x] 4.57d Frontend: `lib/payway.ts` popup loader, store methods, `WalletView.vue` card path
          opens the PayWay popup and polls; Stripe Element, `lib/stripe.ts`,
          `@stripe/stripe-js` and `VITE_STRIPE_PUBLISHABLE_KEY` removed. Card network logos from
          `aba_resource/`.
    - [x] 4.57e Verification: `ruff check` clean; `oxlint` clean on the touched files; `vue-tsc`
          shows the same 16 pre-existing errors and no new ones. Sandbox smoke test against the
          real PayWay sandbox (Niyey's merchant profile, creds copied into `backend/.env`): Check
          Transaction accepts our hash (`tran_id not found`, not `wrong hash`) and the signed card
          form gets PayWay's 302 to its hosted card page. ERD regenerated
          (`docs/erd/generate_erd.py`). `20260926120000_payway_topups.sql` pushed to the linked
          project on 2026-09-26 (first attempt 403'd while the CLI was logged into the Niyey
          account, which made the first card top-up 500). A real card payment through the popup is left to the user per
          [[feedback_no_build_or_run_skill]].
  - [x] 4.58 Real ABA KHQR replaces the fake 4.4 QR (user request, 2026-09-26). "QR Scan" now
        shows a genuine KHQR from PayWay's `generate-qr` (scannable by ABA Mobile or any Bakong
        app), laid out to `aba_resource/qr_guideline.png`'s "on Website Popup" style. For the
        demo, a timer still auto-succeeds the payment; a real scan settles it the same way.
    - [x] 4.58a Migration: `payway_topups.method` (`card` | `khqr`).
    - [x] 4.58b Backend: `payway.generate_qr`; `POST /wallet/topup/khqr` records a `khqr` row and
          returns the QR string; `GET /wallet/topup/khqr/{tran_id}` settles it (PayWay approval,
          or the demo timer). In-memory `_khqr_sessions` and `/complete` removed.
    - [x] 4.58c Frontend: `KhqrCard.vue` rebuilt to the guideline (ABA PAY logo 196x31, red KHQR
          header with folded corner, merchant + amount, perforation, 144px code with the Bakong
          badge, scan caption, 24px safe space), ported from Niyey. Store + `WalletView.vue`
          modal updated, with an expiry countdown.
    - [x] 4.58d Verification: `ruff check` clean; `oxlint` clean on the touched files; `vue-tsc`
          shows the same 16 pre-existing errors. Migration pushed. Sandbox `generate-qr` returns a
          real KHQR (`000201...`) for all four package prices. It first failed with "Wrong Hash."
          because `amount` went out as a JSON number: whole-dollar 10.0 never matches the hashed
          "10.00". It's now sent as the hashed string (Niyey has the same latent bug). Settle
          logic checked on an unsaved row: fresh KHQR `pending`, over 5 min `expired`, card never
          auto-succeeds. ERD regenerated. Demo auto-confirm is `KHQR_AUTO_CONFIRM_SECONDS` (10s)
          in `routers/wallet.py`.
    - [x] 4.58e Fix (user report, same day): on success the KHQR modal closed and reopened.
          `fetchWallet()` flips `walletStore.loading`, and `WalletView.vue` swaps the whole page,
          modal included, for its skeleton while that's true. `fetchWallet({ silent: true })` now
          refreshes in place, used after card and KHQR payments. The KHQR modal stays open on
          success ("N SC added to your wallet" + Done) instead of auto-closing;
          `POST /wallet/topup/khqr` returns `coins` for that line.
  - [x] 4.59 Payouts stay simulated; demo payout card saves (user request, 2026-09-26). Checked
        PayWay's Payout API against the sandbox: our hash is accepted, but beneficiaries must be
        RSA-encrypted (key from ABA) and whitelisted, and a payee can only be an ABA account or
        merchant ID, never a card. User chose to keep payouts simulated (4.31's flow, unchanged).
        `5156 8399 3770 6777` couldn't be saved as a payout card because it fails the Luhn check;
        it's now allowed by name in `_DEMO_PAYOUT_CARDS` (`routers/wallet.py`) and
        `DEMO_PAYOUT_CARDS` (`utils/card.ts`). Its `51` prefix makes it a Mastercard, so it saves
        and shows as "Mastercard •••• 6777". `ruff` + `oxlint` clean, `vue-tsc` unchanged (16).

---

## Cut list (only if time runs out)

- Settings Notifications/Privacy persistence (found 2026-09-11 during 4.23) — both tabs are
  local-only `ref()`s with no store or backend; toggles/selects reset on tab switch or reload
- Album/Wish CRUD (found 2026-09-11 during 4.20) — add/edit/delete endpoints + UI for
  `album_items`/`wish_items`, re-scoped to work for buyers (`user_id`) as well as Pals
  (`player_id`); today both tables are read-only, Pal-only, seed-data-populated
- Admin panel (1.15, 3.14)
- Earnings tracker — fall back to plain booking history (3.7)
- Subscriptions backend — fall back to the static mock page as-is (3.11)
- Estars leaderboard backend — fall back to the static mock ranking as-is (3.12)
