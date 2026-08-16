# SquadUp — Build Checkpoint

This file is the single source of truth for build progress. Work **one task at a time**:
pick the next unchecked box under "Next Up", implement it, check it off, then stop and
return here before starting the next one. Don't jump ahead or batch multiple tasks.

**Stack correction from the original recap:** no Tailwind CSS. UI is built with
**Element Plus** (+ `@phosphor-icons/vue` for icons), both already in
`frontend/package.json`.

**Brand colors:** primary `#059669`, background `#0F172A` — dark theme only (no
light/dark toggle). Wired as Element Plus CSS var overrides in
`frontend/src/styles/theme.css`.

**Order of operations:** Frontend UI first (static/mock data, no backend calls) →
Backend (FastAPI + Supabase) to wire everything for real → Payment integration
(ABA/KHQR/Stripe) is the last task in the project, after every other feature works
end-to-end.

---

## Status

- **Current phase:** Phase 1 — Frontend Pages (static UI, mock data only)
- **Next task:** 1.1 Landing (`/`)
- **Last updated:** 2026-08-16

---

## Phase 0 — Frontend Foundations

- [x] 0.1 Strip default Vite/Vue boilerplate (`HelloWorld`-style demo content, `stores/counter.ts`, sample router entry)
- [x] 0.2 Configure Element Plus (global or auto-import setup, default theme vars, confirm `@phosphor-icons/vue` as the icon set)
- [x] 0.3 Base layout shell: app header/navbar, footer, main content container, responsive breakpoints
- [x] 0.4 Register all page routes in `router/index.ts` as placeholder components (see full route table in Phase 1)
- [x] 0.5 Pinia store skeletons: `auth`, `players`, `bookings`, `messages`, `ui` (empty state shape only, no data fetching yet)
- [x] 0.6 Shared mock data fixtures (fake players, bookings, messages) to build UI against before backend exists

## Phase 1 — Frontend Pages (static UI, mock data only)

Build in this order — each one is a single task:

- [ ] 1.1 Landing (`/`) — hero, how it works, featured players, games supported
- [ ] 1.2 Login (`/login`) + Signup (`/signup`) — forms only, no real auth yet
- [ ] 1.3 Onboarding (`/onboarding`) — runs once right after first login/signup: create base profile (display name, avatar, preferred games, languages, short bio) before entering the app
- [ ] 1.4 Browse Players (`/players`) — card grid, filters (game, rank, role, price, availability, language)
- [ ] 1.5 Player Profile (`/players/:id`) — profile details, reviews list, "Book" CTA
- [ ] 1.6 Become a Player (`/become-player`) — registration flow (game, rank/screenshot upload UI, role, price, availability, bio)
- [ ] 1.7 Booking (`/book/:playerId`) — duration + time picker, request summary, submit
- [ ] 1.8 My Bookings (`/bookings`) — list with status (pending/accepted/declined/completed)
- [ ] 1.9 Messages (`/messages`) — chat UI shell (thread list + message pane), no realtime wiring yet
- [ ] 1.10 Player Dashboard (`/dashboard/player`) — profile mgmt, availability editor, incoming requests, session history, earnings view
- [ ] 1.11 User Dashboard (`/dashboard/user`) — session history, reviews left, spending summary
- [ ] 1.12 Settings (`/settings`) — account settings form
- [ ] 1.13 Admin (`/admin`) — flagged players, disputes list (cut this if time is short later)
- [ ] 1.14 Checkout (`/checkout/:bookingId`) — payment summary UI shell only (no live payment logic — that's Phase 4)

## Phase 2 — Backend Foundations

- [ ] 2.1 FastAPI app structure: routers per domain (players, bookings, messages, reviews, auth), `pydantic-settings` config, CORS for the Vite dev origin
- [ ] 2.2 Supabase connection (service-role client for backend, anon client pattern documented for frontend)
- [ ] 2.3 Database schema in Supabase: `users`, `players`, `bookings`, `messages`, `reviews` tables + relations
- [ ] 2.4 Supabase Storage buckets: player avatars, rank verification screenshots
- [ ] 2.5 Auth wiring: Supabase Auth end-to-end (signup/login/logout, session persistence, route guards on frontend — redirect to Onboarding if profile is incomplete)

## Phase 3 — Backend Features (wire real data into Phase 1 pages)

- [ ] 3.1 User profile creation (Onboarding) + player profile CRUD + connect to Onboarding / Player Profile / Become a Player / Player Dashboard pages
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

- Admin panel (1.12, 3.8)
- Earnings tracker — fall back to plain booking history (3.7)
- Matching algorithm — fall back to unsorted player list (3.3)
