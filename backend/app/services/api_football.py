"""
Sincronización de fixtures del Mundial 2026 desde football-data.org.

Mantiene el contrato del modelo actual:
  - guarda selecciones con nombres normalizados al vocabulario entrenado
  - evita mezclar fixtures demo con fixtures reales al consultar
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

import httpx
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..core.config import settings
from ..db.models import Fixture, FixtureStatus

REAL_FIXTURE_PREFIX = "football-data:"
LEGACY_REAL_FIXTURE_PREFIXES = ("football-data:", "api-football:")

TEAM_ALIASES = {
    "United States": "USA",
    "United States of America": "USA",
    "USA": "USA",
    "Mexico": "Mexico",
    "IR Iran": "Iran",
    "Korea Republic": "South Korea",
    "South Korea": "South Korea",
    "Korea DPR": "North Korea",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Czechia": "Czech Republic",
    "Türkiye": "Turkey",
    "DR Congo": "Congo DR",
    "Ivory Coast": "Cote d'Ivoire",
}

_ROUND_MAP = {
    "round of 32": "round_32",
    "round of 16": "round_16",
    "8th finals": "round_16",
    "quarter-finals": "quarter_final",
    "quarter finals": "quarter_final",
    "semi-finals": "semi_final",
    "semi finals": "semi_final",
    "3rd place final": "third_place",
    "third place": "third_place",
    "final": "final",
}


def normalize_team_name(name: str) -> str:
    clean = " ".join(name.split())
    return TEAM_ALIASES.get(clean, clean)


def is_real_fixture(fx: Fixture) -> bool:
    return bool(fx.external_id and fx.external_id.startswith(LEGACY_REAL_FIXTURE_PREFIXES))


def stage_from_match(stage_name: str | None, group_name: str | None = None) -> str:
    if group_name:
        lowered_group = group_name.strip().lower()
        m = re.search(r"group[_\s-]*([a-z])", lowered_group)
        if m:
            return f"group_{m.group(1)}"
        return "group_stage"

    if not stage_name:
        return "unknown"
    text = stage_name.strip()
    lowered = text.lower()
    if "group" in lowered:
        m = re.search(r"group\s+([a-z])", lowered)
        if m:
            return f"group_{m.group(1)}"
        return "group_stage"
    lowered = lowered.replace("-", " ").replace("_", " ")
    for key, value in _ROUND_MAP.items():
        if key in lowered:
            return value
    slug = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    return slug or "unknown"


def status_from_api(status_name: str | None) -> FixtureStatus:
    code = (status_name or "").upper()
    if code in {"SCHEDULED", "TIMED", "POSTPONED", "SUSPENDED", "CANCELLED"}:
        return FixtureStatus.scheduled
    if code in {"IN_PLAY", "PAUSED", "LIVE"}:
        return FixtureStatus.live
    return FixtureStatus.finished


@dataclass
class SyncResult:
    imported: int
    inserted: int
    updated: int
    competition_code: str
    season: int


class FootballDataClient:
    def __init__(self):
        self.base = settings.football_data_base.rstrip("/")
        self.key = settings.football_data_api_key
        self.competition_code = settings.football_data_competition_code

    @property
    def enabled(self) -> bool:
        return bool(self.key)

    def _get(self, path: str, params: dict | None = None) -> dict:
        if not self.enabled:
            raise RuntimeError("FOOTBALL_DATA_API_KEY no configurada")
        with httpx.Client(
            base_url=self.base,
            headers={"X-Auth-Token": self.key},
            timeout=20.0,
        ) as client:
            resp = client.get(path, params=params)
            resp.raise_for_status()
            data = resp.json()
        if "matches" not in data:
            raise RuntimeError("respuesta inesperada de football-data.org")
        return data

    def fetch_world_cup_fixtures(self, season: int | None = None) -> tuple[str, int, list[dict]]:
        selected_season = season or settings.football_data_season
        params = {"season": selected_season} if selected_season else None
        data = self._get(f"/competitions/{self.competition_code}/matches", params=params)
        rows = data.get("matches") or []
        response_season = selected_season
        filters = data.get("filters") or {}
        if filters.get("season"):
            try:
                response_season = int(filters["season"])
            except (TypeError, ValueError):
                pass
        return self.competition_code, response_season, rows


def sync_world_cup_fixtures(db: Session, season: int | None = None) -> SyncResult:
    client = FootballDataClient()
    competition_code, season, rows = client.fetch_world_cup_fixtures(season=season)

    existing = {
        fx.external_id: fx
        for fx in db.query(Fixture).filter(or_(
            Fixture.external_id.like("football-data:%"),
            Fixture.external_id.like("api-football:%"),
        )).all()
        if fx.external_id
    }

    inserted = 0
    updated = 0
    imported = 0
    for row in rows:
        home = row.get("homeTeam", {}) or {}
        away = row.get("awayTeam", {}) or {}
        if not home.get("name") or not away.get("name") or not row.get("id") or not row.get("utcDate"):
            continue

        external_id = f"{REAL_FIXTURE_PREFIX}{row['id']}"
        obj = existing.get(external_id)
        if obj is None:
            legacy_external_id = f"api-football:{row['id']}"
            obj = existing.get(legacy_external_id)
        if obj is None:
            obj = Fixture(neutral=True)
            db.add(obj)
            inserted += 1
        else:
            updated += 1

        obj.external_id = external_id
        obj.stage = stage_from_match(row.get("stage"), row.get("group"))
        obj.home_team = normalize_team_name(home["name"])
        obj.away_team = normalize_team_name(away["name"])
        obj.kickoff_utc = datetime.fromisoformat(row["utcDate"].replace("Z", "+00:00"))
        obj.status = status_from_api(row.get("status"))

        full_time = ((row.get("score") or {}).get("fullTime") or {})
        obj.home_score = full_time.get("home")
        obj.away_score = full_time.get("away")
        imported += 1

    db.commit()
    return SyncResult(
        imported=imported,
        inserted=inserted,
        updated=updated,
        competition_code=competition_code,
        season=season,
    )
