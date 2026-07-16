"""
Inicializa la base: crea tablas, siembra equipos/fixtures de demo y un admin.
La contraseña admin se toma de ADMIN_PASSWORD (entorno), nunca hardcodeada.

Uso: python -m app.seed
"""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta

from .db.session import Base, engine, SessionLocal
from .db.models import (
    User, Team, Fixture, FixtureStatus, Role,
    UserPrediction, PredictionStatus,
)
from .core.security import hash_password
from .core.config import settings
from .ml.inference import inference
from .services.api_football import sync_world_cup_fixtures

# ---------------------------------------------------------------------------
# Fase de grupos oficial del Mundial FIFA 2026 (formato 48 equipos, 12 grupos).
# Datos "quemados" para una demo autocontenida: cada grupo tiene 4 selecciones
# que el modelo conoce, con la jornada 1 ya jugada (resultados) y el resto por
# jugar (cuotas). Esto habilita además la simulación de campeón (Monte Carlo).
# ---------------------------------------------------------------------------
GROUPS_2026: dict[str, list[str]] = {
    "a": ["Mexico", "Croatia", "Ecuador", "New Zealand"],
    "b": ["Canada", "Morocco", "Japan", "Jordan"],
    "c": ["United States", "Uruguay", "Egypt", "Uzbekistan"],
    "d": ["Argentina", "Denmark", "South Korea", "Panama"],
    "e": ["France", "Senegal", "Poland", "Costa Rica"],
    "f": ["Brazil", "Switzerland", "Ghana", "Saudi Arabia"],
    "g": ["Spain", "Colombia", "Iran", "Norway"],
    "h": ["England", "Serbia", "Cameroon", "Peru"],
    "i": ["Portugal", "Sweden", "Nigeria", "Paraguay"],
    "j": ["Germany", "Turkey", "Australia", "Chile"],
    "k": ["Netherlands", "Austria", "Scotland", "Wales"],
    "l": ["Italy", "Belgium", "Ukraine", "Czech Republic"],
}

# Calendario round-robin (método del círculo) para 4 equipos: (jornada, i, j).
ROUND_ROBIN = [
    (1, 0, 3), (1, 1, 2),
    (2, 0, 2), (2, 3, 1),
    (3, 0, 1), (3, 2, 3),
]

# Marcadores plausibles y deterministas para la jornada ya jugada.
DEMO_SCORES = [(2, 1), (1, 0), (0, 0), (3, 1), (2, 0), (1, 1),
               (2, 2), (0, 1), (3, 0), (1, 2), (2, 3), (0, 2)]

# Usuarios de demo para que el ranking se vea vivo (contraseña común de demo).
DEMO_USERS = [
    ("lucia@demo.io", 3120),
    ("mateo@demo.io", 2480),
    ("sofia@demo.io", 1975),
    ("diego@demo.io", 1540),
    ("valentina@demo.io", 1230),
    ("nico@demo.io", 860),
    ("camila@demo.io", 640),
]

# Plantillas de apuestas de demo (mercado, selección, stake, cuota). Se aplican
# sobre partidos YA jugados para mostrar un historial realista de gana/pierde.
DEMO_BET_TEMPLATES = [
    ("1x2", "home", 150, 1.85),
    ("ou_2.5", "over", 100, 1.95),
    ("btts", "yes", 120, 2.05),
    ("1x2", "away", 80, 3.40),
    ("ou_2.5", "under", 110, 1.90),
    ("1x2", "draw", 60, 3.10),
]


def _bet_won(market: str, selection: str, hg: int, ag: int) -> bool:
    """Misma lógica de liquidación que el panel admin (1x2 / over-under / btts)."""
    if market == "1x2":
        res = "home" if hg > ag else "draw" if hg == ag else "away"
        return selection == res
    if market.startswith("ou_"):
        line = float(market.split("_")[1])
        total = hg + ag
        return (selection == "over" and total > line) or (selection == "under" and total < line)
    if market == "btts":
        both = hg > 0 and ag > 0
        return (selection == "yes" and both) or (selection == "no" and not both)
    return False


def _seed_demo_bets(db):
    """Crea historial de apuestas ya liquidadas para los usuarios de demo.

    Cada usuario recibe varias apuestas sobre partidos jugados (jornada 1), con
    su estado ganada/perdida calculado desde el marcador real y el pago aplicado.
    Idempotente: si ya existen (misma idempotency_key) no se duplican.
    """
    finished = (
        db.query(Fixture)
        .filter(Fixture.status == FixtureStatus.finished)
        .order_by(Fixture.id.asc())
        .all()
    )
    if not finished:
        return
    now = datetime.now(timezone.utc)
    for u_idx, (email, _bal) in enumerate(DEMO_USERS):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            continue
        for k in range(5):
            fx = finished[(u_idx + k) % len(finished)]
            market, selection, stake, odds = DEMO_BET_TEMPLATES[(u_idx + k) % len(DEMO_BET_TEMPLATES)]
            key = f"seed-{u_idx}-{k}"
            if db.query(UserPrediction).filter(
                UserPrediction.user_id == user.id,
                UserPrediction.idempotency_key == key,
            ).first():
                continue
            won = _bet_won(market, selection, fx.home_score, fx.away_score)
            db.add(UserPrediction(
                user_id=user.id, fixture_id=fx.id, market=market, selection=selection,
                stake_points=stake, odds_taken=odds, idempotency_key=key,
                status=PredictionStatus.won if won else PredictionStatus.lost,
                payout_points=int(round(stake * odds)) if won else 0,
                created_at=now - timedelta(days=6, hours=k),
                settled_at=now - timedelta(days=5, hours=k),
            ))


def _build_group_stage(db):
    """Crea las 72 fixtures de la fase de grupos (jornada 1 jugada, resto por jugar)."""
    now = datetime.now(timezone.utc)
    past = now - timedelta(days=6)   # jornada 1 (jugada)
    future = now + timedelta(days=1)  # jornadas 2 y 3 (por jugar)
    score_i = 0
    idx = 0
    for letter, teams in GROUPS_2026.items():
        for md, i, j in ROUND_ROBIN:
            home, away = teams[i], teams[j]
            ext = f"demo-g{letter}-md{md}-{i}{j}"
            if db.query(Fixture).filter(Fixture.external_id == ext).first():
                continue
            if md == 1:
                gh, ga = DEMO_SCORES[score_i % len(DEMO_SCORES)]
                score_i += 1
                db.add(Fixture(
                    external_id=ext, stage=f"group_{letter}", home_team=home, away_team=away,
                    kickoff_utc=past + timedelta(hours=idx), neutral=True,
                    status=FixtureStatus.finished, home_score=gh, away_score=ga,
                ))
            else:
                db.add(Fixture(
                    external_id=ext, stage=f"group_{letter}", home_team=home, away_team=away,
                    kickoff_utc=future + timedelta(hours=idx), neutral=True,
                    status=FixtureStatus.scheduled,
                ))
            idx += 1



def main():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        # admin (solo si no existe)
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        if not db.query(User).filter(User.email == admin_email).first():
            pw = os.getenv("ADMIN_PASSWORD")
            if not pw:
                raise SystemExit("define ADMIN_PASSWORD en el entorno para crear el admin")
            db.add(User(email=admin_email, password_hash=hash_password(pw), role=Role.admin))

        # equipos desde el modelo (si está cargado)
        inference.load()
        for name in inference.teams:
            if not db.query(Team).filter(Team.name == name).first():
                db.add(Team(name=name))

        seeded_real = False
        if settings.football_data_api_key:
            try:
                result = sync_world_cup_fixtures(db)
                seeded_real = result.imported > 0
                print(
                    f"sync football-data.org ok: {result.imported} fixtures "
                    f"(competencia {result.competition_code}, temporada {result.season})"
                )
            except Exception as e:
                print(f"sync football-data.org falló, usando demo: {e}")

        if not seeded_real:
            _build_group_stage(db)

        # Usuarios de demo (para poblar el ranking). Contraseña opcional DEMO_PASSWORD.
        demo_pw = os.getenv("DEMO_PASSWORD")
        if demo_pw:
            demo_hash = hash_password(demo_pw)
            for email, balance in DEMO_USERS:
                if not db.query(User).filter(User.email == email).first():
                    db.add(User(
                        email=email, password_hash=demo_hash,
                        role=Role.user, points_balance=balance,
                    ))
            db.flush()  # asegura IDs de usuarios antes de crear su historial
            _seed_demo_bets(db)

        db.commit()
        print(f"seed ok: {db.query(Team).count()} equipos, {db.query(Fixture).count()} fixtures")
    finally:
        db.close()


if __name__ == "__main__":
    main()
