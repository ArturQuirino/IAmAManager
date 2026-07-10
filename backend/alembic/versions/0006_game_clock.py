"""game_clock singleton

Adds the single-row clock that drives the real-time daily matchday job: it
records the last calendar day a round was played (so the job stays idempotent
and never runs twice a day) and a running day counter used for the weekly
youth-academy refresh cadence.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-09
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE game_clock (
            id integer NOT NULL,
            "lastMatchdayDate" date,
            "dayCount" integer NOT NULL DEFAULT 0,
            CONSTRAINT "PK_game_clock" PRIMARY KEY (id),
            CONSTRAINT "CK_game_clock_singleton" CHECK (id = 1)
        )
        """
    )
    op.execute('INSERT INTO game_clock (id, "dayCount") VALUES (1, 0)')


def downgrade() -> None:
    op.execute("DROP TABLE game_clock")
