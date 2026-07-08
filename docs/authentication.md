# Authentication and Access

## Rules

- Authentication is performed via **email + password** (`POST /auth/login`).
- On successful login, the API issues a **JWT access token**. The token encodes the user id (`sub`) and email, and expires after a configurable interval (`JWT_EXPIRES_IN`, default 7 days).
- Login failure (unknown email or wrong password) always returns the same generic error ("Credenciais inválidas") — the API never reveals whether the email exists, to avoid user enumeration.
- All endpoints that expose user-owned data require a valid access token (`Authorization: Bearer <token>`), except `POST /auth/login` and health checks.
- Every resource that belongs to a user (team, players, and any future owned resource) must be **filtered by the authenticated user's id**, derived from the JWT — never from a client-supplied `user_id`.
- There is no concept of roles/permissions yet (e.g. admin vs. manager). Every authenticated user has the same capabilities, scoped to their own team.

## Status

Implemented: login, JWT issuance, `get_current_user` dependency, IDOR-safe filtering on `players`.

Not yet implemented: token refresh, logout/server-side revocation, role-based access control.

## Open questions

- None currently.
