import uuid

from pydantic import BaseModel, ConfigDict


class PlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    position: str
    pace: int
    shooting: int
    passing: int
    dribbling: int
    defending: int
    physical: int
    overall: int


class MyTeamResponse(BaseModel):
    teamName: str
    players: list[PlayerResponse]
