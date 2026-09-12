# Competition

The game has one main championship, organized into **divisions** (tiers). Every team belongs to exactly one division at a time.

## Rules

### Divisions

- Each division has exactly **10 teams**.
- **The number of divisions is unbounded.** The pyramid grows on demand: whenever the current lowest division becomes full of 10 **real** (user-owned) teams and another new user signs up, a **new lowest division is created** for that team, initially filled with **9 fake teams** to complete it (see [Placeholder ("fake") teams](#placeholder-fake-teams)).

### Standings, promotion and relegation

At the end of a season, within each division:

- The **1st placed** team is the **champion of the division**.
- The **1st and 2nd placed** teams are **promoted** to the division above — unless they are already in the top (first) division.
- The **9th and 10th placed** (last and second-to-last) teams are **relegated** to the division below — **except in the lowest division, which has no relegation** (there is no division below it to relegate to).

### Season structure

- A season is played at a rate of **one match per day, in real time**: every real calendar day at **18:00** by default, that day's round is simulated across every division. The time and scheduler activation are configurable through `MATCHDAY_HOUR`, `MATCHDAY_MINUTE`, and `SCHEDULER_ENABLED`.
- Each team plays every other team in its division **twice** — one home leg and one away leg (double round-robin).
- With 10 teams per division, that is 9 opponents × 2 legs = **18 matches per season** per team, i.e. **18 real calendar days** per season.

### Points system

- Standard football points: **win = 3, draw = 1, loss = 0**.

### Tie-break

- Standings are ranked by **points, then goal difference**.

### Match results

- Results are produced by the [match simulation](./match-simulation.md), not entered manually.

### New team placement

- A newly created team (see [Users and teams](./users-and-teams.md)) always starts in the **lowest division**.

### Placeholder ("fake") teams

- The lowest division must always have exactly 10 teams. When there aren't enough real (user-owned) teams to fill it, the remaining slots are filled with **fake teams**: no owning user, and a squad randomly generated with a **deliberately very low skill average** — just enough to not leave the slot empty, not meant to be competitive.
- When a new user signs up:
  - If the current lowest division has a fake team slot available, the new team **replaces a fake team's slot** in that division.
  - If the current lowest division is already full of 10 real teams, a **new lowest division is created**, seeded with the new user's team plus **9 fake teams**.
  - Either way, the user's team **inherits the fake team's current standing** for the season in progress (points, wins/draws/losses, results already played).
  - The user's team gets its **own newly, randomly generated squad** — it does **not** inherit the fake team's (weak) players.
- Fake teams exist purely as placeholders to keep every division always full; they are replaced by real teams as users join.

## Status

Implemented:

- Division, team, match, and game-clock persistence, with Alembic migrations.
- Dynamic division creation and replacement of the lowest-ranked fake team when a user registers.
- Deterministic double round-robin scheduling using the circle method: 18 rounds and 90 matches for a 10-team division.
- Standings, match-result updates, and deterministic ordering by points, goal difference, goals scored, team name, and id.
- Pyramid-wide season completion, promotion/relegation, standings reset, season-number increment, and generation of the next fixture list.
- Idempotent daily matchday processing across all divisions. In development, authenticated users can trigger it through `POST /dev/run-matchday`; this endpoint is not mounted in production.

Operational caveat: the in-process scheduler is implemented, but the separate cloud job entrypoints referenced by the deployment configuration are not yet available. See `deploy/README.md`.

## Open questions

- None currently.
