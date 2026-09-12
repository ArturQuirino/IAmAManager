# Screens

The main screens of the application, and what each is responsible for. This is a product/scope map, not a UI spec — layout and visual design are not covered here.

## Rules

### Login

- Email + password only.
- Links to public account registration. Password recovery remains out of scope. See [Users and teams](./users-and-teams.md) and [Authentication and access](./authentication.md).

### Registration

- Collects email, password, and team name.
- Creates the manager account, team, initial squad, and division placement, then signs the user in.

### Home

- Landing screen after login, showing the next fixture, current league position/division/season, and recent results.

### Team

- Shows the team name, division, season, record, goals, points, and squad size.
- Lets the manager rename the team.

### Tactics

- Lets the user set the **starting XI**, the **bench (reserves)**, and the team's **formation**.
- See [Players and squad — Starting XI](./players.md#starting-xi).

### League table

- Shows the standings of the division the user's team currently belongs to.
- See [Competition — Standings, promotion and relegation](./competition.md#standings-promotion-and-relegation).

### Squad

- Lists every player in the user's squad with attributes shown inline.
- Lets the manager remove players while respecting minimum squad composition. There is currently no separate player-detail route.

### Matches

- Shows fixtures and results for the user's team, with match details and the minute-by-minute event log.
- The current UI can request simulation of an eligible match directly.
- See [Competition — Season structure](./competition.md#season-structure) and [Match simulation](./match-simulation.md) for how a result is produced.

### Youth academy

- Where the user views the current week's 4 generated youth players and decides whether to add each one to the squad.
- See [Players and squad — Youth academy](./players.md#youth-academy).

## Status

Implemented: login, registration, home, team, squad, tactics, matches, league table, youth academy, shared authenticated navigation, logout, and locale selection. All user-facing copy is available in Portuguese, English, and Spanish.

## Open questions

- Should direct, user-triggered match simulation remain available outside development, or should production rely exclusively on the scheduled matchday?
- Should the matches screen remain scoped to the user's team or eventually expose the full division calendar?
- Is a dedicated player-detail view needed beyond the attributes currently shown inline on the squad and tactics screens?
