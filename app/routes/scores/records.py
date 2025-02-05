
from app.models import ScoreRecordsModel, ScoreModel
from app.common.database import DBScore
from app.common.constants import Mods

from fastapi import Request, APIRouter
from sqlalchemy.orm import Session
from typing import List

router = APIRouter()

@router.get("/records/performance", response_model=ScoreRecordsModel)
def get_performance_records(request: Request):
    standard = (
        top_score_pp(mode=0, mods=0, exclude=[Mods.Relax, Mods.Autopilot], session=request.state.db),
        top_score_pp(mode=0, mods=Mods.Relax, session=request.state.db),
        top_score_pp(mode=0, mods=Mods.Autopilot, session=request.state.db),
    )

    taiko = (
        top_score_pp(mode=1, mods=0, exclude=[Mods.Relax], session=request.state.db),
        top_score_pp(mode=1, mods=Mods.Relax, session=request.state.db),
    )

    ctb = (
        top_score_pp(mode=2, mods=0, exclude=[Mods.Relax], session=request.state.db),
        top_score_pp(mode=2, mods=Mods.Relax, session=request.state.db),
    )

    mania = top_score_pp(
        mode=3,
        mods=0,
        session=request.state.db
    )

    return ScoreRecordsModel(
        osu_vanilla=ScoreModel.model_validate(standard[0], from_attributes=True),
        osu_relax=ScoreModel.model_validate(standard[1], from_attributes=True),
        osu_autopilot=ScoreModel.model_validate(standard[2], from_attributes=True),
        taiko_vanilla=ScoreModel.model_validate(taiko[0], from_attributes=True),
        taiko_relax=ScoreModel.model_validate(taiko[1], from_attributes=True),
        ctb_vanilla=ScoreModel.model_validate(ctb[0], from_attributes=True),
        ctb_relax=ScoreModel.model_validate(ctb[1], from_attributes=True),
        mania=ScoreModel.model_validate(mania, from_attributes=True)
    )

@router.get("/records/score", response_model=ScoreRecordsModel)
def get_score_records(request: Request):
    standard = (
        top_score_rscore(mode=0, mods=0, exclude=[Mods.Relax, Mods.Autopilot], session=request.state.db),
        top_score_rscore(mode=0, mods=Mods.Relax, session=request.state.db),
        top_score_rscore(mode=0, mods=Mods.Autopilot, session=request.state.db),
    )

    taiko = (
        top_score_rscore(mode=1, mods=0, exclude=[Mods.Relax], session=request.state.db),
        top_score_rscore(mode=1, mods=Mods.Relax, session=request.state.db),
    )

    ctb = (
        top_score_rscore(mode=2, mods=0, exclude=[Mods.Relax], session=request.state.db),
        top_score_rscore(mode=2, mods=Mods.Relax, session=request.state.db),
    )

    mania = top_score_rscore(
        mode=3,
        mods=0,
        session=request.state.db
    )

    return ScoreRecordsModel(
        osu_vanilla=ScoreModel.model_validate(standard[0], from_attributes=True),
        osu_relax=ScoreModel.model_validate(standard[1], from_attributes=True),
        osu_autopilot=ScoreModel.model_validate(standard[2], from_attributes=True),
        taiko_vanilla=ScoreModel.model_validate(taiko[0], from_attributes=True),
        taiko_relax=ScoreModel.model_validate(taiko[1], from_attributes=True),
        ctb_vanilla=ScoreModel.model_validate(ctb[0], from_attributes=True),
        ctb_relax=ScoreModel.model_validate(ctb[1], from_attributes=True),
        mania=ScoreModel.model_validate(mania, from_attributes=True)
    )

def top_score_pp(
    mode: int,
    mods: int,
    exclude: List[int] = [],
    session: Session = ...
) -> DBScore:
    query = session.query(DBScore).filter(
        DBScore.hidden == False,
        DBScore.status_pp == 3,
        DBScore.mode == mode
    )

    if mods:
        query = query.filter(DBScore.mods.op("&")(mods) > 0)

    for mod in exclude:
        query = query.filter(DBScore.mods.op("&")(mod) == 0)

    return query.order_by(DBScore.pp.desc()).first()

def top_score_rscore(
    mode: int,
    mods: int,
    exclude: List[int] = [],
    session: Session = ...
) -> DBScore:
    query = session.query(DBScore).filter(
        DBScore.status_score == 3,
        DBScore.hidden == False,
        DBScore.mode == mode
    )

    if mods:
        query = query.filter(DBScore.mods.op("&")(mods) > 0)

    for mod in exclude:
        query = query.filter(DBScore.mods.op("&")(mod) == 0)

    return query.order_by(DBScore.total_score.desc()).first()
