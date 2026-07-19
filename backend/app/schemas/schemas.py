"""Esquemas Pydantic: validación fuerte de entrada/salida (defensa inyección)."""
from __future__ import annotations

import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

_NICK_RE = re.compile(r"^[\w .\-]+$", re.UNICODE)


class RegisterIn(BaseModel):
    email: EmailStr
    nickname: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("nickname")
    @classmethod
    def clean_nickname(cls, v: str) -> str:
        v = v.strip()
        # letras/números/espacios y . - _ (evita inyección/control chars en el
        # nombre público). El unique real lo garantiza la BD.
        if len(v) < 3 or not _NICK_RE.match(v):
            raise ValueError("nickname: 3-30 caracteres, solo letras, números, espacios y . - _")
        return v

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        # Complejidad mínima: >=10 chars, 1 mayúscula, 1 número y 1 especial.
        if (len(v) < 10
                or not re.search(r"[A-Z]", v)
                or not re.search(r"\d", v)
                or not re.search(r"[^A-Za-z0-9]", v)):
            raise ValueError(
                "contraseña: mínimo 10 caracteres, con al menos una mayúscula, "
                "un número y un caracter especial"
            )
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    # El refresh token ya no viaja en el body -- va en cookie HttpOnly
    # (ver api/auth.py). Solo el access token, que el frontend guarda en
    # memoria (nunca localStorage).
    access_token: str
    token_type: str = "bearer"


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    jti: str
    created_at: datetime
    expires_at: datetime


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    nickname: str | None = None
    role: str
    points_balance: int


class FixtureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    stage: str
    home_team: str
    away_team: str
    kickoff_utc: datetime
    status: str
    home_score: int | None = None
    away_score: int | None = None


class PredictionIn(BaseModel):
    fixture_id: int
    market: str = Field(max_length=40)
    selection: str = Field(max_length=40)
    stake_points: int = Field(gt=0, le=100000)
    idempotency_key: str = Field(min_length=8, max_length=64)


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fixture_id: int
    home_team: str | None = None
    away_team: str | None = None
    market: str
    selection: str
    stake_points: int
    odds_taken: float
    status: str
    payout_points: int | None = None
    created_at: datetime
