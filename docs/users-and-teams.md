# Users and Teams

## Rules

- A **user** is uniquely identified by **email**. Emails must be unique across the system.
- Each real user has exactly **one team**, identified by `teamName`. CPU-controlled placeholder teams have no owning user.
- A user's password is **always stored hashed** (bcrypt). Plain-text passwords are never persisted, logged, or returned by the API.
- **When a new user signs up, a new team is automatically created for them**, populated with a **randomly generated squad of players**. The user does not build their initial squad manually.
- See [Competition](./competition.md#new-team-placement) for the rule on which division a new team starts in.

## Status

Implemented:

- Public self-registration (`POST /auth/register`) with unique email validation.
- Automatic creation of a user-owned team, an 18-player random squad (4-3-3 starting XI plus 7 reserves), and placement in the lowest division.
- Immediate JWT issuance after registration.
- Team details and team-name update (`GET/PATCH /team`); team names are unique case-insensitively.

Not yet implemented: email change, password change/recovery, and account deletion.

## Open questions

- None currently.
