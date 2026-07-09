import uuid

from pydantic import BaseModel

from app.schemas.player import PlayerResponse


class StartingXiRequest(BaseModel):
    # The intended starting XI. Composition (exactly eleven, one goalkeeper) is
    # validated in TacticsService so it can emit a stable errorCode; keeping the
    # schema permissive avoids FastAPI's generic 422 shadowing that code.
    playerIds: list[uuid.UUID]


class TacticsResponse(BaseModel):
    # Outfield shape of the current XI (e.g. "4-3-3"); null when none is set.
    formation: str | None
    starters: list[PlayerResponse]
    bench: list[PlayerResponse]
