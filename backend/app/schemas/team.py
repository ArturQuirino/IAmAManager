from pydantic import BaseModel, ConfigDict, Field, field_validator

# Team-name length limits mirror the registration rule (see schemas/auth.py):
# the same club-naming constraints apply whether the name is chosen at sign-up
# or edited later on the team screen.
TEAM_NAME_MIN_LENGTH = 2
TEAM_NAME_MAX_LENGTH = 50


class TeamResponse(BaseModel):
    """General information shown on the team screen.

    Combines the club's identity (name), its current placement (division level
    and season, null while unplaced), the running season record, and the squad
    size. Assembled explicitly by the router since the derived fields are not
    plain columns of the `Team` model.
    """

    model_config = ConfigDict(from_attributes=True)

    teamName: str
    divisionLevel: int | None
    seasonNumber: int | None
    played: int
    wins: int
    draws: int
    losses: int
    goalsFor: int
    goalsAgainst: int
    goalDifference: int
    points: int
    playersCount: int


class UpdateTeamRequest(BaseModel):
    teamName: str = Field(
        min_length=TEAM_NAME_MIN_LENGTH, max_length=TEAM_NAME_MAX_LENGTH
    )

    @field_validator("teamName")
    @classmethod
    def validate_team_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < TEAM_NAME_MIN_LENGTH:
            raise ValueError("teamName is too short")
        return normalized
