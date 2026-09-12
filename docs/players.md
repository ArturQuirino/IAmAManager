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

Implemented:

- Four-position `Player` model (`GK`, `DEF`, `MID`, `ATT`) with the six attributes above and a derived, non-persisted `overall`.
- Random player generation and an 18-player initial squad: a 4-3-3 starting XI plus 7 randomly positioned reserves.
- Authenticated squad listing and player removal, enforcing the minimum composition.
- Starting-XI selection with exactly 11 distinct players owned by the team and exactly one goalkeeper. Formation is derived dynamically as `DEF-MID-ATT`.
- Youth academy with four candidates, lazy initial generation, weekly replacement, ownership checks, and promotion into the squad up to the 40-player cap.

The weekly refresh is performed by the matchday cycle every seven successful game days. There is also a development-only manual matchday trigger.

## Open questions

- None currently.
