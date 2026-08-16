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

---

## Status

- **Current phase:** Phase 1 — Frontend Pages (static UI, mock data only)
- **Next task:** 1.6e Become a Player — Review & submit step
- **Last updated:** 2026-08-17

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
- [ ] 1.4 Browse Players (`/players`) — card grid, filters (game, rank, role, price, availability, language)
- [ ] 1.5 Player Profile (`/players/:id`) — profile details, reviews list, "Book" CTA
- [ ] 1.6 Become a Player (`/become-player`) — 5-step "Pal Application" wizard, built per the mockups in `squadup_ui/ONBOARDING/` (folder name is a misnomer — this is the only signup-adjacent flow in the design; there's no separate base-profile onboarding). After signup, a modal ("Just looking for a player" / "Become a Pal") routes here or to Browse Players — see `PostSignupRoleModal.vue`. Split into sub-tasks, one screen at a time:
  - [x] 1.6a Account — avatar, display name, email, phone, region, timezone, password, terms checkbox (`ACCOUNT.jpg`)
  - [x] 1.6b Games & skills — game(s), rank, role (`GAMES.jpg`)
  - [x] 1.6c Rates & availability — pricing, schedule (`RATES.jpg`)
  - [x] 1.6d Verify & payout — ID upload, Squad Coin payout setup (`VERIFY.jpg`)
  - [ ] 1.6e Review & submit — final summary before submitting (`REVIEW.jpg`)
  - [ ] 1.6f Success — confirmation screen after submit (`SUCCESS.jpg`)
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

- Admin panel (1.12, 3.8)
- Earnings tracker — fall back to plain booking history (3.7)
- Matching algorithm — fall back to unsorted player list (3.3)
