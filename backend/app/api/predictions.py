"""
Catálogo de fixtures + predicciones del modelo + simulación de torneo.
Lecturas intensivas -> cacheadas en Redis con TTL.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..db.models import Fixture
from ..schemas.schemas import FixtureOut
from ..ml.inference import inference
from ..ml.montecarlo import simulate_tournament
from ..core.ratelimit import _r, _redis_ok
from ..services.api_football import is_real_fixture, normalize_team_name

router = APIRouter(prefix="/v1", tags=["predictions"])

_TOURNEY_CACHE_KEY = "tourney:champion"
_TOURNEY_TTL = 3600


@router.get("/fixtures", response_model=list[FixtureOut])
def list_fixtures(
    stage: str | None = Query(None, max_length=40),
    db: Session = Depends(get_db),
):
    q = db.query(Fixture)
    real_exists = db.query(Fixture.id).filter(or_(
        Fixture.external_id.like("football-data:%"),
        Fixture.external_id.like("api-football:%"),
    )).first() is not None
    if real_exists:
        q = q.filter(or_(
            Fixture.external_id.like("football-data:%"),
            Fixture.external_id.like("api-football:%"),
        ))
    if stage:
        q = q.filter(Fixture.stage == stage)
    return q.order_by(Fixture.kickoff_utc).limit(200).all()


@router.get("/fixtures/{fixture_id}/prediction")
def fixture_prediction(fixture_id: int, db: Session = Depends(get_db)):
    if not inference.ready:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "modelo no cargado")
    fx = db.get(Fixture, fixture_id)
    if not fx:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "fixture no existe")
    try:
        return inference.predict_match(fx.home_team, fx.away_team, neutral=fx.neutral)
    except KeyError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"equipo sin datos: {e}")


@router.get("/predict")
def predict_adhoc(
    home: str = Query(max_length=100),
    away: str = Query(max_length=100),
    neutral: bool = True,
):
    """Predicción ad-hoc entre dos selecciones conocidas por el modelo."""
    if not inference.ready:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "modelo no cargado")
    try:
        return inference.predict_match(
            normalize_team_name(home),
            normalize_team_name(away),
            neutral=neutral,
        )
    except KeyError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"equipo sin datos: {e}")


@router.get("/tournament/champion")
def tournament_champion(db: Session = Depends(get_db)):
    """Probabilidades de campeón/finalista/avance vía Monte Carlo. Cacheado."""
    if not inference.ready:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "modelo no cargado")

    if _redis_ok and _r is not None:
        cached = _r.get(_TOURNEY_CACHE_KEY)
        if cached:
            return json.loads(cached)

    groups: dict[str, list[str]] = {}
    fixtures = db.query(Fixture).order_by(Fixture.kickoff_utc).all()
    real_fixtures = [fx for fx in fixtures if is_real_fixture(fx)]
    selected = real_fixtures or fixtures
    for fx in selected:
        if not fx.stage.startswith("group_"):
            continue
        group_name = fx.stage.split("_", 1)[1].upper()
        bucket = groups.setdefault(group_name, [])
        for team in (fx.home_team, fx.away_team):
            if team in inference.teams and team not in bucket:
                bucket.append(team)

    groups = {k: v for k, v in groups.items() if len(v) == 4}
    if not groups:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "no hay grupos oficiales cargados; sincroniza fixtures del Mundial 2026",
        )

    result = simulate_tournament(inference.model, groups, n_sims=5000)
    result["source"] = "football-data.org" if real_fixtures else "demo"
    result["group_count"] = len(groups)

    if _redis_ok and _r is not None:
        _r.setex(_TOURNEY_CACHE_KEY, _TOURNEY_TTL, json.dumps(result))
    return result
