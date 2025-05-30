
from fastapi import HTTPException, APIRouter, Request
from app.common.database import reports
from app.models import ReportModel
from app.utils import requires
from typing import List

router = APIRouter()

@router.get("/reports", response_model=List[ReportModel])
@requires("users.moderation.reports")
def get_user_reports(request: Request, user_id: int) -> List[ReportModel]:
    return [
        ReportModel.model_validate(report, from_attributes=True)
        for report in reports.fetch_all(user_id, request.state.db)
    ]

@router.delete("/reports/{id}", response_model=ReportModel)
@requires("users.moderation.reports.delete")
def resolve_user_report(
    request: Request,
    user_id: int,
    id: int
) -> ReportModel:
    if not (report := reports.fetch_by_id(id, request.state.db)):
        raise HTTPException(404, "Report not found")

    if report.target_id != user_id:
        raise HTTPException(400, "Report does not belong to the specified user")

    success = reports.update(
        report.id,
        {"resolved": True},
        request.state.db
    )

    if not success:
        raise HTTPException(500, "Failed to resolve report")

    return ReportModel.model_validate(report, from_attributes=True)
