import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import conflict, not_found
from app.models.player import Player, PlayerPosition
from app.models.team import Team

# Squad composition guardrails (see docs/players.md): a squad must always keep
# at least one goalkeeper and ten outfield players, and never exceed the cap.
MIN_GOALKEEPERS = 1
MIN_OUTFIELD_PLAYERS = 10
MAX_SQUAD_SIZE = 40

# The order positions are grouped in for display.
_POSITION_ORDER = {
    PlayerPosition.GK: 0,
    PlayerPosition.DEF: 1,
    PlayerPosition.MID: 2,
    PlayerPosition.ATT: 3,
}


class SquadService:
    """Reads a team's squad and removes players within the composition rules.

    Adding players is owned by other flows (registration, youth academy); this
    service only exposes reads and the guard-railed removal.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_squad(self, team: Team) -> list[Player]:
        """The team's players, grouped GK → DEF → MID → ATT, then by name."""
        players = self.db.scalars(
            select(Player).where(Player.teamId == team.id)
        ).all()
        return sorted(
            players,
            key=lambda player: (_POSITION_ORDER[player.position], player.name),
        )

    def remove_player(self, team: Team, player_id: uuid.UUID) -> None:
        """Release a player, provided it does not break a squad minimum.

        Filtering by the team's id enforces ownership (IDOR): a player that
        belongs to another team is reported as not found, never removed.
        """
        player = self.db.scalar(
            select(Player).where(
                Player.id == player_id, Player.teamId == team.id
            )
        )
        if player is None:
            raise not_found("squad.playerNotFound")

        self._assert_removable(team, player)
        self.db.delete(player)
        self.db.commit()

    def _assert_removable(self, team: Team, player: Player) -> None:
        if player.position == PlayerPosition.GK:
            if self._count_goalkeepers(team) <= MIN_GOALKEEPERS:
                raise conflict("squad.minGoalkeeper")
        elif self._count_outfield(team) <= MIN_OUTFIELD_PLAYERS:
            raise conflict("squad.minOutfield")

    def _count_goalkeepers(self, team: Team) -> int:
        return self._count(team, is_goalkeeper=True)

    def _count_outfield(self, team: Team) -> int:
        return self._count(team, is_goalkeeper=False)

    def _count(self, team: Team, *, is_goalkeeper: bool) -> int:
        condition = (
            Player.position == PlayerPosition.GK
            if is_goalkeeper
            else Player.position != PlayerPosition.GK
        )
        return (
            self.db.scalar(
                select(func.count())
                .select_from(Player)
                .where(Player.teamId == team.id, condition)
            )
            or 0
        )
