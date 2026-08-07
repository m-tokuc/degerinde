"""
Değerinde — production startup / environment validation.
Called from FastAPI startup and usable as a CLI: python validate_env.py
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


@dataclass
class ValidationReport:
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def print(self) -> None:
        print("\n═══ Değerinde Environment Validation ═══")
        for c in self.checks:
            mark = "✅" if c.ok else "❌"
            print(f"  {mark} {c.name}: {c.detail}")
        print(f"═══ Overall: {'PASS' if self.ok else 'FAIL'} ═══\n")


def validate_environment(
    *,
    model_loaded: bool | None = None,
    model_path: str | None = None,
    require_araclar: bool = False,
) -> ValidationReport:
    """
    Validate model file, DB (predictions), and CORS config.
    If model_loaded is passed (from main), reuse that flag; else probe MODEL_PATH.
    """
    report = ValidationReport()
    model_path = model_path or os.getenv("MODEL_PATH", "car_price_model.pkl")
    db_url = os.getenv(
        "DB_URL",
        "postgresql+psycopg2://postgres:sifre123@localhost:5432/postgres",
    )
    cors = os.getenv("CORS_ORIGINS", "*")

    # 1) Model pickle
    if model_loaded is not None:
        report.checks.append(
            CheckResult(
                "model_loaded",
                model_loaded,
                f"in-memory flag={model_loaded} path={model_path}",
            )
        )
    else:
        exists = os.path.isfile(model_path)
        loaded_ok = False
        detail = f"missing file: {model_path}"
        if exists:
            try:
                import joblib
                data = joblib.load(model_path)
                loaded_ok = "model" in data and "categorical_features" in data
                n = len(data.get("categorical_features", [])) + len(
                    data.get("numerical_features", [])
                )
                detail = f"{model_path} OK · features={n} · r2={data.get('r2', '?')}"
            except Exception as e:
                detail = f"load error: {e}"
        report.checks.append(CheckResult("model_pkl", loaded_ok, detail))

    # 2) Database + predictions table
    db_ok = False
    db_detail = ""
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            # Ensure predictions exists / is queryable
            try:
                from app_db import init_db

                init_db()
            except Exception:
                pass
            n = conn.execute(text("SELECT COUNT(*) FROM predictions")).scalar()
            db_detail = f"connected · predictions rows={n} · url_host={_safe_host(db_url)}"
            if require_araclar:
                cars = conn.execute(text('SELECT COUNT(*) FROM araclar')).scalar()
                db_detail += f" · araclar={cars}"
                db_ok = cars is not None and int(cars) > 0
            else:
                db_ok = True
        engine.dispose()
    except Exception as e:
        db_detail = f"DB error: {e}"
        db_ok = False
    report.checks.append(CheckResult("database", db_ok, db_detail))

    # 3) CORS
    origins = [o.strip() for o in cors.split(",") if o.strip()]
    cors_ok = len(origins) > 0
    if cors == "*" or origins == ["*"]:
        detail = "CORS_ORIGINS=* (dev OK; lock down for production Flutter domains)"
    else:
        detail = f"CORS_ORIGINS={origins}"
        # Soft warning if no http(s) origins listed — still pass if non-empty
        cors_ok = any(o.startswith("http") or o == "*" for o in origins) or len(origins) > 0
    report.checks.append(CheckResult("cors", cors_ok, detail))

    return report


def _safe_host(db_url: str) -> str:
    try:
        # postgresql+psycopg2://user:pass@host:port/db
        after_at = db_url.split("@", 1)[1]
        return after_at.split("/", 1)[0]
    except Exception:
        return "(hidden)"


def main() -> int:
    report = validate_environment(require_araclar=True)
    report.print()
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
