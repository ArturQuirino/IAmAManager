# Users and Teams

## Rules

- A **user** is uniquely identified by **email**. Emails must be unique across the system.
- Each user has exactly **one team**, identified by `teamName`. There is no concept of multiple teams per user, or of a team without an owning user.
- A user's password is **always stored hashed** (bcrypt). Plain-text passwords are never persisted, logged, or returned by the API.
- **When a new user signs up, a new team is automatically created for them**, populated with a **randomly generated squad of players**. The user does not build their initial squad manually.
- See [Competition](./competition.md#new-team-placement) for the rule on which division a new team starts in.

## Status

Implemented: unique email, bcrypt password hashing, one team per user (`teamName` on `User`).

Not yet implemented:
- Public self-registration endpoint (users are currently provisioned via the seed script only).
- Automatic team + random squad creation on signup.
- Endpoint to update team name, email, or password.

## Open questions

- What determines the "randomness" of the initial squad — fixed squad size? Distribution across positions? Overall range? (See [Players and squad](./players.md#open-questions).)
