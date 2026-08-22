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
(ABA/KHQR/Stripe) is the last task in the project, after every other feature works
end-to-end.

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

---

## Status

- **Current phase:** Phase 1 — Frontend Pages (static UI, mock data only), complete
- **Next task:** Phase 2 — Backend Foundations, starting with 2.1
- **Last updated:** 2026-08-22

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

## Phase 2 — Backend Foundations

- [ ] 2.1 FastAPI app structure: routers per domain (players, bookings, messages, reviews, auth), `pydantic-settings` config, CORS for the Vite dev origin
- [ ] 2.2 Supabase connection (service-role client for backend, anon client pattern documented for frontend)
- [ ] 2.3 Database schema in Supabase: `users`, `players`, `bookings`, `messages`, `reviews` tables + relations
- [ ] 2.4 Supabase Storage buckets: player avatars, rank verification screenshots
- [ ] 2.5 Auth wiring: Supabase Auth end-to-end (signup/login/logout, session persistence, route guards on frontend)

## Phase 3 — Backend Features (wire real data into Phase 1 pages)

- [ ] 3.1 User profile CRUD + player profile CRUD + connect to Player Profile / Become a Player / Player Dashboard pages
- [ ] 3.2 Browse & filter endpoint + connect to Browse Players page
- [ ] 3.3 Matching algorithm (weighted scoring: game 40 / rank 30 / role 20 / availability 10) + apply as default sort on Browse Players
- [ ] 3.4 Booking request flow (create/accept/decline) + connect Booking / My Bookings / Player Dashboard
- [ ] 3.5 Realtime chat via Supabase Realtime + connect Messages page
- [ ] 3.6 Ratings & reviews endpoint + connect to Player Profile and User Dashboard
- [ ] 3.7 Player earnings tracker (derived from completed bookings) + connect to Player Dashboard
- [ ] 3.8 Admin endpoints: player verification, dispute handling (cut if short)
- [ ] 3.9 Docker + Docker Compose for frontend + backend (match Niyay/PawMart setup)

## Phase 4 — Payment: ABA / KHQR / Stripe (final task)

- [ ] 4.1 KHQR (Bakong) integration on Checkout — generate QR, MVP manual payment verification
- [ ] 4.2 ABA PayWay integration as alternate local payment method on Checkout
- [ ] 4.3 Stripe integration for international/card payments
- [ ] 4.4 Payment status → booking confirmation wiring (booking flips to confirmed once payment is verified)
- [ ] 4.5 Manual platform commission tracking (%, recorded per booking — no escrow yet)
- [ ] 4.6 Note in final report: proper escrow (user → platform → player) is a post-launch enhancement, not built for submission

---

## Cut list (only if time runs out)

- Admin panel (1.15, 3.8)
- Earnings tracker — fall back to plain booking history (3.7)
- Matching algorithm — fall back to unsorted player list (3.3)
