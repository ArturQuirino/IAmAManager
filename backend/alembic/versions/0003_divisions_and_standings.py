"""divisions table and team season standings

Adds the `divisions` entity (the tiered competition pyramid), links teams to a
division via a real foreign key on the existing `divisionId` column, and gives
each team its season standing counters (points, played, W/D/L, goals for/against).

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-09
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STANDING_COLUMNS = (
    "points",
    "played",
    "wins",
    "draws",
    "losses",
    "goalsFor",
    "goalsAgainst",
)


def upgrade() -> None:
    # 1. divisions table.
    op.execute(
        """
        CREATE TABLE divisions (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            level integer NOT NULL,
            "seasonNumber" integer NOT NULL,
            "createdAt" TIMESTAMP NOT NULL DEFAULT now(),
            "updatedAt" TIMESTAMP NOT NULL DEFAULT now(),
            CONSTRAINT "PK_divisions" PRIMARY KEY (id)
        )
        """
    )
    op.execute('CREATE INDEX "IDX_divisions_level" ON divisions (level)')

    # 2. Promote teams.divisionId (a plain column since 0002) to a real FK.
    op.execute(
        """
        ALTER TABLE teams ADD CONSTRAINT "FK_teams_division"
            FOREIGN KEY ("divisionId") REFERENCES divisions(id) ON DELETE SET NULL
        """
    )

    # 3. Season standing counters, all starting at zero.
    for column in STANDING_COLUMNS:
        op.execute(
            f'ALTER TABLE teams ADD COLUMN "{column}" integer NOT NULL DEFAULT 0'
        )


def downgrade() -> None:
    for column in STANDING_COLUMNS:
        op.execute(f'ALTER TABLE teams DROP COLUMN "{column}"')
    op.execute('ALTER TABLE teams DROP CONSTRAINT "FK_teams_division"')
    op.execute('DROP INDEX IF EXISTS "IDX_divisions_level"')
    op.execute("DROP TABLE divisions")
