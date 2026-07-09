import random

from app.models.player import ATTRIBUTE_NAMES, Player, PlayerPosition

ATTRIBUTE_MIN = 1
ATTRIBUTE_MAX = 100

# 4-3-3 shape for the starting XI: 1 GK, 4 DEF, 3 MID, 3 ATT.
STARTER_SHAPE: dict[PlayerPosition, int] = {
    PlayerPosition.GK: 1,
    PlayerPosition.DEF: 4,
    PlayerPosition.MID: 3,
    PlayerPosition.ATT: 3,
}
DEFAULT_BENCH_SIZE = 7

FIRST_NAMES = (
    "Marco", "Lucas", "Diego", "Antoine", "Erik", "Carlos", "Nikolai",
    "Kwame", "Matteo", "Thomas", "Yuki", "Andreas", "Felipe", "Oliver",
    "Rafael", "Ibrahim", "Samuel", "Victor", "Mateo", "Stefan", "Emmanuel",
    "Pierre", "David", "Henrik", "James",
)
LAST_NAMES = (
    "Silva", "Fernandez", "Morales", "Dubois", "Lindqvist", "Mendes",
    "Petrov", "Osei", "Rossi", "Becker", "Tanaka", "Christou", "Costa",
    "Hughes", "Santos", "Okonkwo", "Andersson", "Garcia", "Novak", "Koffi",
    "Martin", "Kowalski", "Dahl", "Whitmore", "Berg",
)


class PlayerGenerator:
    """Creates randomly generated (unpersisted) players and squads.

    Pure logic — holds no database session. An injectable RNG keeps tests
    deterministic. Returned `Player` objects have no `teamId` yet; the caller
    assigns the team and persists them.
    """

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng or random.Random()

    def random_player(
        self,
        position: PlayerPosition | None = None,
        *,
        skill_scale: float = 1.0,
    ) -> Player:
        chosen = position or self._rng.choice(list(PlayerPosition))
        attributes = {name: self._roll(skill_scale) for name in ATTRIBUTE_NAMES}
        return Player(
            name=self._random_name(),
            position=chosen,
            isStarter=False,
            **attributes,
        )

    def random_squad(
        self,
        *,
        skill_scale: float = 1.0,
        bench_size: int = DEFAULT_BENCH_SIZE,
    ) -> list[Player]:
        """A full squad: a 4-3-3 starting XI plus random-position bench.

        `skill_scale` below 1.0 produces weaker players (used by fake teams).
        The starters always satisfy the minimum composition (1 GK, 10
        outfield), so any bench mix is safe.
        """
        squad: list[Player] = []
        for position, count in STARTER_SHAPE.items():
            for _ in range(count):
                starter = self.random_player(position, skill_scale=skill_scale)
                starter.isStarter = True
                squad.append(starter)
        for _ in range(bench_size):
            squad.append(self.random_player(skill_scale=skill_scale))
        return squad

    def _roll(self, skill_scale: float) -> int:
        value = round(self._rng.randint(ATTRIBUTE_MIN, ATTRIBUTE_MAX) * skill_scale)
        return max(ATTRIBUTE_MIN, min(ATTRIBUTE_MAX, value))

    def _random_name(self) -> str:
        return f"{self._rng.choice(FIRST_NAMES)} {self._rng.choice(LAST_NAMES)}"
