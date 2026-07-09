import random
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import unprocessable
from app.models.match import Match
from app.models.player import Player, PlayerPosition
from app.models.team import Team

# A match is 91 plays: one per minute from 0 to 90 inclusive.
MATCH_MINUTES = 91

# Time-decay ("fatigue") numerators: success chances fall as the minute rises,
# and a higher Physical slows the decay. Goalkeepers fatigue slower on purpose.
OUTFIELD_FATIGUE = 15
GOALKEEPER_FATIGUE = 5

# Roll ranges per stage. Movement stages (dribble/pass/tackle/save) roll 0–150;
# the shot rolls 0–100.
MOVE_ROLL_MAX = 150
SHOT_ROLL_MAX = 100

# Position selection weights for each attacking/defending role (docs/match-
# simulation.md). A position absent from the XI simply drops out and the rest
# renormalize; the goalkeeper is never an outfield role, so it has no weight.
ATTACKING_WEIGHTS = {
    PlayerPosition.ATT: 60,
    PlayerPosition.MID: 30,
    PlayerPosition.DEF: 10,
}
PASSER_WEIGHTS = {
    PlayerPosition.MID: 60,
    PlayerPosition.DEF: 20,
    PlayerPosition.ATT: 20,
}
TACKLER_WEIGHTS = {
    PlayerPosition.DEF: 70,
    PlayerPosition.MID: 25,
    PlayerPosition.ATT: 5,
}

# Standard football points.
WIN_POINTS = 3
DRAW_POINTS = 1

# A valid lineup for simulation: exactly the starting XI, one of whom is a GK.
STARTERS_REQUIRED = 11

# Play types and outcome codes. These are stable, language-agnostic keys stored
# in the event log; the frontend resolves them to narrated copy.
PLAY_DRIBBLE = "dribble"
PLAY_PASS = "pass"
OUTCOME_GOAL = "goal"
OUTCOME_DRIBBLE_LOST = "dribbleLost"
OUTCOME_TACKLE_WON = "tackleWon"
OUTCOME_SHOT_WIDE = "shotWide"
OUTCOME_SAVED = "saved"
OUTCOME_PASS_INTERCEPTED = "passIntercepted"


def attacker_wins(roll: int, chance: float, max_roll: int) -> bool:
    """Attacker-side stage: the roll must strictly exceed the threshold.

    An exact tie counts as failure, so the defence benefits (docs/match-
    simulation.md, "Ties favor the defense").
    """
    return roll > max_roll - chance


def defender_wins(roll: int, chance: float, max_roll: int) -> bool:
    """Defender-side stage: an exact tie counts as success for the defence."""
    return roll >= max_roll - chance


class MatchSimulationService:
    """Computes a match result as 91 per-minute plays in a single pass.

    The RNG is injectable so tests are deterministic. Only each team's starting
    XI takes part; standings are updated once the score is settled.
    """

    def __init__(self, db: Session, *, rng: random.Random | None = None):
        self.db = db
        self._rng = rng or random.Random()

    def simulate(self, match: Match) -> Match:
        """Play out the match, persist the score, event log and standings."""
        home_starters = self._starters(match.homeTeamId)
        away_starters = self._starters(match.awayTeamId)
        self._require_valid_lineup(home_starters)
        self._require_valid_lineup(away_starters)

        home_score = 0
        away_score = 0
        events: list[dict] = []
        for minute in range(MATCH_MINUTES):
            home_attacks, play_type, scored, outcome, player = self._play_minute(
                minute, home_starters, away_starters
            )
            if scored and home_attacks:
                home_score += 1
            elif scored:
                away_score += 1
            events.append(
                {
                    "minute": minute,
                    "isHome": home_attacks,
                    "playType": play_type,
                    "outcome": outcome,
                    "player": player,
                    "homeScore": home_score,
                    "awayScore": away_score,
                }
            )

        match.homeScore = home_score
        match.awayScore = away_score
        match.played = True
        match.eventLog = events
        self._apply_standings(match, home_score, away_score)
        self.db.commit()
        self.db.refresh(match)
        return match

    def _play_minute(
        self, minute: int, home_starters: list[Player], away_starters: list[Player]
    ) -> tuple[bool, str, bool, str, str]:
        """Resolve one minute; returns (home_attacks, play_type, scored, outcome, player)."""
        home_attacks = self._coin()
        attackers, defenders = (
            (home_starters, away_starters)
            if home_attacks
            else (away_starters, home_starters)
        )
        if self._coin():
            scored, outcome, player = self._dribble_play(minute, attackers, defenders)
            return home_attacks, PLAY_DRIBBLE, scored, outcome, player
        scored, outcome, player = self._pass_play(minute, attackers, defenders)
        return home_attacks, PLAY_PASS, scored, outcome, player

    def _dribble_play(
        self, minute: int, attackers: list[Player], defenders: list[Player]
    ) -> tuple[bool, str, str]:
        dribbler = self._pick(attackers, ATTACKING_WEIGHTS)
        tackler = self._pick(defenders, TACKLER_WEIGHTS)
        keeper = self._goalkeeper(defenders)

        if not self._paced_success(dribbler, "dribbling", minute, OUTFIELD_FATIGUE):
            return False, OUTCOME_DRIBBLE_LOST, dribbler.name
        if self._tackle_wins(tackler, minute):
            return False, OUTCOME_TACKLE_WON, dribbler.name
        if not self._shot_on_target(dribbler, minute):
            return False, OUTCOME_SHOT_WIDE, dribbler.name
        if self._save_made(keeper, minute):
            return False, OUTCOME_SAVED, dribbler.name
        return True, OUTCOME_GOAL, dribbler.name

    def _pass_play(
        self, minute: int, attackers: list[Player], defenders: list[Player]
    ) -> tuple[bool, str, str]:
        passer = self._pick(attackers, PASSER_WEIGHTS)
        # The shooter receives the pass and must be a different player.
        shooter = self._pick(attackers, ATTACKING_WEIGHTS, exclude=passer)
        tackler = self._pick(defenders, TACKLER_WEIGHTS)
        keeper = self._goalkeeper(defenders)

        if not self._paced_success(passer, "passing", minute, OUTFIELD_FATIGUE):
            return False, OUTCOME_PASS_INTERCEPTED, passer.name
        if self._tackle_wins(tackler, minute):
            return False, OUTCOME_TACKLE_WON, shooter.name
        if not self._shot_on_target(shooter, minute):
            return False, OUTCOME_SHOT_WIDE, shooter.name
        if self._save_made(keeper, minute):
            return False, OUTCOME_SAVED, shooter.name
        return True, OUTCOME_GOAL, shooter.name

    def _paced_success(
        self, player: Player, attribute: str, minute: int, fatigue: int
    ) -> bool:
        """Attacker-side movement stage (dribble/pass): 0–150 roll."""
        chance = self._paced_chance(player, attribute, minute, fatigue)
        return attacker_wins(self._roll(MOVE_ROLL_MAX), chance, MOVE_ROLL_MAX)

    def _tackle_wins(self, tackler: Player, minute: int) -> bool:
        chance = self._paced_chance(tackler, "defending", minute, OUTFIELD_FATIGUE)
        return defender_wins(self._roll(MOVE_ROLL_MAX), chance, MOVE_ROLL_MAX)

    def _save_made(self, keeper: Player, minute: int) -> bool:
        chance = self._paced_chance(keeper, "defending", minute, GOALKEEPER_FATIGUE)
        return defender_wins(self._roll(MOVE_ROLL_MAX), chance, MOVE_ROLL_MAX)

    def _shot_on_target(self, shooter: Player, minute: int) -> bool:
        chance = shooter.shooting - OUTFIELD_FATIGUE * minute / shooter.physical
        return attacker_wins(self._roll(SHOT_ROLL_MAX), chance, SHOT_ROLL_MAX)

    def _paced_chance(
        self, player: Player, attribute: str, minute: int, fatigue: int
    ) -> float:
        return (
            getattr(player, attribute)
            + player.pace / 2
            - fatigue * minute / player.physical
        )

    def _pick(
        self,
        players: list[Player],
        weights: dict[PlayerPosition, int],
        *,
        exclude: Player | None = None,
    ) -> Player:
        """Pick a position by weight (present positions only), then uniformly."""
        pool = [p for p in players if p is not exclude and p.position in weights]
        positions = sorted({p.position for p in pool}, key=lambda pos: pos.value)
        chosen = self._rng.choices(
            positions, weights=[weights[pos] for pos in positions], k=1
        )[0]
        return self._rng.choice([p for p in pool if p.position == chosen])

    def _goalkeeper(self, players: list[Player]) -> Player:
        return next(p for p in players if p.position == PlayerPosition.GK)

    def _apply_standings(
        self, match: Match, home_score: int, away_score: int
    ) -> None:
        home = self.db.get(Team, match.homeTeamId)
        away = self.db.get(Team, match.awayTeamId)
        self._record_result(home, scored=home_score, conceded=away_score)
        self._record_result(away, scored=away_score, conceded=home_score)

    def _record_result(self, team: Team, *, scored: int, conceded: int) -> None:
        team.played += 1
        team.goalsFor += scored
        team.goalsAgainst += conceded
        if scored > conceded:
            team.wins += 1
            team.points += WIN_POINTS
        elif scored == conceded:
            team.draws += 1
            team.points += DRAW_POINTS
        else:
            team.losses += 1

    def _starters(self, team_id: uuid.UUID) -> list[Player]:
        return list(
            self.db.scalars(
                select(Player).where(
                    Player.teamId == team_id, Player.isStarter.is_(True)
                )
            ).all()
        )

    def _require_valid_lineup(self, starters: list[Player]) -> None:
        keepers = sum(1 for p in starters if p.position == PlayerPosition.GK)
        if len(starters) != STARTERS_REQUIRED or keepers != 1:
            raise unprocessable("match.lineupIncomplete")

    def _coin(self) -> bool:
        return self._rng.random() < 0.5

    def _roll(self, max_roll: int) -> int:
        return self._rng.randint(0, max_roll)
