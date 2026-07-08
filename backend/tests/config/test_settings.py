from datetime import timedelta

import pytest

from app.config.settings import Settings, parse_jwt_expires_in


def test_parse_jwt_expires_in_supports_all_units() -> None:
    assert parse_jwt_expires_in("7d") == timedelta(days=7)
    assert parse_jwt_expires_in("2h") == timedelta(hours=2)
    assert parse_jwt_expires_in("30m") == timedelta(minutes=30)
    assert parse_jwt_expires_in("45s") == timedelta(seconds=45)


def test_parse_jwt_expires_in_rejects_invalid_format() -> None:
    with pytest.raises(ValueError):
        parse_jwt_expires_in("bogus")


def test_cors_origins_list_splits_and_strips() -> None:
    settings = Settings(cors_origins="http://a.com, http://b.com ,")

    assert settings.cors_origins_list == ["http://a.com", "http://b.com"]


def test_should_seed() -> None:
    assert Settings(node_env="development", run_seed="false").should_seed is True
    assert Settings(node_env="production", run_seed="false").should_seed is False
    assert Settings(node_env="production", run_seed="true").should_seed is True
