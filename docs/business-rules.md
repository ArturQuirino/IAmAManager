# General Business Rules

This is the index for the business rules of **I Am a Manager**, a football manager simulator. Rules are organized by scope into the files below. As new scopes come up, add a new file here and link it.

Scope note: each document reflects the rules **as currently understood/designed**, and marks explicitly what is **implemented** vs. **not yet implemented** in the codebase. Open questions/gaps are tracked in an "Open questions" section at the bottom of each file — move an item out once it's resolved.

---

## Scopes

- [Users and teams](./users-and-teams.md) — user/team ownership, account creation, team assignment.
- [Players and squad](./players.md) — positions, attributes, squad composition.
- [Competition](./competition.md) — divisions, promotion/relegation, season structure, fixtures.
- [Match simulation](./match-simulation.md) — how a match's result is computed, minute by minute.
- [Authentication and access](./authentication.md) — login, sessions, authorization model.
- [Screens](./screens.md) — main application screens and what each is responsible for.

## Cross-cutting

- **Localization:** all user-facing messages (API errors, UI text) are in **Portuguese**. Code, identifiers, and documentation (including these files) are in **English**.
