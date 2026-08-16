# SquadUp / Gaming Companion Platform — Project Recap
**Skilled Player Matchmaking for Gamers**

---

## 1. Project Identity

| Field | Detail |
|---|---|
| System type | Gaming companion / Epal matchmaking platform |
| Concept | Users pay skilled players to play games with them (e.g. League of Legends, Valorant, MLBB) |
| Example use case | "I don't want trash teammates — I'll pay a skilled player to carry/play with me" |
| Type | Freelance project — helping a classmate, getting paid |
| Your role | Developer building the website |
| Deadline | Target week 10-11 of your 90-day window |

---

## 2. Stack — Original vs Recommended

> **Original concept note used Next.js + Node.js + Express — completely different from your Niyay stack. Changed to match your stack to eliminate context switching.**

| Component | Original | Recommended | Reason |
|---|---|---|---|
| Frontend | Next.js (React) | Vue.js + Vite | Your existing stack — no context switch |
| CSS | Tailwind CSS | Tailwind CSS | Keep — universal, works with Vue |
| Backend | Node.js + Express | Python (FastAPI) | Your existing stack |
| Realtime | Socket.IO | Supabase Realtime | Already in your stack, no extra library |
| Matching algorithm | JavaScript/TypeScript | Python in FastAPI | Same backend language |
| Hosting | Vercel | Docker + same setup as Niyay | Consistent with your other projects |
| Database | Supabase | Supabase | Keep — no change |

---

## 3. Core Features

| Feature | Description |
|---|---|
| Player Profiles | Skilled players create profiles listing: games they play, rank/skill level, role/position, price per hour, availability schedule, languages spoken, bio. Players verified through rank screenshots. |
| Browse & Filter Players | Users browse available players filtered by: game (LoL, Valorant, MLBB, etc.), rank, role, price range, availability, language. Card-based layout with ratings. |
| Booking / Session Request | User selects a player, chooses session duration, sends a request. Player accepts or declines. Confirmed bookings show in both dashboards. |
| Live Messaging | Real-time chat between user and booked player via Supabase Realtime. Coordinate game details, friend requests, server/region info before playing. |
| Payment via KHQR | User pays player via Bakong KHQR after booking is confirmed. MVP: manual verification. Money goes to player's bank account. Platform commission tracked separately. |
| Rating & Reviews | After a session, user rates the player (1-5 stars) and leaves a review. Helps build trust and quality control. |
| Player Dashboard | Skilled players manage: profile, availability, incoming booking requests, session history, earnings tracker. |
| Matching Algorithm | Weighted compatibility scoring — see Section 4. Simple Python math, NOT complex ML. |

---

## 4. Matching Algorithm — Simplified

The matching algorithm sounds impressive in the concept note but is really just a scoring function:

| Criteria | Points | Logic |
|---|---|---|
| Game match | 40 pts | Player plays the same game as user |
| Rank compatibility | 30 pts | Player's rank is within 1-2 tiers of user's rank (or higher) |
| Role match | 20 pts | Player plays the role/position user needs |
| Availability | 10 pts | Player is available at user's requested time |

Returns sorted list of players by total score. Highest score shown first. That's it — no ML needed.

```python
def match_score(player, user_request):
    score = 0
    if player.game == user_request.game: score += 40
    if rank_compatible(player.rank, user_request.rank): score += 30
    if player.role == user_request.role: score += 20
    if availability_overlap(player.availability, user_request.time): score += 10
    return score

# Sort all players by score, return top results
ranked_players = sorted(players, key=lambda p: match_score(p, request), reverse=True)
```

---

## 5. Deployment of Technology

| Component | Technology |
|---|---|
| Frontend | Vue.js + Vite |
| CSS | Tailwind CSS |
| Backend | Python (FastAPI) |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth |
| Realtime / Chat | Supabase Realtime |
| File Storage | Supabase Storage (player avatars, rank screenshots) |
| Payment | KHQR (Bakong) |
| Containerization | Docker + Docker Compose |
| Version Control | Git + GitHub |

---

## 6. Payment Flow — Important Detail

This platform has a more complex payment situation than PawMart:

- User pays for a session → money should go to the **PLAYER**, not the platform owner
- Platform optionally takes a % commission cut (e.g. 10-15%)
- **MVP:** user pays player's KHQR directly, platform commission tracked manually
- **Post-launch:** implement proper escrow — user pays platform, platform pays player after session completion

> For submission, the MVP approach (direct KHQR to player) is acceptable. Flag the commission/escrow as a future enhancement in the report.

---

## 7. App Pages

| Page | Route | Notes |
|---|---|---|
| Landing | / | Hero + how it works + featured players + games supported |
| Browse Players | /players | Filter/search all available players |
| Player Profile | /players/:id | Individual player page + booking button |
| Booking | /book/:playerId | Select duration, time, send request |
| Checkout | /checkout/:bookingId | KHQR payment for booking |
| Messages | /messages | Chat with booked players via Supabase Realtime |
| My Bookings | /bookings | User's booking history and status |
| Login / Signup | /login, /signup | Supabase Auth |
| Player Dashboard | /dashboard/player | Player manages profile, availability, bookings, earnings |
| User Dashboard | /dashboard/user | User's session history, reviews left, spending |
| Become a Player | /become-player | Registration flow for skilled players to join |
| Settings | /settings | Account settings |
| Admin | /admin | Platform-level oversight — flagged players, disputes |

---

## 8. User Types

| User Type | What they do |
|---|---|
| Regular user | Browse players, book sessions, pay, leave reviews |
| Skilled player (SquadUp) | Create profile, set availability and price, accept bookings, earn money |
| Admin | Manage platform — verify players, handle disputes, view analytics |

---

## 9. Development Approach

| Item | Decision |
|---|---|
| Stack | Identical to Niyay: Vue + FastAPI + Supabase + Tailwind — zero context switching |
| Boilerplate reuse | Auth, Docker, Supabase connection, KHQR — copy from Niyay and PawMart |
| Most custom part | Matching algorithm (Python, simple scoring) + player booking flow |
| Realtime chat | Supabase Realtime channels — simpler than Socket.IO, already in stack |
| Estimated time | 10-14 days of focused work with AI assistance |
| When to build | Week 10-11 of your 90-day plan |
| Scope lock | Get classmate to confirm exact feature list before starting — no additions after |

---

## 10. Scope Warning

> This is the most complex of the 3 freelance projects. Two user types (user + player) means double the pages and flows. The realtime chat adds complexity. Keep scope tight.

### Minimum viable version for submission:
- Player profiles ✅
- Browse + filter players ✅
- Booking request flow ✅
- KHQR payment ✅
- Basic messaging ✅
- Rating system ✅

### Cut if time is short:
- Advanced matching algorithm (just show all players, no scoring)
- Earnings tracker (show booking history instead)
- Admin panel (skip entirely if needed)
