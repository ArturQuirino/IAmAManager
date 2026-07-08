"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-08
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE players_position_enum AS ENUM (
                'GK', 'CB', 'LB', 'RB', 'CDM', 'CM', 'CAM', 'LW', 'RW', 'ST'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            email character varying NOT NULL,
            password character varying NOT NULL,
            "teamName" character varying NOT NULL,
            "createdAt" TIMESTAMP NOT NULL DEFAULT now(),
            "updatedAt" TIMESTAMP NOT NULL DEFAULT now(),
            CONSTRAINT "UQ_users_email" UNIQUE (email),
            CONSTRAINT "PK_users" PRIMARY KEY (id)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS players (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            name character varying NOT NULL,
            position players_position_enum NOT NULL,
            "shirtNumber" integer NOT NULL,
            age integer NOT NULL,
            nationality character varying NOT NULL,
            overall integer NOT NULL,
            "userId" uuid NOT NULL,
            CONSTRAINT "PK_players" PRIMARY KEY (id),
            CONSTRAINT "FK_players_user" FOREIGN KEY ("userId")
                REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    op.execute(
        'CREATE INDEX IF NOT EXISTS "IDX_players_userId" ON players ("userId")'
    )


def downgrade() -> None:
    op.execute("DROP TABLE players")
    op.execute("DROP TABLE users")
    op.execute("DROP TYPE players_position_enum")
