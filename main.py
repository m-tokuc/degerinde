"""
Değerinde — FastAPI Backend v5
Clean schema (araclar_clean) + cascading options from live brands + XGBoost predict
"""
from __future__ import annotations

import os
import re
import uuid
from typing import Any, List, Optional

from dotenv import load_dotenv
load_dotenv()

import joblib
import numpy as np
import pandas as pd
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, text

from app_db import init_db, log_prediction, SessionLocal, PredictionLog
from validate_env import validate_environment
from schema_clean import (
    ensure_clean_table,
    load_clean_dataframe,
    normalize_str,
    parse_hasar_flags,
    parse_tramer_tl,
)

# ─── Config (env-overridable) ───
DB_URL = os.getenv(
    "DB_URL",
    "postgresql+psycopg2://postgres:sifre123@localhost:5432/postgres",
)
MODEL_PATH = os.getenv("MODEL_PATH", "car_price_model.pkl")
PORT = int(os.getenv("PORT", "8000"))
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "*").split(",")
    if o.strip()
]
# Empty FOCUS_BRANDS = all brands present in DB (dynamic growth).
# Set e.g. FOCUS_BRANDS=Fiat,Renault only to temporarily restrict UI.
FOCUS_BRANDS = [
    b.strip()
    for b in os.getenv("FOCUS_BRANDS", "").split(",")
    if b.strip()
]
WEB_DIR = os.getenv("WEB_DIR", os.path.join("frontend", "build", "web"))
STARTUP_VALIDATION: dict = {"ok": False, "checks": []}

app = FastAPI(title="Değerinde API", version="5.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api import router as api_router
app.include_router(api_router, prefix="/api/v2")


engine = create_engine(DB_URL, pool_size=5, max_overflow=10, pool_pre_ping=True)

# ─── Model ───
MODEL_R2 = None
MODEL_MAE = None
MODEL_MAPE = None
try:
    model_data = joblib.load(MODEL_PATH)
    model_pipeline = model_data['model']
    CAT_FEATURES = model_data['categorical_features']
    NUM_FEATURES = model_data['numerical_features']
    MODEL_R2 = float(model_data.get('r2') or 0)
    MODEL_MAE = float(model_data.get('mae') or 0)
    MODEL_MAPE = float(model_data.get('mape') or 0) if model_data.get('mape') is not None else None
    is_model_loaded = True
    print(
        f"✅ Model yüklendi. R²={MODEL_R2:.4f} MAE={MODEL_MAE:,.0f}"
        + (f" MAPE={MODEL_MAPE:.2f}%" if MODEL_MAPE is not None else "")
    )
except Exception as e:
    model_pipeline = None
    CAT_FEATURES = []
    NUM_FEATURES = []
    is_model_loaded = False
    print(f"⚠️ Model yüklenemedi: {e}")


@app.on_event("startup")
def on_startup():
    global STARTUP_VALIDATION
    try:
        init_db()
    except Exception as e:
        print(f"⚠️ predictions DB init hatası: {e}")
    try:
        ensure_clean_table(engine)
    except Exception as e:
        print(f"⚠️ araclar_clean ensure hatası: {e}")

    report = validate_environment(
        model_loaded=is_model_loaded,
        model_path=MODEL_PATH,
        require_araclar=False,
    )
    report.print()
    STARTUP_VALIDATION = {
        "ok": report.ok,
        "checks": [
            {"name": c.name, "ok": c.ok, "detail": c.detail}
            for c in report.checks
        ],
    }
    if not report.ok:
        print("⚠️ Startup validation FAILED — API will start but some features may be degraded.")


_combo_cache: Optional[pd.DataFrame] = None


def _valid_seri(val) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    s = str(val).strip()
    if not s:
        return False
    sn = normalize_str(s)
    if sn in {
        'fiyatlari', 'fiyatlar', 'belirtilmedi', 'belirtilmemis',
        'model', 've', 'r', 'nan', 'none',
    }:
        return False
    if re.search(r'fiyatlar', sn):
        return False
    return True


def _get_combo_df(force_reload: bool = False) -> pd.DataFrame:
    """Build cascading options from araclar_clean — all brands in DB by default."""
    global _combo_cache
    if _combo_cache is not None and not force_reload:
        return _combo_cache

    df = load_clean_dataframe(engine)
    print(f"CRITICAL: araclar_clean rows: {len(df)}")

    df = df.rename(columns={
        "Yil": "Yıl",
        "Yakit_Tipi": "Yakıt Tipi",
        "Vites_Tipi": "Vites Tipi",
        "Kasa_Tipi": "Kasa Tipi",
        "Cekis": "Çekiş",
        "Garanti_Durumu": "Garanti Durumu",
        "Silindir_Sayisi": "Silindir Sayısı",
        "Koltuk_Sayisi": "Koltuk Sayısı",
        "Motor_Hacmi": "Motor Hacmi",
        "Motor_Gucu": "Motor Gücü",
    })

    if "Boya_Durumu" not in df.columns:
        df["Boya_Durumu"] = "Belirsiz"
    df["Boya_Durumu"] = df["Boya_Durumu"].fillna("Belirsiz").astype(str)

    df["Yıl"] = pd.to_numeric(df["Yıl"], errors="coerce").astype("Int64")

    junk_mask = df["Seri"].notna() & ~df["Seri"].apply(_valid_seri)
    if junk_mask.any():
        print(f"CRITICAL: Dropping {junk_mask.sum()} junk Seri rows")
        df.loc[junk_mask, "Seri"] = None
        df.loc[junk_mask, "Model"] = None

    df["Marka_Search"] = df["Marka"].apply(normalize_str)
    df["Seri_Search"] = df["Seri"].apply(normalize_str)
    df["Model_Search"] = df["Model"].apply(normalize_str)
    df["Vites_Search"] = df["Vites Tipi"].apply(normalize_str)
    df["Yakit_Search"] = df["Yakıt Tipi"].apply(normalize_str)
    df["Kasa_Search"] = df["Kasa Tipi"].apply(normalize_str)

    def extract_first_int(val):
        if pd.isna(val) or str(val).strip() == "":
            return None
        m = re.search(r"(\d+)", str(val))
        return int(m.group(1)) if m else None

    df["Silindir Sayısı"] = df["Silindir Sayısı"].apply(extract_first_int)
    df["Koltuk Sayısı"] = df["Koltuk Sayısı"].apply(extract_first_int)
    df["Motor Hacmi"] = df["Motor Hacmi"].apply(extract_first_int).astype("Int64")
    df["Motor Gücü"] = df["Motor Gücü"].apply(extract_first_int).astype("Int64")

    usable = df["Marka"].notna() & df["Seri"].notna() & (df["Marka"] != "Diğer")
    print(f"CRITICAL: Usable (Marka+Seri): {usable.sum()}")
    marka_counts = df.loc[usable].groupby("Marka").size().sort_values(ascending=False)
    print(f"📊 Markaya göre araç sayısı:\n{marka_counts.to_string()}")

    _combo_cache = df.loc[usable].copy()
    if FOCUS_BRANDS:
        before = len(_combo_cache)
        _combo_cache = _combo_cache[_combo_cache["Marka"].isin(FOCUS_BRANDS)].copy()
        print(
            f"FOCUS_BRANDS={FOCUS_BRANDS}: {before} → {len(_combo_cache)} "
            f"(env kısıtı — boş bırakırsanız tüm markalar gelir)"
        )
    else:
        print("FOCUS_BRANDS boş → DB'deki tüm markalar UI'da görünür (dinamik büyüme).")
    print(f"CRITICAL: Combo cache size: {len(_combo_cache)}")
    return _combo_cache


try:
    _get_combo_df()
except Exception as e:
    print(f"⚠️ Combo DF pre-load hatası: {e}")


# ─── Pydantic ───
class DynamicOptionsRequest(BaseModel):
    Marka: Optional[str] = None
    Seri: Optional[str] = None
    Model: Optional[str] = None
    Yil: Optional[int] = None
    Vites_Tipi: Optional[str] = None
    Yakit_Tipi: Optional[str] = None
    Kasa_Tipi: Optional[str] = None


class CarFeaturesRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    Kilometre: int
    Yil: int
    Marka: Optional[str] = 'Belirtilmemiş'
    Seri: Optional[str] = 'Belirtilmemiş'
    Model: Optional[str] = 'Belirtilmemiş'
    Vites_Tipi: Optional[str] = 'Belirtilmemiş'
    Yakit_Tipi: Optional[str] = 'Belirtilmemiş'
    Kasa_Tipi: Optional[str] = 'Belirtilmemiş'
    Cekis: Optional[str] = 'Belirtilmemiş'
    Renk: Optional[str] = 'Belirtilmemiş'
    Kimden: Optional[str] = 'Belirtilmemiş'
    Garanti_Durumu: Optional[str] = 'Belirtilmemiş'
    Silindir_Sayisi: Optional[str] = 'Belirtilmemiş'
    Koltuk_Sayisi: Optional[str] = 'Belirtilmemiş'
    Motor_Hacmi_cc: Optional[float] = None
    Motor_Gucu_hp: Optional[float] = None
    Tramer_TL: Optional[float] = 0.0
    Boya_Degisen: Optional[str] = 'Belirsiz'  # Boya_Durumu alias from UI
    Has_Boya: Optional[int] = None
    Has_Degisen: Optional[int] = None
    Has_Tramer: Optional[int] = None
    request_id: Optional[str] = None


def unique_sorted(series) -> List[Any]:
    vals = [
        str(v).strip() for v in series.dropna().unique()
        if str(v).strip() and str(v).strip().lower() not in ('nan', 'none', '')
    ]
    try:
        return sorted(set(vals), key=lambda x: x.lower())
    except Exception:
        return list(set(vals))


def unique_int_sorted(series) -> List[int]:
    vals = []
    for v in series.dropna().unique():
        try:
            vals.append(int(v))
        except (ValueError, TypeError):
            pass
    return sorted(set(vals), reverse=True)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _resolve_hasar(req: CarFeaturesRequest) -> dict:
    tramer = parse_tramer_tl(req.Tramer_TL)
    if req.Has_Boya is not None or req.Has_Degisen is not None or req.Has_Tramer is not None:
        has_boya = int(req.Has_Boya or 0)
        has_degisen = int(req.Has_Degisen or 0)
        has_tramer = int(req.Has_Tramer or 0) or (1 if tramer > 0 else 0)
        if has_boya and has_degisen:
            status = "Boyalı+Değişen"
        elif has_degisen:
            status = "Değişenli"
        elif has_boya:
            status = "Boyalı"
        elif has_tramer:
            status = "Tramerli"
        else:
            status = req.Boya_Degisen or "Belirsiz"
        return {
            "Boya_Durumu": status,
            "Has_Boya": has_boya,
            "Has_Degisen": has_degisen,
            "Has_Tramer": has_tramer,
            "Tramer_TL": tramer,
        }

    # Map UI Boya_Durumu labels OR free-text
    label = (req.Boya_Degisen or "Belirsiz").strip()
    label_map = {
        "Temiz": {"Boya_Durumu": "Temiz", "Has_Boya": 0, "Has_Degisen": 0, "Has_Tramer": 0},
        "Belirsiz": {"Boya_Durumu": "Belirsiz", "Has_Boya": 0, "Has_Degisen": 0, "Has_Tramer": 0},
        "Belirtilmemiş": {"Boya_Durumu": "Belirsiz", "Has_Boya": 0, "Has_Degisen": 0, "Has_Tramer": 0},
        "Boyalı": {"Boya_Durumu": "Boyalı", "Has_Boya": 1, "Has_Degisen": 0, "Has_Tramer": 0},
        "Değişenli": {"Boya_Durumu": "Değişenli", "Has_Boya": 0, "Has_Degisen": 1, "Has_Tramer": 0},
        "Boyalı+Değişen": {"Boya_Durumu": "Boyalı+Değişen", "Has_Boya": 1, "Has_Degisen": 1, "Has_Tramer": 0},
        "Tramerli": {"Boya_Durumu": "Tramerli", "Has_Boya": 0, "Has_Degisen": 0, "Has_Tramer": 1},
    }
    if label in label_map:
        out = dict(label_map[label])
        if tramer > 0:
            out["Has_Tramer"] = 1
            if out["Boya_Durumu"] == "Belirsiz":
                out["Boya_Durumu"] = "Tramerli"
        out["Tramer_TL"] = tramer
        return out

    flags = parse_hasar_flags(label, tramer_tl=tramer)
    flags["Tramer_TL"] = tramer
    return flags


# ─── ENDPOINTS ───
def _health_payload():
    cache_n = len(_combo_cache) if _combo_cache is not None else 0
    brands = []
    if _combo_cache is not None and len(_combo_cache):
        brands = sorted(_combo_cache["Marka"].dropna().unique().tolist())
    return {
        "status": "API çalışıyor",
        "model_loaded": is_model_loaded,
        "version": "5.0",
        "app": "Değerinde",
        "cars_in_cache": cache_n,
        "brands_in_cache": brands,
        "model_r2": MODEL_R2,
        "model_mae": MODEL_MAE,
        "model_mape": MODEL_MAPE,
        "features": len(CAT_FEATURES) + len(NUM_FEATURES),
        "cors_origins": CORS_ORIGINS,
        "focus_brands": FOCUS_BRANDS or None,
        "table": "araclar_clean",
        "startup_validation": STARTUP_VALIDATION,
    }


@app.get("/api/health")
def health_check():
    return _health_payload()


@app.get("/api/brands")
def list_all_brands():
    """Tüm markaları LIMIT OLMADAN döndür (cache'teki her benzersiz Marka)."""
    full_df = _get_combo_df()
    brands = unique_sorted(full_df['Marka'])
    counts = full_df.groupby('Marka').size().to_dict()
    return {
        "status": "success",
        "count": len(brands),
        "total_cars": int(len(full_df)),
        "limits_applied": False,
        "brands": brands,
        "brand_counts": {b: int(counts.get(b, 0)) for b in brands},
    }


@app.post("/api/dynamic_options")
def get_dynamic_options(req: DynamicOptionsRequest):
    try:
        full_df = _get_combo_df()
        df = full_df

        if req.Marka:
            df = df[df['Marka_Search'] == normalize_str(req.Marka)]
        if req.Seri:
            df = df[df['Seri_Search'] == normalize_str(req.Seri)]
        if req.Model:
            df = df[df['Model_Search'] == normalize_str(req.Model)]
        if req.Yil:
            df = df[df['Yıl'] == req.Yil]
        if req.Vites_Tipi:
            df = df[df['Vites_Search'] == normalize_str(req.Vites_Tipi)]
        if req.Yakit_Tipi:
            df = df[df['Yakit_Search'] == normalize_str(req.Yakit_Tipi)]
        if req.Kasa_Tipi:
            df = df[df['Kasa_Search'] == normalize_str(req.Kasa_Tipi)]

        # LIMIT YOK — her benzersiz değerin tamamı
        markalar = unique_sorted(full_df['Marka'])
        seriler = unique_sorted(df['Seri'])
        modeller = unique_sorted(df['Model'])
        yillar = unique_int_sorted(df['Yıl'])

        return {
            "status": "success",
            "total_matches": int(len(df)),
            "limits_applied": False,
            "meta": {
                "total_cars_in_cache": int(len(full_df)),
                "brand_count": len(markalar),
                "seri_returned": len(seriler),
                "model_returned": len(modeller),
                "yil_returned": len(yillar),
            },
            "Marka": markalar,
            "Seri": seriler,
            "Model": modeller,
            "Yil": yillar,
            "Vites_Tipi": unique_sorted(df['Vites Tipi']),
            "Yakit_Tipi": unique_sorted(df['Yakıt Tipi']),
            "Kasa_Tipi": unique_sorted(df['Kasa Tipi']),
            "Renk": unique_sorted(full_df['Renk']),
            "Cekis": unique_sorted(df['Çekiş']),
            "Motor_Hacmi": unique_sorted(df['Motor Hacmi']),
            "Motor_Gucu": unique_sorted(df['Motor Gücü']),
            "Garanti_Durumu": unique_sorted(full_df['Garanti Durumu']),
            "Silindir_Sayisi": unique_sorted(df['Silindir Sayısı']),
            "Koltuk_Sayisi": unique_sorted(df['Koltuk Sayısı']),
            "Kimden": unique_sorted(full_df['Kimden']),
            # Clean damage statuses (not raw tab titles)
            "Boya_Degisen": [
                "Boyasız / Tamamı Orijinal", "Belirsiz", "Boyalı", "Değişenli", "Boyalı+Değişen", "Tramerli"
            ],
        }
    except Exception as e:
        import traceback
        print(f"❌ dynamic_options HATA: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/reload_cache")
def reload_combo_cache():
    """Call after external scrape batches land in araclar_clean."""
    global _combo_cache
    _combo_cache = None
    df = _get_combo_df(force_reload=True)
    brands = unique_sorted(df["Marka"])
    return {
        "status": "success",
        "cars_in_cache": int(len(df)),
        "brand_count": len(brands),
        "brands": brands,
    }


@app.post("/api/predict")
def predict_price(
    req: CarFeaturesRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    if not is_model_loaded:
        raise HTTPException(status_code=503, detail="Model henüz yüklenmedi.")
    try:
        def parse_num(val):
            if val is None:
                return np.nan
            if isinstance(val, (int, float)):
                return float(val)
            m = re.search(r'(\d+[\.,]?\d*)', str(val).replace('.', '').replace(',', '.'))
            return float(m.group(1)) if m else np.nan

        hasar = _resolve_hasar(req)
        data = {
            'Marka': req.Marka or 'Belirtilmemiş',
            'Seri': req.Seri or 'Belirtilmemiş',
            'Model': req.Model or 'Belirtilmemiş',
            'Vites Tipi': req.Vites_Tipi or 'Belirtilmemiş',
            'Yakıt Tipi': req.Yakit_Tipi or 'Belirtilmemiş',
            'Kasa Tipi': req.Kasa_Tipi or 'Belirtilmemiş',
            'Çekiş': req.Cekis or 'Belirtilmemiş',
            'Renk': req.Renk or 'Belirtilmemiş',
            'Kimden': req.Kimden or 'Belirtilmemiş',
            'Garanti Durumu': req.Garanti_Durumu or 'Belirtilmemiş',
            'Silindir Sayısı': req.Silindir_Sayisi or 'Belirtilmemiş',
            'Koltuk Sayısı': req.Koltuk_Sayisi or 'Belirtilmemiş',
            'Boya_Durumu': hasar['Boya_Durumu'],
            # Back-compat if old pkl still has Boya_Degisen
            'Boya_Degisen': hasar['Boya_Durumu'],
            'Yıl': float(req.Yil),
            'Kilometre': float(req.Kilometre),
            'Motor_Hacmi_cc': parse_num(req.Motor_Hacmi_cc),
            'Motor_Gucu_hp': parse_num(req.Motor_Gucu_hp),
            'Tramer_TL': float(hasar['Tramer_TL']),
            'Has_Boya': float(hasar['Has_Boya']),
            'Has_Degisen': float(hasar['Has_Degisen']),
            'Has_Tramer': float(hasar['Has_Tramer']),
        }

        all_features = CAT_FEATURES + NUM_FEATURES

        def _predict_at_km(km_val: float) -> float:
            row = {
                k: data.get(k, np.nan if k in NUM_FEATURES else 'Belirtilmemiş')
                for k in all_features
            }
            row['Kilometre'] = float(max(0.0, km_val))
            df_input = pd.DataFrame([row])
            return max(0.0, float(model_pipeline.predict(df_input)[0]))

        km = float(max(0.0, req.Kilometre))
        # Sabit KM ızgarası → isotonic (azalan) eğri → istenen km'ye lineer interpolasyon.
        km_grid = [
            0.0, 5000.0, 10000.0, 20000.0, 30000.0, 40000.0, 50000.0,
            60000.0, 80000.0, 100000.0, 120000.0, 140000.0, 160000.0,
            180000.0, 200000.0, 250000.0, 300000.0, 400000.0,
        ]
        raw_on_grid = [_predict_at_km(k) for k in km_grid]
        isotonic: list[float] = []
        last_price = float("inf")
        for p in raw_on_grid:
            p = min(p, last_price)
            isotonic.append(p)
            last_price = p

        if km <= km_grid[0]:
            price = isotonic[0]
        elif km >= km_grid[-1]:
            price = isotonic[-1]
        else:
            price = isotonic[-1]
            for i in range(len(km_grid) - 1):
                k0, k1 = km_grid[i], km_grid[i + 1]
                if k0 <= km <= k1:
                    if k1 == k0:
                        price = isotonic[i]
                    else:
                        t = (km - k0) / (k1 - k0)
                        price = isotonic[i] + t * (isotonic[i + 1] - isotonic[i])
                    break
        price = max(0.0, float(price))
        
        # --- HARD SANITY CHECKS (Safety Guardrails) ---
        # 1. Floor limit: Even a 30-year-old high-km car has a scrap/parts value.
        MIN_PRICE_FLOOR = 150000.0
        if price < MIN_PRICE_FLOOR:
            price = MIN_PRICE_FLOOR
            
        # 2. Cap limit: Prevent absurdly high predictions
        MAX_PRICE_CAP = 50000000.0
        if price > MAX_PRICE_CAP:
            price = MAX_PRICE_CAP
        # ----------------------------------------------

        mae = MODEL_MAE or 0.0
        # Confidence Interval (+/- 4% to simulate market flexibility)
        low = price * 0.96
        high = price * 1.04
        
        # Outlier Detection
        is_outlier = bool((req.Yil < 2005) or (req.Kilometre > 350000))
        outlier_warning = "Bu araç için piyasada yeterli veri bulunmamaktadır, tahmin sapabilir." if is_outlier else ""

        # Explainable AI (Reasoning Heuristic)
        age_years = max(0, 2026 - req.Yil)
        km_impact_val = - (price * 0.01 * (req.Kilometre / 10000.0))
        age_impact_val = - (price * 0.02 * age_years)
        damage_impact_val = 0.0
        if hasar['Has_Tramer'] > 0 or hasar['Has_Boya'] > 0 or hasar['Has_Degisen'] > 0:
            damage_impact_val = - (price * 0.05)
            
        base_average = price - km_impact_val - age_impact_val - damage_impact_val
        
        explanation = {
            "base_average": base_average,
            "km_impact": km_impact_val,
            "age_impact": age_impact_val,
            "damage_impact": damage_impact_val
        }

        req_id = req.request_id or request.headers.get("x-request-id") or str(uuid.uuid4())

        background_tasks.add_task(
            log_prediction,
            brand=req.Marka,
            model=req.Seri,
            trim=req.Model,
            year=req.Yil,
            km=req.Kilometre,
            fuel_type=req.Yakit_Tipi,
            gear_type=req.Vites_Tipi,
            boya_degisen=hasar['Boya_Durumu'],
            predicted_price=price,
            request_id=req_id,
            client_ip=_client_ip(request),
        )

        return {
            "status": "success",
            "predicted_price": price,
            "currency": "TRY",
            "confidence_low": low,
            "confidence_high": high,
            "mae": mae,
            "model_r2": MODEL_R2,
            "model_mape": MODEL_MAPE,
            "features_used": len(all_features),
            "request_id": req_id,
            "km_monotonic": True,
            "is_outlier": is_outlier,
            "outlier_warning": outlier_warning,
            "explanation": explanation,
            "hasar": {
                "Boya_Durumu": hasar["Boya_Durumu"],
                "Has_Boya": hasar["Has_Boya"],
                "Has_Degisen": hasar["Has_Degisen"],
                "Has_Tramer": hasar["Has_Tramer"],
                "Tramer_TL": hasar["Tramer_TL"],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/predictions/history")
@app.get("/predictions/history")
def predictions_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    brand: Optional[str] = Query(None),
):
    """Geçmiş tahmin logları (pagination)."""
    db = SessionLocal()
    try:
        q = db.query(PredictionLog).order_by(PredictionLog.created_at.desc())
        if brand:
            q = q.filter(PredictionLog.brand.ilike(brand))
        total = q.count()
        rows = q.offset(offset).limit(limit).all()
        return {
            "status": "success",
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": [
                {
                    "id": str(r.id),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "brand": r.brand,
                    "model": r.model,
                    "trim": r.trim,
                    "year": r.year,
                    "km": r.km,
                    "fuel_type": r.fuel_type,
                    "gear_type": r.gear_type,
                    "boya_degisen": r.boya_degisen,
                    "boya_degisen_count": r.boya_degisen_count,
                    "predicted_price": r.predicted_price,
                    "request_id": r.request_id,
                    "client_ip": r.client_ip,
                }
                for r in rows
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/cars")
def get_cars(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    try:
        with engine.connect() as conn:
            q = text("""
                SELECT "Baslik","Fiyat","Kilometre","Yil" AS "Yıl",
                       "Kasa_Tipi" AS "Kasa Tipi",
                       "Vites_Tipi" AS "Vites Tipi",
                       "Yakit_Tipi" AS "Yakıt Tipi",
                       "Renk", "Marka", "Seri"
                FROM araclar_clean
                ORDER BY "Fiyat" DESC NULLS LAST
                LIMIT :limit OFFSET :offset
            """)
            rows = conn.execute(q, {"limit": limit, "offset": offset}).fetchall()
            cars = [dict(r._mapping) for r in rows]
        return {"status": "success", "count": len(cars), "data": cars}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Flutter Web (SPA) — aynı origin'den mobil/desktop ───
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

_web_path = Path(WEB_DIR)


def _register_web_routes():
    if not _web_path.is_dir() or not (_web_path / "index.html").is_file():
        print(f"⚠️ Web build yok ({_web_path}) — sadece API. "
              f"Önce: cd frontend && flutter build web --release")

        @app.get("/")
        def root_api_only():
            return _health_payload()

        return

    assets_dir = _web_path / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="flutter_assets")

    canvaskit = _web_path / "canvaskit"
    if canvaskit.is_dir():
        app.mount("/canvaskit", StaticFiles(directory=str(canvaskit)), name="canvaskit")

    @app.get("/")
    async def spa_index():
        return FileResponse(_web_path / "index.html")

    @app.get("/{file_path:path}")
    async def spa_fallback(file_path: str):
        # API yollarına dokunma
        if file_path.startswith("api/") or file_path.startswith("docs") or file_path.startswith("openapi"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = (_web_path / file_path).resolve()
        try:
            candidate.relative_to(_web_path.resolve())
        except ValueError:
            raise HTTPException(status_code=404, detail="Not found")
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_web_path / "index.html")

    print(f"✅ Flutter web servis ediliyor: {_web_path}")


_register_web_routes()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
