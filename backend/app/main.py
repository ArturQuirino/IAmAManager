import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.database.session import SessionLocal
from app.routers import (
    auth,
    competition,
    dev,
    health,
    matches,
    players,
    squad,
    tactics,
    team,
    youth,
)
from app.scheduler import start_scheduler
from app.seed.seed import run_seed

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
    scheduler_task = start_scheduler()
    try:
        yield
    finally:
        if scheduler_task is not None:
            scheduler_task.cancel()


app = FastAPI(title="Football Manager API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "errorCode" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


api_router = health.router
app.include_router(api_router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(players.router, prefix="/api")
app.include_router(team.router, prefix="/api")
app.include_router(competition.router, prefix="/api")
app.include_router(squad.router, prefix="/api")
app.include_router(tactics.router, prefix="/api")
app.include_router(youth.router, prefix="/api")
app.include_router(matches.router, prefix="/api")

# The manual matchday trigger is a development aid only — never exposed in
# production, where the daily scheduler is the sole driver of the game world.
if not settings.is_production:
    app.include_router(dev.router, prefix="/api")
