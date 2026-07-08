# Players and Squad

## Rules

### Player entity

- A **player** always belongs to exactly one team, and is never shared between teams.
- **Positions.** Initially, a player can be one of four broad positions:
  - Goalkeeper
  - Defender
  - Midfielder
  - Attacker
- **Attributes.** Each player has six core attributes, each an integer from **1 to 100**:
  - Pace
  - Shooting
  - Passing
  - Dribbling
  - Defending
  - Physical
  - `overall` is **not an independent value** — it is **derived as the average of the six attributes above** (rounded to the nearest integer).
- **Not needed for now:** `age` and `nationality` are deferred to a future iteration (not part of the current player model). `shirtNumber` is not needed at all — dropped as a business rule concern.
- A user can only view and act on **their own** squad. Players are always filtered by the authenticated user's id — a user can never read or act on another user's players.
- New players are created as part of a team's automatic, random generation (see [Users and teams](./users-and-teams.md)), the youth academy (below), or via the seed process — there is no manual "create arbitrary player" flow.

### Random player generation

- A randomly generated player gets each of the six attributes (Pace, Shooting, Passing, Dribbling, Defending, Physical) drawn **uniformly between 1 and 100**; `overall` is then computed as their average.
- Position, when not specified by the caller, is chosen **uniformly at random** among the four positions.
- This is the same generation used for a new team's initial squad and for each of the youth academy's weekly players (each generated for a specific, required position — see [Youth academy](#youth-academy)).
- Reference for a full random team's shape (adapted from a prior prototype, see [Open questions](#open-questions)): starters fixed as **1 goalkeeper, 4 defenders, 3 midfielders, 3 attackers** (a 4-3-3 shape), plus additional bench players generated with random positions to fill out the rest of the squad.

### Youth academy

- Once a week, each team's **youth academy page** is refreshed with **4 new randomly generated players — one per position** (goalkeeper, defender, midfielder, attacker).
- The user chooses whether to **add each youth player to their squad or not**. It is not automatic.
- **Any youth player not added before the next weekly refresh is permanently lost.** When the refresh happens, unselected youth players are removed from the game entirely (not just from the youth page).
- A youth player **cannot be added if the squad is already at the 40-player maximum** — the user must release a player first.

### Squad size limits

- **Minimum:** at least **1 goalkeeper** and **10 outfield players** (defenders + midfielders + attackers combined).
- **Maximum:** a squad may have **at most 40 players** in total.

### Removing players from the squad

- A user can remove players from their own squad, subject to the **minimum squad composition** above (at least 1 goalkeeper, at least 10 outfield players).
- A removal that would break either minimum is not allowed.

### Starting XI

- On the Tactics screen (see [Screens](./screens.md#tactics)), the user selects their **11 starters** and the rest of the squad becomes bench (reserves).
- The starting XI must have **exactly one goalkeeper** and **10 outfield players in any mix** of defender/midfielder/attacker (no minimum per outfield position). No fixed named formations (4-3-3, 4-4-2, etc.) are required — this rule stands on its own (see [Match simulation](./match-simulation.md#player-roles-and-selection-weights)).

## Status

Implemented: `Player` model with `name`, `position`, `shirtNumber`, `age`, `nationality`, `overall`, owned by a user (`userId`); read-only "my team" endpoint. Note: `shirtNumber` is no longer a business requirement (can be dropped), and `age`/`nationality` are deferred to a future iteration — the current fields are ahead of, and partly diverge from, the rules below.

Not yet implemented:
- The simplified 4-position model described above. **Note:** the current `PlayerPosition` enum in code (`backend/app/models/player.py`) has 10 granular positions (`GK`, `CB`, `LB`, `RB`, `CDM`, `CM`, `CAM`, `LW`, `RW`, `ST`) — this needs to be reconciled with the 4-position rule (either the enum is simplified, or the 4 positions are a display/grouping concept layered on top of the granular enum).
- The six-attribute model and derived `overall` (currently `overall` is a stored, independent field).
- Squad management endpoints (add/remove player, select starting XI).
- Random player/squad generation logic.
- Youth academy (weekly refresh, generation, add-to-squad flow).

## Open questions

- How does the current 10-position enum reconcile with the 4-position rule (goalkeeper/defender/midfielder/attacker)?
