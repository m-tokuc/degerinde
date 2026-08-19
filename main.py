import os
import re
import time
import json
import logging
from typing import Optional, List, Dict, Any

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from schema_clean import get_engine as get_db_engine
from app_db import log_prediction, SessionLocal as get_db_session_factory
from feature_engineering import (
    parse_tramer_tl,
    parse_hasar_flags,
    clean_damage_and_tramer,
    HIGH_CARDINALITY_CATS,
    LOW_CARDINALITY_CATS,
    NUMERICAL_FEATURES
)

# Logger Yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("degerinde")

app = FastAPI(title="Değerinde AI API", version="5.0")

# CORS Yapılandırması
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.getenv("MODEL_PATH", "car_price_model.pkl")
if not os.path.exists(MODEL_PATH) and os.path.exists("models/v2/model.pkl"):
    MODEL_PATH = "models/v2/model.pkl"

model = None
is_model_loaded = False
MODEL_R2 = 0.9559
MODEL_MAE = 67249
MODEL_MAPE = 8.65

# Model Yükleme
try:
    if os.path.exists(MODEL_PATH):
        loaded_data = joblib.load(MODEL_PATH)
        if isinstance(loaded_data, dict) and "model" in loaded_data:
            model = loaded_data["model"]
            MODEL_R2 = loaded_data.get("r2", MODEL_R2)
            MODEL_MAE = loaded_data.get("mae", MODEL_MAE)
            MODEL_MAPE = loaded_data.get("mape", MODEL_MAPE)
        else:
            model = loaded_data
        is_model_loaded = True
        logger.info(f"✅ Model yüklendi: {MODEL_PATH}")
    else:
        logger.warning(f"⚠️ Model dosyası bulunamadı: {MODEL_PATH}")
except Exception as e:
    logger.error(f"❌ Model yükleme hatası: {e}")

# Veritabanı ve Önbellek
_combo_cache = None
FOCUS_BRANDS = []

def load_data_cache():
    global _combo_cache
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            query = text("SELECT * FROM araclar_clean WHERE \"Marka\" IS NOT NULL")
            _combo_cache = pd.read_sql(query, conn)
            logger.info(f"CRITICAL: Usable (Marka+Seri): {len(_combo_cache)}")
    except Exception as e:
        logger.warning(f"Önbellek yüklenirken hata oluştu (seed verisi fallback): {e}")
        if os.path.exists("seed_data.jsonl"):
            _combo_cache = pd.read_json("seed_data.jsonl", lines=True)
            # Normalize Turkish column names from raw scrape format
            if "Yıl" in _combo_cache.columns and "Yil" not in _combo_cache.columns:
                _combo_cache = _combo_cache.rename(columns={"Yıl": "Yil"})
            if "Kilometre" in _combo_cache.columns:
                _combo_cache["Yil"] = pd.to_numeric(_combo_cache["Yil"], errors="coerce")
    # Always ensure 'Yil' column exists (not 'Yıl')
    if _combo_cache is not None and "Yıl" in _combo_cache.columns and "Yil" not in _combo_cache.columns:
        _combo_cache = _combo_cache.rename(columns={"Yıl": "Yil"})

@app.on_event("startup")
def startup_event():
    load_data_cache()
    try:
        from app_db import init_db
        init_db()
        logger.info("✅ predictions tablosu hazır.")
    except Exception as e:
        logger.error(f"DB init hatası: {e}")


# ─── Pydantic Şemaları ───
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
    Boya_Degisen: Optional[str] = 'Belirsiz'
    Has_Boya: Optional[int] = None
    Has_Degisen: Optional[int] = None
    Has_Tramer: Optional[int] = None
    # 13 Parçalı Ekspertiz Alanları
    sol_on_camurluk: Optional[int] = 0
    kaput: Optional[int] = 0
    sag_on_camurluk: Optional[int] = 0
    tavan: Optional[int] = 0
    sol_on_kapi: Optional[int] = 0
    sag_on_kapi: Optional[int] = 0
    sol_arka_kapi: Optional[int] = 0
    sag_arka_kapi: Optional[int] = 0
    sol_arka_camurluk: Optional[int] = 0
    bagaj: Optional[int] = 0
    sag_arka_camurluk: Optional[int] = 0
    on_tampon: Optional[int] = 0
    arka_tampon: Optional[int] = 0
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


def _resolve_hasar(req: CarFeaturesRequest) -> dict:
    tramer = parse_tramer_tl(req.Tramer_TL)

    parts = [
        req.sol_on_camurluk, req.kaput, req.sag_on_camurluk, req.tavan,
        req.sol_on_kapi, req.sag_on_kapi, req.sol_arka_kapi, req.sag_arka_kapi,
        req.sol_arka_camurluk, req.bagaj, req.sag_arka_camurluk,
        req.on_tampon, req.arka_tampon
    ]
    boyali_sayisi = sum(1 for p in parts if p in (1, 2))
    degisen_sayisi = sum(1 for p in parts if p == 3)

    if boyali_sayisi > 0 or degisen_sayisi > 0:
        has_boya = 1 if boyali_sayisi > 0 else 0
        has_degisen = 1 if degisen_sayisi > 0 else 0
        has_tramer = 1 if tramer > 0 else 0

        if has_boya and has_degisen:
            status = f"{degisen_sayisi} Değişen, {boyali_sayisi} Boyalı"
        elif has_degisen:
            status = f"{degisen_sayisi} Değişenli"
        else:
            status = f"{boyali_sayisi} Parça Boyalı"

        return {
            "Boya_Durumu": status,
            "Has_Boya": has_boya,
            "Has_Degisen": has_degisen,
            "Has_Tramer": has_tramer,
            "Tramer_TL": tramer,
        }

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
@app.get("/")
def root():
    return {"message": "Değerinde AI API çalışıyor", "version": "5.0"}

@app.get("/api/health")
def health():
    return {
        "status": "API çalışıyor",
        "model_loaded": is_model_loaded,
        "version": "5.0",
        "model_r2": MODEL_R2,
        "model_mae": MODEL_MAE,
        "model_mape": MODEL_MAPE,
    }

@app.get("/brands")
@app.get("/api/brands")
def get_brands():
    if _combo_cache is None or len(_combo_cache) == 0:
        return []
    return unique_sorted(_combo_cache["Marka"])

@app.post("/api/dynamic_options")
def dynamic_options(req: DynamicOptionsRequest):
    if _combo_cache is None or len(_combo_cache) == 0:
        return {"markalar": [], "seriler": [], "modeller": [], "yillar": [], "vitesler": [], "yakitlar": [], "kasalar": []}

    df = _combo_cache
    if req.Marka and req.Marka != "Belirtilmemiş":
        df = df[df["Marka"] == req.Marka]
    if req.Seri and req.Seri != "Belirtilmemiş":
        df = df[df["Seri"] == req.Seri]
    if req.Model and req.Model != "Belirtilmemiş":
        df = df[df["Model"] == req.Model]
    if req.Yil:
        yil_col = "Yil" if "Yil" in df.columns else "Yıl"
        if yil_col in df.columns:
            df = df[df[yil_col] == req.Yil]
    if req.Vites_Tipi and req.Vites_Tipi != "Belirtilmemiş":
        df = df[df["Vites_Tipi"] == req.Vites_Tipi]
    if req.Yakit_Tipi and req.Yakit_Tipi != "Belirtilmemiş":
        df = df[df["Yakit_Tipi"] == req.Yakit_Tipi]

    return {
        "markalar": unique_sorted(_combo_cache["Marka"]),
        "seriler": unique_sorted(df["Seri"]) if "Seri" in df else [],
        "modeller": unique_sorted(df["Model"]) if "Model" in df else [],
        "yillar": unique_int_sorted(df["Yil"]) if "Yil" in df.columns else (unique_int_sorted(df["Yıl"]) if "Yıl" in df.columns else []),
        "vitesler": unique_sorted(df["Vites_Tipi"]) if "Vites_Tipi" in df else [],
        "yakitlar": unique_sorted(df["Yakit_Tipi"]) if "Yakit_Tipi" in df else [],
        "kasalar": unique_sorted(df["Kasa_Tipi"]) if "Kasa_Tipi" in df else [],
    }

@app.post("/api/predict")
def predict(req: CarFeaturesRequest, request: Request):
    if not is_model_loaded or model is None:
        raise HTTPException(status_code=503, detail="Yapay zeka modeli henüz yüklenmedi.")

    hasar = _resolve_hasar(req)
    arac_yasi = max(0, 2026 - req.Yil)
    yillik_km = req.Kilometre / max(1, arac_yasi)

    input_data = {
        "Marka": req.Marka,
        "Seri": req.Seri,
        "Model": req.Model,
        "Kasa_Tipi": req.Kasa_Tipi,
        "Vites_Tipi": req.Vites_Tipi,
        "Yakit_Tipi": req.Yakit_Tipi,
        "Cekis": req.Cekis,
        "Renk": req.Renk,
        "Kimden": req.Kimden,
        "Garanti_Durumu": req.Garanti_Durumu,
        "Silindir_Sayisi": str(req.Silindir_Sayisi or "4"),
        "Koltuk_Sayisi": str(req.Koltuk_Sayisi or "5"),
        "Boya_Durumu": hasar["Boya_Durumu"],
        "Arac_Yasi": arac_yasi,
        "Kilometre": req.Kilometre,
        "Yillik_Ortalama_KM": yillik_km,
        "Motor_Hacmi_cc": req.Motor_Hacmi_cc or 1600.0,
        "Motor_Gucu_hp": req.Motor_Gucu_hp or 110.0,
        "Tramer_TL": hasar["Tramer_TL"],
        "Has_Boya": hasar["Has_Boya"],
        "Has_Degisen": hasar["Has_Degisen"],
        "Has_Tramer": hasar["Has_Tramer"],
    }

    df_in = pd.DataFrame([input_data])

    try:
        pred = float(model.predict(df_in)[0])
    except Exception as e:
        logger.error(f"Tahmin hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Fiyat tahmin edilirken hata: {str(e)}")

    # Mantık Sınırları
    pred = max(100_000, min(15_000_000, pred))
    fiyat = int(round(pred, -3))
    min_fiyat = int(round(fiyat * 0.94, -3))
    max_fiyat = int(round(fiyat * 1.06, -3))

    # Veritabanına Loglama
    try:
        session_factory = get_db_session_factory()
        with session_factory() as session:
            log_prediction(
                session=session,
                request_data=req.model_dump(),
                predicted_price=fiyat,
                client_ip=request.headers.get("x-forwarded-for", "127.0.0.1"),
                user_agent=request.headers.get("user-agent", "web"),
                model_version="v2"
            )
    except Exception as e:
        logger.warning(f"Tahmin loglanamadı: {e}")

    return {
        "tahmini_fiyat": fiyat,
        "fiyat_araligi": {
            "min": min_fiyat,
            "max": max_fiyat
        },
        "hasar_analizi": hasar,
        "guven_skoru": 94
    }
