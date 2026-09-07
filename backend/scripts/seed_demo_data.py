"""Seed demo Pals (and a lighter slice of buyers/bookings/reviews) into the real, linked
Supabase project (CHECKPOINT.md 3.17). Unlike the throwaway users created/deleted by each
Phase 3/4 live smoke test, these rows are meant to stay: they give Browse Players/Player
Profile/Checkout real, bookable listings instead of the client-side-only `mocks/players.ts`
fixtures (`p1`..`p8`), which have no backing `players`/`services` row and can't be booked for
real (see the `isRealId` guard added to `stores/bookings.ts`).

Covers every game in `frontend/src/data/games.ts` that has a rank ladder (~30 titles, ranked
games get priority coverage) plus a curated set of popular non-ranked/co-op games (each
guaranteed 2-5 dedicated services, per 2026-09-05 request) so no game filter on Browse Players
comes back empty. Each Pal gets one primary service (their main game, with a rank badge for
ranked games) plus a random chance of 1-2 extra services (a second game, or a companion service
like Coaching/Voice Call/Watch Together) to land the total service count comfortably above the
Pal count.

Every seeded `auth.users` row uses a placeholder `@SEED_EMAIL_DOMAIN` address - `.test` is an
IANA-reserved TLD that never resolves, so these accounts are guaranteed non-deliverable and
never meant to log in, just to exist as FK targets (same role `on_auth_user_created`
normally fills for a real Google signup). That shared domain is also the marker `teardown`
uses to find and remove every seeded row again - `players`/`services`/`bookings`/`reviews`/
`wallet_transactions` all cascade from `auth.users` (see `account_deletion_cascade.sql`), so
deleting the auth row is enough.

Idempotency (3.17c): `seed` refuses to run if any seed accounts already exist, rather than
trying to merge into them - run `teardown` first to reseed from scratch.

Run from `backend/` (Settings' `.env` resolves relative to CWD):
    uv run python scripts/seed_demo_data.py seed [--pals 120] [--buyers 40]
    uv run python scripts/seed_demo_data.py teardown
"""

import argparse
import random
import re
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException

from backend.core.config import get_settings
from backend.core.supabase import get_supabase_client
from backend.core.wallet import adjust_coin_balance
from backend.routers.bookings import _generate_order_number
from backend.routers.reviews import _recompute_after_review, _sentiment_for

SEED_EMAIL_DOMAIN = "squadup-seed.test"

# Ranked games ------------------------------------------------------------------------------
# Rank ladders copied verbatim from `frontend/src/data/games.ts`'s `gameRanks` so the badge a
# seeded Pal shows matches the ladder the rest of the app knows about. Roles are genre-flavored
# (lane/role for team shooters & MOBAs, archetypes for fighting/card games, classes for
# sports/racing/RTS) - purely descriptive text, not enforced anywhere.
RANKED_GAMES: dict[str, tuple[list[str], list[str] | None]] = {
    "Valorant": (
        ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal", "Radiant"],
        ["Duelist", "Controller", "Initiator", "Sentinel"],
    ),
    "League of Legends": (
        ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Emerald", "Diamond", "Master", "Grandmaster", "Challenger"],
        ["Top", "Jungle", "Mid", "ADC", "Support"],
    ),
    "Dota 2": (
        ["Herald", "Guardian", "Crusader", "Archon", "Legend", "Ancient", "Divine", "Immortal"],
        ["Carry", "Mid", "Offlane", "Support", "Hard Support"],
    ),
    "Apex Legends": (
        ["Rookie", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Predator"],
        ["Fragger", "Support", "Recon"],
    ),
    "Rocket League": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Champion", "Grand Champion", "Supersonic Legend"],
        ["Striker", "Midfielder", "Goalkeeper"],
    ),
    "Counter-Strike 2": (
        ["Silver", "Gold Nova", "Master Guardian", "Legendary Eagle", "Supreme", "Global Elite"],
        ["Entry Fragger", "AWPer", "IGL", "Support", "Lurker"],
    ),
    "Overwatch 2": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster", "Champion"],
        ["Tank", "Damage", "Support"],
    ),
    "Rainbow Six Siege": (
        ["Copper", "Bronze", "Silver", "Gold", "Platinum", "Emerald", "Diamond", "Champion"],
        ["Entry Fragger", "Anchor", "Support", "Flex"],
    ),
    "Call of Duty: Warzone": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Crimson", "Iridescent", "Top 250"],
        ["Slayer", "Support", "IGL", "Sniper"],
    ),
    "Street Fighter 6": (
        ["Rookie", "Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grand Master"],
        ["Rushdown", "Zoner", "Grappler", "All-Rounder"],
    ),
    "Guilty Gear Strive": (
        ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Vanquisher"],
        ["Rushdown", "Zoner", "Grappler", "All-Rounder"],
    ),
    "Mortal Kombat 1": (
        ["Apprentice", "Kombatant", "Warrior", "Champion", "Master", "Grand Master", "Demi God", "God", "Elder God"],
        ["Rushdown", "Zoner", "Grappler", "All-Rounder"],
    ),
    "PUBG: Battlegrounds": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster"],
        ["Assaulter", "Sniper", "Support", "IGL"],
    ),
    "PUBG Mobile": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Crown", "Ace", "Conqueror"],
        ["Assaulter", "Sniper", "Support", "IGL"],
    ),
    "Hearthstone": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Legend"],
        ["Aggro", "Control", "Midrange", "Combo"],
    ),
    "Teamfight Tactics": (
        ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Emerald", "Diamond", "Master", "Grandmaster", "Challenger"],
        ["Reroll", "Fast 8", "Standard"],
    ),
    "Legends of Runeterra": (
        ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master"],
        ["Aggro", "Control", "Midrange", "Combo"],
    ),
    "Marvel Snap": (
        [
            "Recruit", "Agent", "Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond",
            "Vibranium", "Omega", "Galactic", "Infinite",
        ],
        ["Aggro", "Control", "Midrange", "Combo"],
    ),
    "NBA 2K25": (
        ["Rookie", "Pro", "All-Star", "Superstar", "Elite"],
        ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"],
    ),
    "Gran Turismo 7": (
        ["E", "D", "C", "B", "A", "S"],
        ["Sprint Racer", "Endurance Racer", "Drift Specialist"],
    ),
    "iRacing": (
        ["Rookie", "D", "C", "B", "A", "Pro", "Pro/World Class"],
        ["Sprint Racer", "Endurance Racer", "Drift Specialist"],
    ),
    "StarCraft II": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster"],
        ["Terran", "Protoss", "Zerg"],
    ),
    "Age of Empires IV": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Conqueror"],
        ["Rush", "Boom", "Turtle", "Fast Castle"],
    ),
    "Clash Royale": (
        ["Bronze", "Silver", "Gold", "Legendary"],
        ["Aggro", "Control", "Midrange", "Combo"],
    ),
    "The Finals": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ruby"],
        ["Light", "Medium", "Heavy"],
    ),
    "Mobile Legends: Bang Bang": (
        ["Warrior", "Elite", "Master", "Grandmaster", "Epic", "Legend", "Mythic", "Mythical Glory"],
        ["Roamer", "Gold Laner", "EXP Laner", "Jungler", "Mid Laner"],
    ),
    "Smite": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Masters", "Grandmaster"],
        ["Solo", "Jungle", "Mid", "Support", "Carry"],
    ),
    "Heroes of the Storm": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster"],
        ["Tank", "Bruiser", "Ranged Assassin", "Melee Assassin", "Healer", "Support"],
    ),
    "EA Sports FC 24": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Elite"],
        ["Striker", "Midfielder", "Defender", "Goalkeeper"],
    ),
    "EA Sports FC 25": (
        ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Elite"],
        ["Striker", "Midfielder", "Defender", "Goalkeeper"],
    ),
    "Brawl Stars": (
        ["Bronze", "Silver", "Gold", "Diamond", "Mythic", "Legendary", "Masters", "Pro"],
        ["Aggro", "Support", "Sniper", "Tank"],
    ),
}

# Games shown on the landing page's "Browse by game" rail that also have a rank ladder - get
# extra weight so those never come up short (2026-09-05: "priority to rank games").
FEATURED_RANKED = {
    "Valorant", "Counter-Strike 2", "Apex Legends", "Overwatch 2", "League of Legends", "Dota 2",
    "Rocket League", "Rainbow Six Siege", "Call of Duty: Warzone", "PUBG: Battlegrounds",
    "StarCraft II", "Mobile Legends: Bang Bang", "Brawl Stars", "EA Sports FC 25",
}

# Non-ranked games ---------------------------------------------------------------------------
# No competitive rank ladder in `games.ts`, so these Pals show no rank badge - but every game
# here is guaranteed 2-5 dedicated services (2026-09-05 request) via `_build_game_plan` below.
# Classes are filled in only where the game actually has a recognizable one; otherwise `None`.
NON_RANKED_GAMES: dict[str, list[str] | None] = {
    "Fortnite": None,
    "Genshin Impact": None,
    "Minecraft": None,
    "Palworld": None,
    "Sea of Thieves": None,
    "Destiny 2": ["Titan", "Hunter", "Warlock"],
    "Warframe": None,
    "Lost Ark": None,
    "New World": None,
    "Escape from Tarkov": None,
    "Baldur's Gate 3": ["Fighter", "Wizard", "Rogue", "Cleric", "Druid"],
    "It Takes Two": None,
    "Diablo IV": ["Barbarian", "Sorcerer", "Druid", "Necromancer", "Rogue"],
    "World of Warcraft": ["Tank", "Healer", "DPS"],
    "Deep Rock Galactic": ["Driller", "Engineer", "Gunner", "Scout"],
    "Elden Ring": None,
    "Monster Hunter World": None,
    "Honor of Kings": ["Roamer", "Jungler", "Mid Laner", "Farmer", "Support"],
    "Halo Infinite": ["Slayer", "Support", "Objective"],
    "Left 4 Dead 2": None,
}

ALL_GAME_NAMES = list(RANKED_GAMES) + list(NON_RANKED_GAMES)

# Every remaining title in `frontend/src/data/games.ts`'s `gameNames` (mostly single-player/
# narrative games with no duo/rank angle) - `expand` covers each of these at least once via a
# "generalist" Pal per `_seed_cluster_pal` rather than tacking them onto an already-themed
# competitive Pal (2026-09-06: "every single game" should have coverage, keeping ranked games
# the heavier focus). Order is the source file's own (loosely alphabetical/franchise-grouped),
# chunked into small clusters so a generalist Pal's game list still reads as a plausible person's
# backlog rather than a random dump.
LONG_TAIL_GAMES = [
    "Alan Wake", "Assassin's Creed", "Among Us", "Age of Empires", "Assassin's Creed Odyssey",
    "Ashen", "Ark: Survival Evolved", "Astroneer", "A Plague Tale: Innocence",
    "Batman: Arkham City", "BioShock", "Borderlands", "Battlefield 4", "Baldur's Gate II",
    "Bloodborne", "Bayonetta 3", "Black Myth: Wukong", "Brothers: A Tale of Two Sons",
    "Celeste", "Cyberpunk 2077", "Control", "Crusader Kings III", "Cuphead", "Civilization VI",
    "Cities: Skylines", "Chained Echoes", "Cult of the Lamb", "Crash Bandicoot 4",
    "Dark Souls", "Death Stranding", "Doom Eternal", "Dead Cells", "Divinity: Original Sin 2",
    "Dishonored 2", "Disco Elysium", "Days Gone", "Dying Light 2",
    "Europa Universalis IV", "Enter the Gungeon", "Ender Lilies", "Everspace 2",
    "Fallout 4", "FTL: Faster Than Light", "Far Cry 6", "Forza Horizon 5", "Fable",
    "Firewatch", "Fire Emblem Engage", "Frostpunk 2", "Football Manager 2024",
    "God of War", "Grand Theft Auto V", "Ghost of Tsushima", "Guild Wars 2", "Gris",
    "Gears 5", "Griftlands", "Grounded", "Gunfire Reborn", "Granblue Fantasy Versus Rising",
    "Hades", "Hollow Knight", "Hearts of Iron IV", "Half-Life 2", "Hi-Fi Rush", "Hitman 3",
    "Horizon Forbidden West", "Human Fall Flat", "Hogwarts Legacy",
    "Inside", "Into the Breach", "Ikaruga", "Ittle Dew", "Immortals Fenyx Rising",
    "Insurgency: Sandstorm", "Inscryption", "Icarus", "Iron Harvest",
    "Journey", "Just Cause 4", "Jusant", "Jotun", "Jump King", "Jedi: Survivor", "John Wick Hex",
    "Kingdom Come: Deliverance", "Kena: Bridge of Spirits", "Katana ZERO",
    "Kerbal Space Program", "Killer Instinct", "Kingdom Hearts III", "Kirby and the Forgotten Land",
    "Lies of P", "Loop Hero", "Lethal Company", "Little Nightmares II",
    "Lego Star Wars: The Skywalker Saga",
    "Mass Effect Legendary Edition", "Metro Exodus", "Mortal Kombat 11", "Mortal Shell",
    "Monster Train", "Metal Gear Solid V", "My Time at Portia",
    "NieR: Automata", "No Man's Sky", "Need for Speed Heat", "Noita", "Nioh 2", "Neon White",
    "Nine Sols",
    "Outer Wilds", "Ori and the Blind Forest", "Outriders", "Owlboy",
    "Ori and the Will of the Wisps", "Ooblets", "Old World",
    "Persona 5 Royal", "Portal 2", "Path of Exile", "Prey", "Plague Tale: Requiem",
    "Pizza Tower", "Planet Coaster", "Prison Architect",
    "Quake II", "Quantum Break", "Quern: Undying Thoughts", "Quasimorph",
    "Red Dead Redemption 2", "Resident Evil 4", "Rimworld", "Returnal", "Remnant II",
    "Risk of Rain 2", "Ready or Not",
    "Slay the Spire", "Stardew Valley", "Starfield", "Sekiro: Shadows Die Twice",
    "Streets of Rage 4", "Subnautica", "Skul: The Hero Slayer", "Spider-Man 2",
    "Splitgate 2",
    "The Witcher 3", "Terraria", "Tekken 8", "Titanfall 2", "Total War: Warhammer III",
    "The Last of Us Part II", "Total War: Three Kingdoms", "Tunic", "Tiny Tina's Wonderlands",
    "Undertale", "Untitled Goose Game", "Unravel Two", "Until Dawn", "Uncharted 4",
    "Ultrakill", "Unpacking",
    "Valheim", "Vampire Survivors", "Vermintide 2", "Viewfinder", "Vampyr", "Void Bastards",
    "Wo Long: Fallen Dynasty", "Witchfire", "Wolfenstein II", "Wasteland 3", "Wuthering Waves",
    "Xenoblade Chronicles 3", "XCOM 2", "X4: Foundations", "Xuan-Yuan Sword VII",
    "Yakuza 0", "Yooka-Laylee", "Yakuza: Like a Dragon",
    "Zelda: Breath of the Wild", "Zenless Zone Zero", "Zomboid", "Zero Escape",
]

CLUSTER_TAGLINES = [
    "I bounce between games depending on the mood, come hang out",
    "Not a one-game kind of Pal, ask what's cracked open tonight",
    "Backlog's huge, always down for something different",
    "Casual sessions, no pressure, just good company",
    "Jack of all trades, come pick the game",
]
CLUSTER_SERVICE_TEMPLATES = [
    "Co-op & chill sessions",
    "Full clears and boss carries",
    "Casual playthrough company",
    "Speedrun & challenge runs",
]
CLUSTER_SESSION_LINES = [
    "No pressure, just good company along the way.",
    "Happy to vibe and play, first playthrough or fiftieth.",
    "Great background chat while we get through it together.",
    "Let's see how far we get, no rush.",
    "I'll bring snack breaks and bad jokes.",
]

WHATS_INCLUDED_TEAM = [
    "Live voice comms the whole session",
    "Positioning & call-out tips as we play",
]
WHATS_INCLUDED_CASUAL = [
    "Friendly, low-pressure sessions",
    "Happy to go at your pace",
]

# Handle/display-name generation --------------------------------------------------------------
# Mixes a few Discord-like naming conventions (camel-case tags, dotted/underscored handles,
# plain first-name-style handles, the occasional "xX...Xx"/"itz" tryhard tag) so the roster
# reads like a real player list rather than one templated pattern repeated 120 times.

PREFIXES = [
    "Shadow", "Velvet", "Mythic", "Frost", "Gold", "Sentinel", "Crimson", "Silent", "Iron", "Astral",
    "Neon", "Rapid", "Solar", "Lunar", "Blaze", "Void", "Storm", "Phantom", "Nova", "Rogue",
    "Echo", "Titan", "Arc", "Cobalt", "Ember", "Glacier", "Onyx", "Vortex", "Toxic", "Crypt",
    "Static", "Grim", "Feral", "Azure", "Obsidian", "Prism", "Sable", "Wraith", "Havoc", "Jade",
]
SUFFIXES = [
    "Strike", "Ace", "Roamer", "Jungler", "Blade", "Queen", "Titan", "Rookie", "Fang", "Reaper",
    "Sniper", "Guardian", "Wraith", "Falcon", "Hunter", "Viper", "Knight", "Ghost", "Striker", "Legend",
    "Wolf", "Phoenix", "Drift", "Surge", "Nomad", "Rider", "Flux", "Specter", "Rune", "Howl",
]
NAME_WORDS = [
    "kai", "mira", "jun", "zeke", "noa", "ren", "talia", "dex", "yara", "milo",
    "sana", "theo", "nova", "ezra", "kira", "finn", "luca", "mina", "arlo", "juno",
    "remy", "nash", "ivy", "cole", "zane", "lyra", "kane", "asha", "rhys", "toma",
]


def _clean_handle(raw: str) -> str:
    return re.sub(r"[^a-z0-9._]", "", raw.lower()) or "pal"


def _gen_identity(used_handles: set[str]) -> tuple[str, str]:
    """Returns `(display_name, handle_local_part)` in one of several naming styles, retrying on
    collision since `players.handle` is unique."""
    for _ in range(50):
        prefix = random.choice(PREFIXES)
        suffix = random.choice(SUFFIXES)
        word = random.choice(NAME_WORDS)
        style = random.random()

        if style < 0.28:
            display, handle = f"{prefix}{suffix}", f"{prefix}{suffix}"
        elif style < 0.45:
            display, handle = f"{prefix} {suffix}", f"{prefix}.{suffix}"
        elif style < 0.60:
            n = random.randint(1, 99)
            display, handle = f"{word.capitalize()}{n}", f"{word}{n}"
        elif style < 0.74:
            n = random.randint(1, 99)
            display, handle = f"{prefix}{suffix}", f"{prefix}_{suffix}{n}"
        elif style < 0.85:
            display, handle = f"itz{suffix}", f"itz{suffix}"
        elif style < 0.93:
            display, handle = f"xX{prefix}{suffix}Xx", f"xx_{prefix}{suffix}_xx"
        else:
            display, handle = f"{word.capitalize()}.gg", f"{word}.gg"

        handle = _clean_handle(handle)
        if handle not in used_handles:
            used_handles.add(handle)
            return display, handle

    # Exhausted retries (astronomically unlikely at this scale) - force uniqueness.
    n = random.randint(1000, 9999)
    display, handle = f"{prefix}{suffix}{n}", _clean_handle(f"{prefix}{suffix}{n}")
    used_handles.add(handle)
    return display, handle


TAGLINES = [
    "I'm the duo your friends warned about",
    "Roll the dice, no bad rolls with me",
    "Don't be shy, let's play!",
    "Wanna get carried by me? Let's go!!",
    "Your new favorite gaming buddy",
    "Val with me, or add me to VC",
    "I only play ranked in NA",
    "Come talk with me?",
    "Chill vibes, clutch plays",
    "Climbing the ladder one game at a time",
    "Bring your A-game, I'll bring the carry",
    "Duo queue therapy sessions available",
]

REVIEW_TEXTS = [
    "Carried so hard, climbed a whole rank this week.",
    "Great callouts and super chill to play with.",
    "Showed up on time and actually knew the meta.",
    "Would book again, made ranked fun instead of stressful.",
    "Patient with me even when I threw a few games.",
    "Solid comms, good vibes, clean mechanics.",
]

# Companion services a Pal can offer alongside their main game - same archetypes as the
# authored `p1`/`self` mock profiles (`frontend/src/mocks/playerProfiles.ts`).
COMPANION_SERVICES = [
    {"name": "Coaching Session", "unit": "/hour", "price_range": (700, 1300), "styles": ["Fundamentals", "Macro Play"]},
    {"name": "Voice Call", "unit": "/session", "price_range": (200, 450), "styles": ["Laid Back"]},
    {"name": "Watch Together", "unit": "/session", "price_range": (200, 500), "styles": ["Laid Back"]},
    {"name": "E-Chat", "unit": "/15min", "price_range": (0, 0), "styles": ["Laid Back"]},
]

LANGUAGES = ["English", "Khmer", "Vietnamese", "Tagalog", "Indonesian", "Chinese", "Korean"]
TIMEZONES = ["GMT+07:00", "GMT+08:00", "GMT+09:00", "GMT+06:30"]

BUYER_FIRST_NAMES = [
    "Alex", "Jordan", "Sam", "Maya", "Leo", "Nadia", "Kai", "Priya", "Ethan", "Sofia",
    "Marcus", "Lena", "Ravi", "Chloe", "Omar", "Tess",
]
BUYER_LAST_INITIALS = list("ABCDEFGHJKLMNPRSTW")


def _random_past_iso(max_days: int) -> str:
    delta = timedelta(days=random.randint(0, max_days), hours=random.randint(0, 23), minutes=random.randint(0, 59))
    return (datetime.now(UTC) - delta).isoformat()


def _create_seed_user(client, email: str, display_name: str) -> str:
    result = client.auth.admin.create_user(
        {"email": email, "email_confirm": True, "user_metadata": {"full_name": display_name}}
    )
    return result.user.id


def _list_seed_users(client) -> list:
    users = []
    page = 1
    while True:
        batch = client.auth.admin.list_users(page=page, per_page=200)
        if not batch:
            break
        users.extend(u for u in batch if u.email and u.email.endswith(f"@{SEED_EMAIL_DOMAIN}"))
        if len(batch) < 200:
            break
        page += 1
    return users


# Game planning -----------------------------------------------------------------------------


def _build_game_plan(n_pals: int) -> list[str]:
    """Assigns each of `n_pals` a primary game. Every game gets a baseline allocation first (2-3
    for non-ranked games, per the 2026-09-05 "at least 2-5 services" request; 1-2 for niche ranked
    games; 3-5 for the ones featured on the landing page's "Browse by game" rail) so nothing comes
    up empty, then the total is trimmed down to `n_pals` by shaving the biggest allocations first
    (never below each game's floor) or padded out with extra ranked-weighted picks if there's
    still room - keeping ranked games the larger share overall, as requested."""
    counts: dict[str, int] = {}
    for game in NON_RANKED_GAMES:
        counts[game] = random.randint(3, 4) if game == "Fortnite" else random.randint(2, 3)
    for game in RANKED_GAMES:
        counts[game] = random.randint(3, 5) if game in FEATURED_RANKED else random.randint(1, 2)

    floor = {g: (2 if g in NON_RANKED_GAMES else 1) for g in counts}

    total = sum(counts.values())
    while total > n_pals:
        above_floor = [g for g, n in counts.items() if n > floor[g]]
        if not above_floor:
            break
        g = max(above_floor, key=lambda g: counts[g])
        counts[g] -= 1
        total -= 1

    if total < n_pals:
        ranked_names = list(RANKED_GAMES)
        weights = [5 if g in FEATURED_RANKED else 2 for g in ranked_names]
        for g in random.choices(ranked_names, weights=weights, k=n_pals - total):
            counts[g] += 1

    plan = [game for game, n in counts.items() for _ in range(n)]
    random.shuffle(plan)
    return plan[:n_pals]


# Service helpers -----------------------------------------------------------------------------


def _insert_service(
    client,
    player_id: str,
    *,
    name: str,
    description: str,
    styles: list[str],
    platforms: list[str],
    whats_included: list[str],
    price: int,
    price_unit: str,
    served_count: int,
) -> str:
    service_id = str(uuid4())
    client.table("services").insert(
        {
            "id": service_id,
            "player_id": player_id,
            "name": name,
            "description": description,
            "styles": styles,
            "platforms": platforms,
            "whats_included": whats_included,
            "avg_response_time": random.choice(["5-10 mins", "10-15 mins", "10-20 mins"]),
            "served_count": served_count,
        }
    ).execute()

    client.table("service_pricing_options").insert(
        {"service_id": service_id, "label": f"Standard {price_unit}", "price_coins": price, "price_unit": price_unit, "sort_order": 0}
    ).execute()

    if price == 0 or random.random() < 0.4:
        if price == 0 or random.random() < 0.5:
            client.table("service_promotions").insert(
                {"service_id": service_id, "label": "1st Order Free", "discount_type": "first_order_free"}
            ).execute()
        else:
            pct = random.choice([10, 15, 20])
            client.table("service_promotions").insert(
                {"service_id": service_id, "label": f"{pct}% Off", "discount_type": "percent_off", "discount_value": pct}
            ).execute()

    return service_id


def _game_price(game: str, rank: str | None) -> int:
    if rank is not None:
        ranks = RANKED_GAMES[game][0]
        rank_index = ranks.index(rank)
        return max(150, 250 + rank_index * 80 + random.randint(-40, 90))
    return random.randint(200, 700)


def _seed_game_service(client, player_id: str, game: str, rank: str | None, role: str | None) -> tuple[str, int]:
    price = _game_price(game, rank)
    flavor = " ".join(part for part in (rank, role) if part)
    description = f"{flavor + ' on ' if flavor else ''}{game}. {random.choice(TAGLINES)}" if flavor else f"{game} sessions. {random.choice(TAGLINES)}"
    service_id = _insert_service(
        client,
        player_id,
        name=game,
        description=description,
        styles=[role] if role else [],
        platforms=[game],
        whats_included=WHATS_INCLUDED_TEAM if rank is not None else WHATS_INCLUDED_CASUAL,
        price=price,
        price_unit="/Game",
        served_count=random.randint(0, 400),
    )
    return service_id, price


def _seed_companion_service(client, player_id: str, primary_game: str) -> None:
    template = random.choice(COMPANION_SERVICES)
    low, high = template["price_range"]
    price = random.randint(low, high) if high > low else low
    description, whats_included = {
        "Coaching Session": (
            f"One-on-one VOD review and fundamentals for {primary_game}.",
            ["1-hour live VOD review", "Notes tailored to your rank"],
        ),
        "Voice Call": (
            "Just here to chat and keep you company between matches.",
            ["1-on-1 voice call", "Laid back, no pressure vibes"],
        ),
        "Watch Together": (
            f"Pro matches, streams, or just {primary_game}. Let's watch it together.",
            ["Synced watch session", "Live commentary and reactions"],
        ),
        "E-Chat": (
            "Voice call and chill, no game required.",
            ["Live voice chat for 15 minutes", "1st order free for new buyers"],
        ),
    }[template["name"]]
    _insert_service(
        client,
        player_id,
        name=template["name"],
        description=description,
        styles=template["styles"],
        platforms=[primary_game, "SquadUp"],
        whats_included=whats_included,
        price=price,
        price_unit=template["unit"],
        served_count=random.randint(0, 150),
    )


def _seed_extra_services(client, player_id: str, primary_game: str, current_games: list[str]) -> None:
    n_extra = random.choices([0, 1, 2], weights=[25, 55, 20])[0]
    games = list(current_games)
    for _ in range(n_extra):
        if random.random() < 0.55:
            _seed_companion_service(client, player_id, primary_game)
            continue

        candidates = [g for g in ALL_GAME_NAMES if g != primary_game]
        game = random.choice(candidates)
        if game in RANKED_GAMES:
            ranks, roles = RANKED_GAMES[game]
            rank = random.choice(ranks)
            role = random.choice(roles) if roles else None
        else:
            rank = None
            role_list = NON_RANKED_GAMES[game]
            role = random.choice(role_list) if role_list else None
        _seed_game_service(client, player_id, game, rank, role)
        if game not in games:
            games.append(game)

    if games != current_games:
        client.table("players").update({"games": games}).eq("id", player_id).execute()


# Seeding -----------------------------------------------------------------------------------


def _seed_pal(client, email_local: str, game: str, used_handles: set[str]) -> dict:
    if game in RANKED_GAMES:
        ranks, roles = RANKED_GAMES[game]
        rank = random.choice(ranks)
        role = random.choice(roles) if roles else None
    else:
        rank = None
        role_list = NON_RANKED_GAMES[game]
        role = random.choice(role_list) if role_list else None

    display_name, handle_local = _gen_identity(used_handles)
    email = f"{email_local}@{SEED_EMAIL_DOMAIN}"
    user_id = _create_seed_user(client, email, display_name)
    client.table("users").update({"handle": f"@{handle_local}"}).eq("id", user_id).execute()

    player_id = str(uuid4())
    client.table("players").insert(
        {
            "id": player_id,
            "user_id": user_id,
            "display_name": display_name,
            "tagline": random.choice(TAGLINES),
            "timezone": random.choice(TIMEZONES),
            "language": random.choice(LANGUAGES),
            "tier": f"Pal {random.randint(1, 5)}",
            "games": [game],
            "rank": rank,
            "role": role,
            "languages": random.sample(LANGUAGES, k=random.randint(1, 2)),
            "price_per_hour": None,
            "online": random.random() < 0.55,
            "is_new": True,
            "payout_schedule": random.choice(["weekly", "bi_weekly", "monthly"]),
        }
    ).execute()

    service_id, price = _seed_game_service(client, player_id, game, rank, role)
    client.table("players").update({"highlighted_service_id": service_id, "price_per_hour": round(price / 2, 2)}).eq(
        "id", player_id
    ).execute()

    _seed_extra_services(client, player_id, game, [game])

    return {
        "user_id": user_id,
        "player_id": player_id,
        "service_id": service_id,
        "service_name": game,
        "display_name": display_name,
        "price": price,
    }


def _seed_cluster_pal(client, email_local: str, games: list[str], used_handles: set[str]) -> None:
    """A "generalist" Pal covering a small cluster of `LONG_TAIL_GAMES` (mostly single-player
    titles with no rank/role angle) - one service per game, all in the same casual/companion
    style rather than the competitive duo framing `_seed_pal` uses for ranked games."""
    display_name, handle_local = _gen_identity(used_handles)
    email = f"{email_local}@{SEED_EMAIL_DOMAIN}"
    user_id = _create_seed_user(client, email, display_name)
    client.table("users").update({"handle": f"@{handle_local}"}).eq("id", user_id).execute()

    player_id = str(uuid4())
    client.table("players").insert(
        {
            "id": player_id,
            "user_id": user_id,
            "display_name": display_name,
            "tagline": random.choice(CLUSTER_TAGLINES),
            "timezone": random.choice(TIMEZONES),
            "language": random.choice(LANGUAGES),
            "tier": f"Pal {random.randint(1, 3)}",
            "games": games,
            "rank": None,
            "role": None,
            "languages": random.sample(LANGUAGES, k=random.randint(1, 2)),
            "price_per_hour": None,
            "online": random.random() < 0.5,
            "is_new": True,
            "payout_schedule": random.choice(["weekly", "bi_weekly", "monthly"]),
        }
    ).execute()

    highlighted_service_id = None
    last_price = 0
    for game in games:
        price = random.randint(150, 500)
        service_id = _insert_service(
            client,
            player_id,
            name=game,
            description=f"{random.choice(CLUSTER_SERVICE_TEMPLATES)} for {game}. {random.choice(CLUSTER_SESSION_LINES)}",
            styles=[],
            platforms=[game],
            whats_included=WHATS_INCLUDED_CASUAL,
            price=price,
            price_unit="/Game",
            served_count=random.randint(0, 100),
        )
        highlighted_service_id = highlighted_service_id or service_id
        last_price = price

    client.table("players").update(
        {"highlighted_service_id": highlighted_service_id, "price_per_hour": round(last_price / 2, 2)}
    ).eq("id", player_id).execute()


def _seed_buyer(client, index: int) -> dict:
    display_name = f"{random.choice(BUYER_FIRST_NAMES)} {random.choice(BUYER_LAST_INITIALS)}."
    email = f"buyer{index:03d}@{SEED_EMAIL_DOMAIN}"
    user_id = _create_seed_user(client, email, display_name)
    # Generous starting balance so the seeded completed bookings below always clear.
    client.table("users").update({"coin_balance": random.randint(3000, 8000)}).eq("id", user_id).execute()
    return {"user_id": user_id, "display_name": display_name}


def _seed_completed_booking(client, buyer: dict, pal: dict, commission_pct: float) -> None:
    booking_id = str(uuid4())
    order_number = _generate_order_number(client)
    price = pal["price"]
    created_at = _random_past_iso(max_days=75)
    commission_coins = round(price * commission_pct / 100)

    client.table("bookings").insert(
        {
            "id": booking_id,
            "order_number": order_number,
            "player_id": pal["player_id"],
            "service_id": pal["service_id"],
            "user_id": buyer["user_id"],
            "status": "completed",
            "service_type_label": "Standard /Game",
            "price_coins": price,
            "price_unit": "/Game",
            "quantity": 1,
            "subtotal_coins": price,
            "total_coins": price,
            "commission_pct": commission_pct,
            "commission_coins": commission_coins,
            "created_at": created_at,
        }
    ).execute()

    try:
        adjust_coin_balance(
            client, buyer["user_id"], -price, kind="order", label="Order", detail=pal["service_name"], booking_id=booking_id
        )
        adjust_coin_balance(
            client, pal["user_id"], price, kind="order", label="Order", detail=pal["service_name"], booking_id=booking_id
        )
    except HTTPException as exc:
        print(f"    (skipped wallet ledger for {order_number}: {exc.detail})")

    if random.random() < 0.85:
        rating = random.choices([5, 4, 3], weights=[65, 25, 10])[0]
        client.table("reviews").insert(
            {
                "id": str(uuid4()),
                "service_id": pal["service_id"],
                "booking_id": booking_id,
                "author_id": buyer["user_id"],
                "rating": rating,
                "text": random.choice(REVIEW_TEXTS),
                "sentiment": _sentiment_for(rating),
                "created_at": created_at,
            }
        ).execute()
        _recompute_after_review(client, pal["service_id"], pal["player_id"])


def _seed_pending_booking(client, buyer: dict, pal: dict) -> None:
    booking_id = str(uuid4())
    order_number = _generate_order_number(client)
    price = pal["price"]

    client.table("bookings").insert(
        {
            "id": booking_id,
            "order_number": order_number,
            "player_id": pal["player_id"],
            "service_id": pal["service_id"],
            "user_id": buyer["user_id"],
            "status": "pending",
            "service_type_label": "Standard /Game",
            "price_coins": price,
            "price_unit": "/Game",
            "quantity": 1,
            "subtotal_coins": price,
            "total_coins": price,
        }
    ).execute()

    try:
        adjust_coin_balance(
            client, buyer["user_id"], -price, kind="order", label="Order", detail=pal["service_name"], booking_id=booking_id
        )
    except HTTPException as exc:
        print(f"    (skipped wallet ledger for {order_number}: {exc.detail})")


def seed(client, n_pals: int, n_buyers: int) -> None:
    existing = _list_seed_users(client)
    if existing:
        print(f"Found {len(existing)} existing seed accounts under @{SEED_EMAIL_DOMAIN}.")
        print("Run `teardown` first, then reseed from scratch.")
        sys.exit(1)

    commission_pct = get_settings().platform_commission_pct

    print(f"Creating {n_pals} Pals across {len(ALL_GAME_NAMES)} games...")
    used_handles: set[str] = set()
    game_plan = _build_game_plan(n_pals)
    pals = []
    for i, game in enumerate(game_plan):
        pal = _seed_pal(client, f"pal{i:03d}", game, used_handles)
        pals.append(pal)
        if (i + 1) % 20 == 0:
            print(f"  ...{i + 1}/{n_pals}")

    services_count = client.table("services").select("id", count="exact").execute().count
    print(f"Created {len(pals)} Pals, {services_count} services total.")

    print(f"Creating {n_buyers} buyers...")
    buyers = [_seed_buyer(client, i) for i in range(n_buyers)]

    print("Seeding booking/review history for a subset of Pals...")
    for pal in pals:
        if random.random() >= 0.5:
            continue
        client.table("players").update({"is_new": False}).eq("id", pal["player_id"]).execute()
        for _ in range(random.randint(1, 3)):
            _seed_completed_booking(client, random.choice(buyers), pal, commission_pct)
        if random.random() < 0.3:
            _seed_pending_booking(client, random.choice(buyers), pal)

    print(f"Done. Seeded {len(pals)} Pals and {len(buyers)} buyers under @{SEED_EMAIL_DOMAIN}.")


def teardown(client) -> None:
    users = _list_seed_users(client)
    if not users:
        print("No seed accounts found.")
        return
    for user in users:
        client.auth.admin.delete_user(user.id)
        print(f"  deleted {user.email}")
    print(f"Deleted {len(users)} seed accounts (cascades removed their players/services/bookings/reviews/wallet rows).")


# Targets for `expand`'s ranked-game top-up (2026-09-06: "moderate" boost - featured ranked
# games land around 10 services, the rest around 6, on top of whatever `seed` already created).
EXPAND_FEATURED_TARGET = 10
EXPAND_RANKED_TARGET = 6


def expand(client) -> None:
    """Run after `seed`: tops up every ranked game toward a healthier service count and adds one
    "generalist" Pal per 4-game cluster of `LONG_TAIL_GAMES` so every game in `games.ts` has at
    least one real listing, without touching the Pals `seed` already created."""
    existing = _list_seed_users(client)
    if not existing:
        print("No existing seed accounts found - run `seed` first.")
        sys.exit(1)

    used_handles = {
        u["handle"].lstrip("@") for u in client.table("users").select("handle").execute().data if u["handle"]
    }

    counts = Counter(s["name"] for s in client.table("services").select("name").execute().data)
    ranked_plan: list[str] = []
    for game in RANKED_GAMES:
        target = EXPAND_FEATURED_TARGET if game in FEATURED_RANKED else EXPAND_RANKED_TARGET
        ranked_plan.extend([game] * max(0, target - counts.get(game, 0)))
    random.shuffle(ranked_plan)

    print(f"Boosting ranked games with {len(ranked_plan)} more Pals...")
    for i, game in enumerate(ranked_plan):
        _seed_pal(client, f"ex{i:04d}", game, used_handles)
        if (i + 1) % 20 == 0:
            print(f"  ...{i + 1}/{len(ranked_plan)}")

    clusters = [LONG_TAIL_GAMES[i : i + 4] for i in range(0, len(LONG_TAIL_GAMES), 4)]
    print(f"Covering {len(LONG_TAIL_GAMES)} long-tail games via {len(clusters)} generalist Pals...")
    for i, cluster in enumerate(clusters):
        _seed_cluster_pal(client, f"gen{i:04d}", cluster, used_handles)
        if (i + 1) % 10 == 0:
            print(f"  ...{i + 1}/{len(clusters)}")

    print(f"Done. Added {len(ranked_plan)} ranked Pals and {len(clusters)} generalist Pals.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_parser = subparsers.add_parser("seed", help="Create demo Pals/buyers/bookings")
    seed_parser.add_argument("--pals", type=int, default=24)
    seed_parser.add_argument("--buyers", type=int, default=12)

    subparsers.add_parser("teardown", help="Delete every seeded account")
    subparsers.add_parser("expand", help="Boost ranked games and cover every other game.ts title")

    args = parser.parse_args()
    client = get_supabase_client()

    if args.command == "seed":
        seed(client, args.pals, args.buyers)
    elif args.command == "expand":
        expand(client)
    else:
        teardown(client)


if __name__ == "__main__":
    main()
