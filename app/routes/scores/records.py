
from app.common.config import config_instance as config
from app.models import ScoreRecordsModel, ScoreModel
from app.common.database import DBScore, DBBeatmap
from app.common.constants import Mods

from fastapi import Request, APIRouter
from sqlalchemy.orm import Session
from typing import List

router = APIRouter()

@router.get("/records/performance", response_model=ScoreRecordsModel)
def get_performance_records(request: Request):
    standard = top_score_pp(mode=0, session=request.state.db)
    taiko = top_score_pp(mode=1, session=request.state.db)
    ctb = top_score_pp(mode=2, session=request.state.db)
    mania = top_score_pp(mode=3, session=request.state.db)

    return ScoreRecordsModel(
        osu=ScoreModel.model_validate(standard, from_attributes=True),
        taiko=ScoreModel.model_validate(taiko, from_attributes=True),
        ctb=ScoreModel.model_validate(ctb, from_attributes=True),
        mania=ScoreModel.model_validate(mania, from_attributes=True)
    )

@router.get("/records/score", response_model=ScoreRecordsModel)
def get_score_records(request: Request):
    standard = top_score_rscore(mode=0, session=request.state.db)
    taiko = top_score_rscore(mode=1, session=request.state.db)
    ctb = top_score_rscore(mode=2, session=request.state.db)
    mania = top_score_rscore(mode=3, session=request.state.db)

    return ScoreRecordsModel(
        osu=ScoreModel.model_validate(standard, from_attributes=True),
        taiko=ScoreModel.model_validate(taiko, from_attributes=True),
        ctb=ScoreModel.model_validate(ctb, from_attributes=True),
        mania=ScoreModel.model_validate(mania, from_attributes=True)
    )

def top_score_pp(mode: int, session: Session) -> DBScore:
    query = session.query(DBScore).filter(
        DBScore.status_pp == 3,
        DBScore.hidden == False,
        DBScore.mode == mode
    )

    if not config.APPROVED_MAP_REWARDS:
        # Ensure that the map is either ranked or approved
        query = query.join(DBScore.beatmap).filter(DBBeatmap.status.in_((1, 2)))

    return query.order_by(DBScore.pp.desc()).first()

def top_score_rscore(mode: int, session: Session) -> DBScore:
    query = session.query(DBScore).filter(
        DBScore.status_score == 3,
        DBScore.hidden == False,
        DBScore.mode == mode
    )

    if not config.APPROVED_MAP_REWARDS:
        # Ensure that the map is either ranked or approved
        query = query.join(DBScore.beatmap).filter(DBBeatmap.status.in_((1, 2)))

    return query.order_by(DBScore.total_score.desc()).first()
