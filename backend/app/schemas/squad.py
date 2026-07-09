from pydantic import BaseModel

from app.schemas.player import PlayerResponse


class SquadResponse(BaseModel):
    teamName: str
    players: list[PlayerResponse]
