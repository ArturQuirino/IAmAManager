"""Shared pytest fixtures.

The whole suite runs against an **in-memory SQLite** database and FastAPI
dependency overrides, so it is fast, isolated and idempotent — no real
Postgres, no network. Each test gets a fresh schema (created and dropped per
test) which guarantees no state bleeds between tests.
"""

from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Import the models so their tables register on Base.metadata *before*
# create_all runs. app/models/__init__.py is empty, so without these imports
# the metadata would be empty and no tables would be created.
import app.models.division  # noqa: F401
import app.models.player  # noqa: F401
import app.models.team  # noqa: F401
import app.models.user  # noqa: F401
from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.user import User
from app.services.auth_service import AuthService


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """A SQLAlchemy Session bound to a throwaway in-memory SQLite database.

    StaticPool + a single shared connection keep the in-memory database alive
    for the duration of the test (a plain in-memory engine would drop the
    schema as soon as the first connection is returned to the pool).
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session_local = sessionmaker(
        bind=engine, autocommit=False, autoflush=False
    )
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient with get_db overridden to use the in-memory session.

    Instantiated **without** the `with` context manager on purpose: entering
    the context would trigger the app lifespan, which runs `run_seed` against
    the real Postgres engine. We only need the routes, not startup events.
    """

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(db_session: Session) -> Callable[[User], dict[str, str]]:
    """Factory that mints a valid `Authorization` header for a given user.

    Signs a real JWT with the same secret the app uses, so the full
    `get_current_user` decode + lookup path is exercised end to end.
    """

    def _build(user: User) -> dict[str, str]:
        token = AuthService(db_session).create_access_token(user)
        return {"Authorization": f"Bearer {token}"}

    return _build
