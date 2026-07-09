from pydantic import BaseModel

from app.schemas.player import PlayerResponse


class YouthResponse(BaseModel):
    # Youth prospects reuse the player contract (six attributes + derived
    # overall); a candidate becomes a Player unchanged when promoted.
    candidates: list[PlayerResponse]
    # Current squad size and the cap, so the client can disable "add" once the
    # squad is full (see docs/players.md).
    squadSize: int
    maxSquadSize: int
