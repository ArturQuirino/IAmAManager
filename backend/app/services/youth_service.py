import random
import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import conflict, not_found
from app.models.player import ATTRIBUTE_NAMES, Player, PlayerPosition
from app.models.team import Team
from app.models.youth_candidate import YouthCandidate
from app.services.player_generator import PlayerGenerator
from app.services.squad_service import MAX_SQUAD_SIZE

# The academy offers exactly one prospect per position every week — see
# docs/players.md.
YOUTH_POSITIONS = (
    PlayerPosition.GK,
    PlayerPosition.DEF,
    PlayerPosition.MID,
    PlayerPosition.ATT,
)


class YouthService:
    """The weekly youth academy: prospect generation and promotion.

    An injectable RNG keeps generation deterministic under test. The weekly
    refresh is currently manual (a later stage schedules it); until then
    `get_current` generates the first batch lazily so the page is usable.
    """

    def __init__(self, db: Session, *, rng: random.Random | None = None):
        self.db = db
        self._generator = PlayerGenerator(rng)

    def get_current(self, team: Team) -> list[YouthCandidate]:
        """This week's prospects, generating an initial batch on demand."""
        candidates = self._find_candidates(team)
        if not candidates:
            candidates = self._generate_week(team)
        return candidates

    def refresh_week(self, team: Team) -> list[YouthCandidate]:
        """Discard any prospects not promoted and generate a fresh batch.

        Un-added candidates are permanently lost on refresh (docs/players.md).
        """
        for candidate in self._find_candidates(team):
            self.db.delete(candidate)
        return self._generate_week(team)

    def add_to_squad(self, team: Team, candidate_id: uuid.UUID) -> Player:
        """Promote a prospect into the squad, unless the squad is at its cap.

        Filtering the candidate by the team's id enforces ownership (IDOR):
        another team's prospect is reported as not found.
        """
        candidate = self.db.scalar(
            select(YouthCandidate).where(
                YouthCandidate.id == candidate_id,
                YouthCandidate.teamId == team.id,
            )
        )
        if candidate is None:
            raise not_found("youth.candidateNotFound")
        if self._squad_size(team) >= MAX_SQUAD_SIZE:
            raise conflict("squad.full")

        player = self._to_player(team, candidate)
        self.db.add(player)
        self.db.delete(candidate)
        self.db.commit()
        self.db.refresh(player)
        return player

    def _find_candidates(self, team: Team) -> list[YouthCandidate]:
        return list(
            self.db.scalars(
                select(YouthCandidate)
                .where(YouthCandidate.teamId == team.id)
                .order_by(YouthCandidate.position)
            ).all()
        )

    def _generate_week(self, team: Team) -> list[YouthCandidate]:
        week_of = date.today()
        candidates = [
            self._new_candidate(team, position, week_of)
            for position in YOUTH_POSITIONS
        ]
        self.db.add_all(candidates)
        self.db.commit()
        for candidate in candidates:
            self.db.refresh(candidate)
        return candidates

    def _new_candidate(
        self, team: Team, position: PlayerPosition, week_of: date
    ) -> YouthCandidate:
        prototype = self._generator.random_player(position)
        attributes = {name: getattr(prototype, name) for name in ATTRIBUTE_NAMES}
        return YouthCandidate(
            name=prototype.name,
            position=position,
            weekOf=week_of,
            teamId=team.id,
            **attributes,
        )

    def _to_player(self, team: Team, candidate: YouthCandidate) -> Player:
        attributes = {name: getattr(candidate, name) for name in ATTRIBUTE_NAMES}
        return Player(
            name=candidate.name,
            position=candidate.position,
            isStarter=False,
            teamId=team.id,
            **attributes,
        )

    def _squad_size(self, team: Team) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(Player)
                .where(Player.teamId == team.id)
            )
            or 0
        )
