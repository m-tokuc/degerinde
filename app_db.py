"""
Değerinde — Prediction persistence (SQLAlchemy)
Ayrı predictions tablosu; araclar veri setine dokunmaz.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Generator, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def _default_db_url() -> str:
    return os.getenv(
        "DB_URL",
        "postgresql+psycopg2://postgres:sifre123@localhost:5432/postgres",
    )


DB_URL = _default_db_url()

engine = create_engine(
    DB_URL,
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


class PredictionLog(Base):
    """Kullanıcı tahmin sorgularının audit log'u."""

    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    brand = Column(String(100), nullable=True, index=True)
    model = Column(String(100), nullable=True)  # Seri (Clio, Egea…)
    trim = Column(String(200), nullable=True)   # Model/Trim (1.5 dCi Touch)
    year = Column(Integer, nullable=True)
    km = Column(Integer, nullable=True)
    fuel_type = Column(String(50), nullable=True)
    gear_type = Column(String(50), nullable=True)
    boya_degisen = Column(String(200), nullable=True)
    boya_degisen_count = Column(Integer, nullable=True, default=0)
    predicted_price = Column(Float, nullable=False)
    shap_explanation = Column(JSONB, nullable=True)
    request_id = Column(String(64), nullable=True, index=True)
    client_ip = Column(String(64), nullable=True)


def init_db() -> None:
    """predictions tablosunu oluştur (idempotent)."""
    Base.metadata.create_all(bind=engine)
    # Ek güvenlik: ham SQL ile IF NOT EXISTS
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS predictions (
                id UUID PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                brand VARCHAR(100),
                model VARCHAR(100),
                trim VARCHAR(200),
                year INTEGER,
                km INTEGER,
                fuel_type VARCHAR(50),
                gear_type VARCHAR(50),
                boya_degisen VARCHAR(200),
                boya_degisen_count INTEGER DEFAULT 0,
                predicted_price DOUBLE PRECISION NOT NULL,
                shap_explanation JSONB,
                request_id VARCHAR(64),
                client_ip VARCHAR(64)
            )
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_predictions_created_at ON predictions (created_at DESC)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_predictions_brand ON predictions (brand)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_predictions_request_id ON predictions (request_id)"
        ))
    print("✅ predictions tablosu hazır.")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def parse_boya_count(boya_degisen: Optional[str]) -> int:
    """'3 Parça' gibi metinden sayı çıkar; yoksa 0."""
    if not boya_degisen or boya_degisen in ("Belirtilmemiş", "None", ""):
        return 0
    import re
    m = re.search(r"(\d+)", str(boya_degisen))
    return int(m.group(1)) if m else 0


def log_prediction(
    *,
    brand: Optional[str],
    model: Optional[str],
    trim: Optional[str],
    year: Optional[int],
    km: Optional[int],
    fuel_type: Optional[str],
    gear_type: Optional[str],
    boya_degisen: Optional[str],
    predicted_price: float,
    shap_explanation: Optional[dict] = None,
    request_id: Optional[str],
    client_ip: Optional[str],
) -> None:
    """Senkron DB yazımı — BackgroundTasks içinden çağrılır."""
    db = SessionLocal()
    try:
        row = PredictionLog(
            id=uuid.uuid4(),
            created_at=datetime.now(timezone.utc),
            brand=brand,
            model=model,
            trim=trim,
            year=year,
            km=km,
            fuel_type=fuel_type,
            gear_type=gear_type,
            boya_degisen=boya_degisen,
            boya_degisen_count=parse_boya_count(boya_degisen),
            predicted_price=predicted_price,
            shap_explanation=shap_explanation,
            request_id=request_id,
            client_ip=client_ip,
        )
        db.add(row)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"⚠️ Prediction log hatası (non-blocking): {e}")
    finally:
        db.close()
