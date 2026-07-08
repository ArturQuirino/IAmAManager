import uuid

from pydantic import BaseModel, ConfigDict, Field


class PlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    name: str
    position: str
    shirtNumber: int = Field(serialization_alias="shirtNumber")
    age: int
    nationality: str
    overall: int
    userId: uuid.UUID = Field(serialization_alias="userId")


class MyTeamResponse(BaseModel):
    teamName: str
    players: list[PlayerResponse]
