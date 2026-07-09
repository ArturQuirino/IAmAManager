"""youth_candidates table

Adds the weekly youth-academy prospects. Each candidate mirrors a player's
six-attribute / four-position shape, belongs to a team, and is tagged with the
week it was generated for. Reuses the existing `players_position_enum`.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-09
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE youth_candidates (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            name character varying NOT NULL,
            position players_position_enum NOT NULL,
            pace integer NOT NULL,
            shooting integer NOT NULL,
            passing integer NOT NULL,
            dribbling integer NOT NULL,
            defending integer NOT NULL,
            physical integer NOT NULL,
            "weekOf" date NOT NULL,
            "teamId" uuid NOT NULL,
            CONSTRAINT "PK_youth_candidates" PRIMARY KEY (id),
            CONSTRAINT "FK_youth_candidates_team" FOREIGN KEY ("teamId")
                REFERENCES teams(id) ON DELETE CASCADE
        )
        """
    )
    op.execute(
        'CREATE INDEX "IDX_youth_candidates_teamId" '
        'ON youth_candidates ("teamId")'
    )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS "IDX_youth_candidates_teamId"')
    op.execute("DROP TABLE youth_candidates")
