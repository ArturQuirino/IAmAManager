# Match Simulation

How a match's result is computed. This logic is adapted from a prior prototype (a separate local repository, `RealManager`) where it was already implemented end-to-end, and is carried over here as the intended design for this game's match engine. See [Players and squad — Player entity](./players.md#player-entity) for the attribute model this simulation depends on.

## Rules

### Match structure

- A match is simulated as a sequence of **91 discrete plays**, one for each minute from **0 to 90** (inclusive).
- The whole match is computed **synchronously in one pass** when triggered — it is not paced over real time. The per-minute breakdown exists so the result can be replayed/narrated minute-by-minute afterwards (a textual event log per minute), not so the user waits 90 real minutes.
- Only a team's **Starting XI** (see [Players and squad — Starting XI](./players.md#starting-xi)) takes part. Bench/reserve players have no effect on the match.

### Determining the attacking side and play type (per minute)

- For every minute, a 50/50 coin flip decides which of the two teams is attacking; the other team defends.
- For every minute, a separate 50/50 coin flip decides whether the play is a **Dribble play** or a **Pass play** (see below).

### Player roles and selection weights

Every play involves picking specific starters into roles. Which starter fills an attacking role is **weighted by position**, not fixed to a single position anymore:

- **Dribbler** (attacking team, only in a Dribble play — see below): drawn from the attacking team's starters, weighted **Attacker 60% / Midfielder 30% / Defender 10%**. This same player also takes the resulting shot.
- **Passer** (attacking team, only in a Pass play — see below): drawn from the attacking team's starters, weighted **Midfielder 60% / Defender 20% / Attacker 20%**.
- **Shooter** (attacking team, only in a Pass play): the player who receives the pass and shoots, drawn from the attacking team's starters, weighted **Attacker 60% / Midfielder 30% / Defender 10%** (same weights as the Dribbler role). **The Shooter must be a different player from the Passer** — if the weighted roll picks the same individual for both roles, the Shooter is re-rolled (excluding the Passer) until a different player is selected.
- **Tackler:** drawn from the defending team's starters, weighted **Defender 70% / Midfielder 25% / Attacker 5%**.
- **Goalkeeper:** the defending team's starter playing Goalkeeper. Unchanged.

Within a chosen position, the specific starter is picked uniformly at random (e.g. if Midfielder is rolled for the Passer role and the team has 3 starting midfielders, each has an equal chance).

### Ties favor the defense

Every stage below compares a random roll against a threshold derived from a "success chance." **On an exact tie, the defending side of that stage wins:**

- **Dribble, Pass, Shot** — the roll represents the *attacker's* (or passer's) chance to succeed. A tie means **failure** (dribble lost / pass intercepted / shot off target) — the defense benefits.
- **Tackle, Save** — the roll represents the *defender's*/*goalkeeper's* chance to succeed. A tie means **success** (tackle won / save made) — the defense benefits.

### Play type 1 — Dribble play

Funnel of four sequential checks; a failure at any stage ends the play immediately (no goal) and skips the remaining stages:

1. **Dribble** — the Dribbler tries to get past the defense.
   - Success chance = `Dribbling + Pace / 2 − 15 × minute / Physical` (Dribbler's own attributes).
   - Roll: a random number from 0–150 must exceed `150 − chance`.
   - Failure → Dribbler loses the ball, play ends.
2. **Tackle** — the Tackler tries to win the ball back.
   - Success chance = `Defending + Pace / 2 − 15 × minute / Physical` (Tackler's own attributes).
   - Same 0–150 roll mechanic.
   - Success → Tackler wins the ball, play ends (no goal).
3. **Shot** — the Dribbler shoots.
   - On-target chance = `Shooting − 15 × minute / Physical` (Dribbler's own attributes).
   - Roll: a random number from 0–100 must exceed `100 − chance`.
   - Failure → shot goes wide, play ends.
4. **Save** — the Goalkeeper tries to save.
   - Save chance = `Defending + Pace / 2 − 5 × minute / Physical` (Goalkeeper's own attributes). The fatigue term intentionally uses `5` here instead of `15` — goalkeepers are meant to fatigue slower than outfield players.
   - Same 0–150 roll mechanic.
   - Success → Goalkeeper saves, play ends (no goal).
   - Failure → **goal** for the attacking side.

### Play type 2 — Pass play

Same funnel shape, but the attacking side involves two different players — a Passer and a Shooter — instead of one:

1. **Pass** — the Passer tries to find the Shooter.
   - Success chance = `Passing + Pace / 2 − 15 × minute / Physical` (Passer's own attributes) — same formula shape as the Dribble stage, using `Passing` instead of `Dribbling`.
   - Roll: a random number from 0–150 must exceed `150 − chance`.
   - Failure → pass is lost/intercepted, play ends.
2. **Tackle** — the Tackler tries to stop the Shooter (the pass's receiver) before they can shoot.
   - Success chance = `Defending + Pace / 2 − 15 × minute / Physical` (Tackler's own attributes). Same formula as the Dribble play's tackle stage.
   - Success → Tackler wins the ball, play ends (no goal).
3. **Shot** — the Shooter shoots.
   - On-target chance = `Shooting − 15 × minute / Physical` (Shooter's own attributes). Same formula as the Dribble play's shot stage.
   - Failure → shot goes wide, play ends.
4. **Save** — the Goalkeeper tries to save. Identical to the Dribble play's save stage.
   - Failure → **goal** for the attacking side.

All success-chance formulas include a time-decay ("fatigue") term: success chance drops as the match minute increases, and a higher `Physical` slows that decay.

### Result and standings

- The match's final score is the cumulative goals across all 91 plays.
- Once a match finishes, [Competition](./competition.md) standings are updated: goals for/against, goal difference, matches played, win/draw/loss, and points (see [Competition — Points system](./competition.md#points-system)).
- **Tie-break for standings: points, then goal difference.**

## Status

Not yet implemented in this codebase. This document describes the intended design, carried over from the reference prototype.

## Open questions

- None currently.
