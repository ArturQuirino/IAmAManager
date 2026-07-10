from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.schemas.dev import MatchdayReportResponse
from app.services.matchday_service import MatchdayService

# Development-only endpoints for exercising the real-time loop by hand. This
# router is not mounted in production (see main.py); there the daily scheduler
# is the only trigger.
router = APIRouter(prefix="/dev", tags=["dev"])


@router.post("/run-matchday", response_model=MatchdayReportResponse)
def run_matchday(
    _: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchdayReportResponse:
    """Manually advance the game world by one day (idempotent per day)."""
    report = MatchdayService(db).run_due_matchday()
    return MatchdayReportResponse(
        ran=report.ran,
        matchesPlayed=report.matchesPlayed,
        seasonEnded=report.seasonEnded,
        youthRefreshed=report.youthRefreshed,
    )
