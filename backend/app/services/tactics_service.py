import uuid
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import not_found, unprocessable
from app.models.player import Player, PlayerPosition
from app.models.team import Team

# A starting XI is exactly eleven players: one goalkeeper and ten outfield
# players in any mix of defenders/midfielders/attackers (see docs/players.md,
# "Starting XI"). Ten outfield is implied by the first two rules, so it is not
# a separate failure mode.
REQUIRED_STARTERS = 11
REQUIRED_GOALKEEPERS = 1

# The order positions are grouped in for display (mirrors SquadService).
_POSITION_ORDER = {
    PlayerPosition.GK: 0,
    PlayerPosition.DEF: 1,
    PlayerPosition.MID: 2,
    PlayerPosition.ATT: 3,
}

# Outfield lines, in the order a formation string reads (e.g. "4-3-3").
_FORMATION_LINES = (PlayerPosition.DEF, PlayerPosition.MID, PlayerPosition.ATT)


def derive_formation(starters: list[Player]) -> str | None:
    """The outfield shape of the starting XI as a "DEF-MID-ATT" string.

    Formations are not a fixed enum (docs/players.md): the shape is read off
    the starters' positions, e.g. 4 defenders / 3 midfielders / 3 attackers →
    "4-3-3". Returns None when no XI has been set yet, so the client can show a
    placeholder rather than "0-0-0".
    """
    outfield = [player for player in starters if player.position != PlayerPosition.GK]
    if not outfield:
        return None
    counts = Counter(player.position for player in outfield)
    return "-".join(str(counts.get(line, 0)) for line in _FORMATION_LINES)


class TacticsService:
    """Reads and sets a team's starting XI within the composition rules.

    Starters are persisted on `Player.isStarter`; only the starting XI takes
    part in a match (docs/match-simulation.md). Every query filters by the
    resolved team's id, which enforces ownership (IDOR): a player id belonging
    to another team never resolves and is reported as not found.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_tactics(self, team: Team) -> tuple[list[Player], list[Player]]:
        """The team's starters and bench, each grouped GK → DEF → MID → ATT."""
        players = self._team_players(team)
        starters = self._sorted([p for p in players if p.isStarter])
        bench = self._sorted([p for p in players if not p.isStarter])
        return starters, bench

    def set_starting_xi(
        self, team: Team, player_ids: list[uuid.UUID]
    ) -> tuple[list[Player], list[Player]]:
        """Persist the given players as the starting XI, benching the rest.

        Validates that the selection is exactly eleven distinct owned players
        with exactly one goalkeeper before touching any state.
        """
        unique_ids = self._validate_selection_size(player_ids)
        players = self._team_players(team)
        starters = self._select_owned(players, unique_ids)
        self._assert_valid_composition(starters)

        starter_ids = {player.id for player in starters}
        for player in players:
            player.isStarter = player.id in starter_ids
        self.db.commit()
        return self.get_tactics(team)

    def _validate_selection_size(
        self, player_ids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        unique_ids = set(player_ids)
        if (
            len(player_ids) != REQUIRED_STARTERS
            or len(unique_ids) != REQUIRED_STARTERS
        ):
            raise unprocessable("tactics.mustBe11")
        return unique_ids

    def _select_owned(
        self, players: list[Player], unique_ids: set[uuid.UUID]
    ) -> list[Player]:
        starters = [player for player in players if player.id in unique_ids]
        if len(starters) != REQUIRED_STARTERS:
            raise not_found("tactics.playerNotFound")
        return starters

    def _assert_valid_composition(self, starters: list[Player]) -> None:
        goalkeepers = sum(
            1 for player in starters if player.position == PlayerPosition.GK
        )
        if goalkeepers != REQUIRED_GOALKEEPERS:
            raise unprocessable("tactics.needExactlyOneGk")

    def _team_players(self, team: Team) -> list[Player]:
        return list(
            self.db.scalars(
                select(Player).where(Player.teamId == team.id)
            ).all()
        )

    def _sorted(self, players: list[Player]) -> list[Player]:
        return sorted(
            players,
            key=lambda player: (_POSITION_ORDER[player.position], player.name),
        )
