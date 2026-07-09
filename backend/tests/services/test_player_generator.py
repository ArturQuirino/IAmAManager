import random
from collections import Counter

from app.models.player import ATTRIBUTE_NAMES, PlayerPosition
from app.services.player_generator import (
    DEFAULT_BENCH_SIZE,
    STARTER_SHAPE,
    PlayerGenerator,
)


def _generator() -> PlayerGenerator:
    return PlayerGenerator(rng=random.Random(1234))


def test_random_player_attributes_within_bounds() -> None:
    player = _generator().random_player()

    for attribute in ATTRIBUTE_NAMES:
        value = getattr(player, attribute)
        assert 1 <= value <= 100
    assert isinstance(player.position, PlayerPosition)
    assert player.isStarter is False
    assert player.name


def test_random_player_honours_requested_position() -> None:
    player = _generator().random_player(PlayerPosition.GK)

    assert player.position == PlayerPosition.GK


def test_random_player_position_is_uniform_across_four() -> None:
    generator = _generator()

    positions = Counter(generator.random_player().position for _ in range(400))

    assert set(positions) == set(PlayerPosition)


def test_random_squad_has_433_starters() -> None:
    squad = _generator().random_squad()

    starters = [player for player in squad if player.isStarter]
    starter_positions = Counter(player.position for player in starters)

    assert starter_positions[PlayerPosition.GK] == STARTER_SHAPE[PlayerPosition.GK]
    assert starter_positions[PlayerPosition.DEF] == STARTER_SHAPE[PlayerPosition.DEF]
    assert starter_positions[PlayerPosition.MID] == STARTER_SHAPE[PlayerPosition.MID]
    assert starter_positions[PlayerPosition.ATT] == STARTER_SHAPE[PlayerPosition.ATT]
    assert len(starters) == 11


def test_random_squad_bench_size_and_flags() -> None:
    squad = _generator().random_squad()

    bench = [player for player in squad if not player.isStarter]

    assert len(bench) == DEFAULT_BENCH_SIZE
    assert len(squad) == 11 + DEFAULT_BENCH_SIZE


def test_skill_scale_lowers_attributes() -> None:
    squad = _generator().random_squad(skill_scale=0.5)

    for player in squad:
        for attribute in ATTRIBUTE_NAMES:
            value = getattr(player, attribute)
            assert 1 <= value <= 50
