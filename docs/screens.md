# Screens

The main screens of the application, and what each is responsible for. This is a product/scope map, not a UI spec — layout and visual design are not covered here.

## Rules

### Login

- Email + password only.
- Out of scope for now: account creation (sign-up), password recovery. See [Users and teams](./users-and-teams.md) and [Authentication and access](./authentication.md).

### Home

- Landing screen after login. Not yet designed (see [Open questions](#open-questions)).

### Tactics

- Lets the user set the **starting XI**, the **bench (reserves)**, and the team's **formation**.
- See [Players and squad — Starting XI](./players.md#starting-xi).

### League table

- Shows the standings of the division the user's team currently belongs to.
- See [Competition — Standings, promotion and relegation](./competition.md#standings-promotion-and-relegation).

### Squad

- Lists every player in the user's squad, with a **detail view per player**.
- Where the user manages the squad, e.g. removing players. See [Players and squad](./players.md).

### Matches

- Shows the list of matches for the user's team (fixtures and/or results).
- See [Competition — Season structure](./competition.md#season-structure) and [Match simulation](./match-simulation.md) for how a result is produced.

### Youth academy

- Where the user views the current week's 4 generated youth players and decides whether to add each one to the squad.
- See [Players and squad — Youth academy](./players.md#youth-academy).

## Status

Not yet implemented: all screens above (no frontend routes for tactics, league table, squad detail, matches, or youth academy exist yet beyond the current login and read-only "my team" pages).

## Open questions

- Home screen: what does it actually show (e.g. next match, latest results, notifications)? Not yet designed.
- Squad screen vs. Tactics screen boundary: squad screen manages the roster (view/remove/detail); Tactics screen manages starters/bench/formation from within that roster. Confirm this split is correct.
- Matches screen: does it show only the user's team's matches, or the full division calendar/results for all 10 teams?
- Player detail view: which attributes/info are shown per player beyond the fields already in the model (name, position, shirt number, age, nationality, overall)?
