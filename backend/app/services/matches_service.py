import random
import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.exceptions import conflict, not_found
from app.models.match import Match
from app.models.team import Team
from app.services.match_simulation_service import MatchSimulationService


class MatchesService:
    """Reads a team's fixtures and triggers a manual simulation.

    Every lookup filters by the resolved team, so a match involving another
    team never resolves and is reported as not found (IDOR). The simulation
    engine itself is stateless about ownership; this service is the boundary.
    """

    def __init__(self, db: Session):
        self.db = db

    def list_for_team(self, team: Team) -> list[Match]:
        """The team's fixtures (home or away), ordered by round."""
        return list(
            self.db.scalars(
                select(Match)
                .where(self._involves(team))
                .order_by(Match.round.asc(), Match.id.asc())
            ).all()
        )

    def get_for_team(self, team: Team, match_id: uuid.UUID) -> Match:
        match = self.db.scalar(
            select(Match).where(Match.id == match_id, self._involves(team))
        )
        if match is None:
            raise not_found("match.notFound")
        return match

    def simulate_for_team(
        self, team: Team, match_id: uuid.UUID, *, rng: random.Random | None = None
    ) -> Match:
        """Simulate one of the team's fixtures, rejecting an already-played one."""
        match = self.get_for_team(team, match_id)
        if match.played:
            raise conflict("match.alreadyPlayed")
        return MatchSimulationService(self.db, rng=rng).simulate(match)

    def _involves(self, team: Team):
        return or_(Match.homeTeamId == team.id, Match.awayTeamId == team.id)
