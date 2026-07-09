"""matches table

Adds the season fixture list: one row per confrontation on a given round of a
division's season, holding the played score and the per-minute event log used
to replay a match. Scores and the log stay null until the match is simulated.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-09
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE matches (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            "divisionId" uuid NOT NULL,
            "seasonNumber" integer NOT NULL,
            round integer NOT NULL,
            "homeTeamId" uuid NOT NULL,
            "awayTeamId" uuid NOT NULL,
            "scheduledDate" date,
            "homeScore" integer,
            "awayScore" integer,
            played boolean NOT NULL DEFAULT false,
            "eventLog" jsonb,
            CONSTRAINT "PK_matches" PRIMARY KEY (id),
            CONSTRAINT "FK_matches_division" FOREIGN KEY ("divisionId")
                REFERENCES divisions(id) ON DELETE CASCADE,
            CONSTRAINT "FK_matches_home_team" FOREIGN KEY ("homeTeamId")
                REFERENCES teams(id) ON DELETE CASCADE,
            CONSTRAINT "FK_matches_away_team" FOREIGN KEY ("awayTeamId")
                REFERENCES teams(id) ON DELETE CASCADE
        )
        """
    )
    op.execute(
        'CREATE INDEX "IDX_matches_divisionId" ON matches ("divisionId")'
    )
    op.execute('CREATE INDEX "IDX_matches_homeTeamId" ON matches ("homeTeamId")')
    op.execute('CREATE INDEX "IDX_matches_awayTeamId" ON matches ("awayTeamId")')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS "IDX_matches_awayTeamId"')
    op.execute('DROP INDEX IF EXISTS "IDX_matches_homeTeamId"')
    op.execute('DROP INDEX IF EXISTS "IDX_matches_divisionId"')
    op.execute("DROP TABLE matches")
