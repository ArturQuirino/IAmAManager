"""teams table and reconciled player model

Introduces the `teams` entity (owning players; nullable userId for future fake
teams), moves `teamName` from users to teams, reworks `players` to the
6-attribute / 4-position model with a derived overall, and repoints players
from userId to teamId.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-08
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. teams table.
    op.execute(
        """
        CREATE TABLE teams (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            "teamName" character varying NOT NULL,
            "userId" uuid,
            "divisionId" uuid,
            "createdAt" TIMESTAMP NOT NULL DEFAULT now(),
            "updatedAt" TIMESTAMP NOT NULL DEFAULT now(),
            CONSTRAINT "PK_teams" PRIMARY KEY (id),
            CONSTRAINT "FK_teams_user" FOREIGN KEY ("userId")
                REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    op.execute('CREATE INDEX "IDX_teams_userId" ON teams ("userId")')

    # 2. One team per existing user, carrying the old teamName.
    op.execute(
        """
        INSERT INTO teams (id, "teamName", "userId")
        SELECT uuid_generate_v4(), u."teamName", u.id FROM users u
        """
    )

    # 3. Repoint players onto teams via teamId.
    op.execute('ALTER TABLE players ADD COLUMN "teamId" uuid')
    op.execute(
        """
        UPDATE players p SET "teamId" = t.id
        FROM teams t WHERE t."userId" = p."userId"
        """
    )
    op.execute('ALTER TABLE players ALTER COLUMN "teamId" SET NOT NULL')
    op.execute(
        """
        ALTER TABLE players ADD CONSTRAINT "FK_players_team"
            FOREIGN KEY ("teamId") REFERENCES teams(id) ON DELETE CASCADE
        """
    )

    # 4. Six core attributes seeded from the old overall, plus isStarter.
    for attribute in (
        "pace",
        "shooting",
        "passing",
        "dribbling",
        "defending",
        "physical",
    ):
        op.execute(f'ALTER TABLE players ADD COLUMN {attribute} integer')
        op.execute(f'UPDATE players SET {attribute} = overall')
        op.execute(f'ALTER TABLE players ALTER COLUMN {attribute} SET NOT NULL')
    op.execute(
        'ALTER TABLE players ADD COLUMN "isStarter" boolean NOT NULL DEFAULT false'
    )

    # 5. Collapse the 10-position enum into 4 broad positions.
    op.execute(
        "CREATE TYPE players_position_enum_new AS ENUM ('GK', 'DEF', 'MID', 'ATT')"
    )
    op.execute(
        """
        ALTER TABLE players ALTER COLUMN position TYPE players_position_enum_new
        USING (
            CASE position::text
                WHEN 'GK' THEN 'GK'
                WHEN 'CB' THEN 'DEF'
                WHEN 'LB' THEN 'DEF'
                WHEN 'RB' THEN 'DEF'
                WHEN 'CDM' THEN 'MID'
                WHEN 'CM' THEN 'MID'
                WHEN 'CAM' THEN 'MID'
                WHEN 'LW' THEN 'ATT'
                WHEN 'RW' THEN 'ATT'
                WHEN 'ST' THEN 'ATT'
            END::players_position_enum_new
        )
        """
    )
    op.execute("DROP TYPE players_position_enum")
    op.execute("ALTER TYPE players_position_enum_new RENAME TO players_position_enum")

    # 6. Drop superseded player columns and the old owner link.
    op.execute('DROP INDEX IF EXISTS "IDX_players_userId"')
    op.execute('ALTER TABLE players DROP COLUMN "userId"')
    op.execute('ALTER TABLE players DROP COLUMN "shirtNumber"')
    op.execute("ALTER TABLE players DROP COLUMN age")
    op.execute("ALTER TABLE players DROP COLUMN nationality")
    op.execute("ALTER TABLE players DROP COLUMN overall")
    op.execute('CREATE INDEX "IDX_players_teamId" ON players ("teamId")')

    # 7. teamName now lives on teams.
    op.execute('ALTER TABLE users DROP COLUMN "teamName"')


def downgrade() -> None:
    # Players of ownerless (fake) teams cannot be mapped back to a userId.
    op.execute(
        """
        DELETE FROM players
        WHERE "teamId" IN (SELECT id FROM teams WHERE "userId" IS NULL)
        """
    )

    # 1. Restore users.teamName from the owning team.
    op.execute(
        'ALTER TABLE users ADD COLUMN "teamName" character varying NOT NULL DEFAULT \'\''
    )
    op.execute(
        """
        UPDATE users u SET "teamName" = t."teamName"
        FROM teams t WHERE t."userId" = u.id
        """
    )
    op.execute('ALTER TABLE users ALTER COLUMN "teamName" DROP DEFAULT')

    # 2. Re-add the old player columns.
    op.execute('ALTER TABLE players ADD COLUMN "userId" uuid')
    op.execute(
        """
        UPDATE players p SET "userId" = t."userId"
        FROM teams t WHERE t.id = p."teamId"
        """
    )
    op.execute('ALTER TABLE players ALTER COLUMN "userId" SET NOT NULL')
    op.execute(
        """
        ALTER TABLE players ADD CONSTRAINT "FK_players_user"
            FOREIGN KEY ("userId") REFERENCES users(id) ON DELETE CASCADE
        """
    )

    op.execute("ALTER TABLE players ADD COLUMN overall integer")
    op.execute(
        """
        UPDATE players SET overall = ROUND(
            (pace + shooting + passing + dribbling + defending + physical) / 6.0
        )
        """
    )
    op.execute("ALTER TABLE players ALTER COLUMN overall SET NOT NULL")

    op.execute('ALTER TABLE players ADD COLUMN "shirtNumber" integer')
    op.execute(
        """
        UPDATE players p SET "shirtNumber" = s.rn FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY "teamId" ORDER BY id) AS rn
            FROM players
        ) s WHERE s.id = p.id
        """
    )
    op.execute('ALTER TABLE players ALTER COLUMN "shirtNumber" SET NOT NULL')
    op.execute(
        "ALTER TABLE players ADD COLUMN age integer NOT NULL DEFAULT 25"
    )
    op.execute("ALTER TABLE players ALTER COLUMN age DROP DEFAULT")
    op.execute(
        "ALTER TABLE players ADD COLUMN nationality character varying "
        "NOT NULL DEFAULT 'Unknown'"
    )
    op.execute("ALTER TABLE players ALTER COLUMN nationality DROP DEFAULT")

    # 3. Expand the 4-position enum back to the 10-position enum.
    op.execute(
        """
        CREATE TYPE players_position_enum_old AS ENUM (
            'GK', 'CB', 'LB', 'RB', 'CDM', 'CM', 'CAM', 'LW', 'RW', 'ST'
        )
        """
    )
    op.execute(
        """
        ALTER TABLE players ALTER COLUMN position TYPE players_position_enum_old
        USING (
            CASE position::text
                WHEN 'GK' THEN 'GK'
                WHEN 'DEF' THEN 'CB'
                WHEN 'MID' THEN 'CM'
                WHEN 'ATT' THEN 'ST'
            END::players_position_enum_old
        )
        """
    )
    op.execute("DROP TYPE players_position_enum")
    op.execute("ALTER TYPE players_position_enum_old RENAME TO players_position_enum")

    # 4. Drop the new player columns and the teamId link.
    op.execute('DROP INDEX IF EXISTS "IDX_players_teamId"')
    op.execute('ALTER TABLE players DROP CONSTRAINT "FK_players_team"')
    op.execute('ALTER TABLE players DROP COLUMN "teamId"')
    op.execute('ALTER TABLE players DROP COLUMN "isStarter"')
    for attribute in (
        "pace",
        "shooting",
        "passing",
        "dribbling",
        "defending",
        "physical",
    ):
        op.execute(f"ALTER TABLE players DROP COLUMN {attribute}")
    op.execute('CREATE INDEX "IDX_players_userId" ON players ("userId")')

    # 5. Drop the teams table.
    op.execute('DROP INDEX IF EXISTS "IDX_teams_userId"')
    op.execute("DROP TABLE teams")
