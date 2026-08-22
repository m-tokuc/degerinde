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

from explainability import PriceExplainer
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

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Logger Yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("degerinde")

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Değerinde AI API", version="5.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

import json
model_metadata = {}

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
            
        meta_path = os.path.join(os.path.dirname(MODEL_PATH), "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                model_metadata = json.load(f)
                
        is_model_loaded = True
        logger.info(f"✅ Model yüklendi: {MODEL_PATH}")
        explainer = PriceExplainer(model_path=MODEL_PATH)
    else:
        logger.warning(f"⚠️ Model dosyası bulunamadı: {MODEL_PATH}")
        explainer = None
except Exception as e:
    logger.error(f"❌ Model yükleme hatası: {e}")

# Veritabanı ve Önbellek
_combo_cache = None
FOCUS_BRANDS = []

@app.post("/api/admin/reload-model")
def reload_model():
    global model, is_model_loaded, explainer, model_metadata
    try:
        if not os.path.exists(MODEL_PATH):
            raise HTTPException(status_code=404, detail="Model dosyası bulunamadı.")
            
        loaded_data = joblib.load(MODEL_PATH)
        if isinstance(loaded_data, dict) and "model" in loaded_data:
            model = loaded_data["model"]
        else:
            model = loaded_data
        
        meta_path = os.path.join(os.path.dirname(MODEL_PATH), "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                model_metadata = json.load(f)

        is_model_loaded = True
        explainer = PriceExplainer(model_path=MODEL_PATH)
        logger.info(f"✅ Model yeniden yüklendi: {MODEL_PATH}")
        return {"status": "success", "message": "Model başarıyla güncellendi."}
    except Exception as e:
        logger.error(f"❌ Model reload hatası: {e}")
        raise HTTPException(status_code=500, detail="Model güncellenirken sunucu hatası oluştu.")

def load_data_cache():
    global _combo_cache
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            query = text("SELECT * FROM araclar_clean WHERE \"Marka\" IS NOT NULL")
            _combo_cache = pd.read_sql(query, conn)
            logger.info(f"CRITICAL: Usable (Marka+Seri): {len(_combo_cache)}")
    except Exception as e:
        logger.warning(f"Veritabanı hatası: {e}. Yedeğe geçiliyor...")
        if os.path.exists("dropdown_cache.csv"):
            _combo_cache = pd.read_csv("dropdown_cache.csv")
            logger.info(f"dropdown_cache.csv hizlica yüklendi. {len(_combo_cache)} kayıt.")
        elif os.path.exists("araba_verileri.jsonl"):
            _combo_cache = pd.read_json("araba_verileri.jsonl", lines=True)
            rename_map = {
                "Yıl": "Yil", "Vites Tipi": "Vites_Tipi", "Yakıt Tipi": "Yakit_Tipi",
                "Kasa Tipi": "Kasa_Tipi", "Motor Hacmi": "Motor_Hacmi", "Motor Gücü": "Motor_Gucu",
                "Garanti Durumu": "Garanti_Durumu", "Çekiş": "Cekis"
            }
            _combo_cache = _combo_cache.rename(columns=rename_map)
            logger.info(f"araba_verileri.jsonl hizlica yüklendi. {len(_combo_cache)} kayıt.")
        elif os.path.exists("seed_data.jsonl"):
            _combo_cache = pd.read_json("seed_data.jsonl", lines=True)
            rename_map = {
                "Yıl": "Yil",
                "Vites Tipi": "Vites_Tipi",
                "Yakıt Tipi": "Yakit_Tipi",
                "Kasa Tipi": "Kasa_Tipi",
                "Motor Hacmi": "Motor_Hacmi",
                "Motor Gücü": "Motor_Gucu",
                "Garanti Durumu": "Garanti_Durumu",
                "Çekiş": "Cekis"
            }
            _combo_cache = _combo_cache.rename(columns=rename_map)
            logger.info(f"seed_data.jsonl hizlica yüklendi. {len(_combo_cache)} kayıt.")
            if "Kilometre" in _combo_cache.columns:
                _combo_cache["Yil"] = pd.to_numeric(_combo_cache["Yil"], errors="coerce")

    if _combo_cache is not None and "Yıl" in _combo_cache.columns and "Yil" not in _combo_cache.columns:
        _combo_cache = _combo_cache.rename(columns={"Yıl": "Yil"})
    if _combo_cache is not None and "Marka" in _combo_cache.columns:
        _combo_cache["Marka"] = _combo_cache["Marka"].replace({"Citroen": "Citroën"})

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

class AutoFillSpecsRequest(BaseModel):
    Marka: str
    Seri: str
    Model: str
    Kasa_Tipi: Optional[str] = None


class CarFeaturesRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    Kilometre: Optional[int] = 100000
    Yil: Optional[int] = 2015
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

    if all(p is not None for p in parts):
        if boyali_sayisi > 0 or degisen_sayisi > 0:
            has_boya = 1 if boyali_sayisi > 0 else 0
            has_degisen = 1 if degisen_sayisi > 0 else 0
            has_tramer = 1 if tramer > 0 else 0

            if has_boya and has_degisen:
                status = "Boyalı+Değişen"
            elif has_degisen:
                status = "Değişenli"
            else:
                status = "Boyalı"

            return {
                "Boya_Durumu": status,
                "Has_Boya": has_boya,
                "Has_Degisen": has_degisen,
                "Has_Tramer": has_tramer,
                "Tramer_TL": tramer,
                "kaput": req.kaput,
                "tavan": req.tavan,
                "bagaj": req.bagaj,
                "sol_on_camurluk": req.sol_on_camurluk,
                "sag_on_camurluk": req.sag_on_camurluk,
                "sol_arka_camurluk": req.sol_arka_camurluk,
                "sag_arka_camurluk": req.sag_arka_camurluk,
                "sol_on_kapi": req.sol_on_kapi,
                "sag_on_kapi": req.sag_on_kapi,
                "sol_arka_kapi": req.sol_arka_kapi,
                "sag_arka_kapi": req.sag_arka_kapi,
                "on_tampon": req.on_tampon,
                "arka_tampon": req.arka_tampon,
            }
        else:
            # All provided parts are Orijinal
            has_tramer = 1 if tramer > 0 else 0
            return {
                "Boya_Durumu": "Tramerli" if has_tramer else "Temiz",
                "Has_Boya": 0,
                "Has_Degisen": 0,
                "Has_Tramer": has_tramer,
                "Tramer_TL": tramer,
                "kaput": req.kaput,
                "tavan": req.tavan,
                "bagaj": req.bagaj,
                "sol_on_camurluk": req.sol_on_camurluk,
                "sag_on_camurluk": req.sag_on_camurluk,
                "sol_arka_camurluk": req.sol_arka_camurluk,
                "sag_arka_camurluk": req.sag_arka_camurluk,
                "sol_on_kapi": req.sol_on_kapi,
                "sag_on_kapi": req.sag_on_kapi,
                "sol_arka_kapi": req.sol_arka_kapi,
                "sag_arka_kapi": req.sag_arka_kapi,
                "on_tampon": req.on_tampon,
                "arka_tampon": req.arka_tampon,
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
            "kaput": 0, "tavan": 0, "bagaj": 0, 
            "sol_on_camurluk": 0, "sag_on_camurluk": 0,
            "sol_arka_camurluk": 0, "sag_arka_camurluk": 0,
            "sol_on_kapi": 0, "sag_on_kapi": 0,
            "sol_arka_kapi": 0, "sag_arka_kapi": 0,
            "on_tampon": 0, "arka_tampon": 0,
        }

    label = (req.Boya_Degisen or "Belirsiz").strip()
    label_map = {
        "Temiz": {"Boya_Durumu": "Temiz", "Has_Boya": 0, "Has_Degisen": 0, "Has_Tramer": 0},
        "Belirsiz": {"Boya_Durumu": "Belirsiz", "Has_Boya": 0, "Has_Degisen": 0, "Has_Tramer": 0},
        "Belirtilmemiş": {"Boya_Durumu": "Belirsiz", "Has_Boya": 0, "Has_Degisen": 0, "Has_Tramer": 0},
        "Boyalı": {"Boya_Durumu": "Boyalı", "Has_Boya": 1, "Has_Degisen": 0, "Has_Tramer": 0},
        "Değişenli": {"Boya_Durumu": "Değişenli", "Has_Boya": 0, "Has_Degisen": 1, "Has_Tramer": 0},
        "Boyalı+Değişen": {"Boya_Durumu": "Boyalı+Değişen", "Has_Boya": 1, "Has_Degisen": 1, "Has_Tramer": 0},
        "Lokal Boyalı": {"Boya_Durumu": "Lokal Boyalı", "Has_Boya": 1, "Has_Degisen": 0, "Has_Tramer": 0},
        "Tramerli": {"Boya_Durumu": "Tramerli", "Has_Boya": 0, "Has_Degisen": 0, "Has_Tramer": 1}
    }
    
    if label in label_map:
        out = dict(label_map[label])
        if tramer > 0:
            out["Has_Tramer"] = 1
            if out["Boya_Durumu"] == "Belirsiz":
                out["Boya_Durumu"] = "Tramerli"
        out["Tramer_TL"] = tramer
    else:
        # Fallback for complex strings
        out = parse_hasar_flags(label, tramer_tl=tramer) if "parse_hasar_flags" in globals() else {"Boya_Durumu": "Belirsiz", "Has_Boya": 0, "Has_Degisen": 0, "Has_Tramer": 0}
        out["Tramer_TL"] = tramer
        
    # Ensure 13 part keys always exist to avoid KeyError 'kaput'
    for _part in ["kaput", "tavan", "bagaj", "sol_on_camurluk", "sag_on_camurluk",
                  "sol_arka_camurluk", "sag_arka_camurluk", "sol_on_kapi", "sag_on_kapi",
                  "sol_arka_kapi", "sag_arka_kapi", "on_tampon", "arka_tampon"]:
        out.setdefault(_part, 0)
        
    return out


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

    df_for_years = _combo_cache
    if req.Seri and req.Seri != "Belirtilmemiş":
        df_for_years = _combo_cache[_combo_cache["Seri"] == req.Seri]
    elif req.Marka and req.Marka != "Belirtilmemiş":
        df_for_years = _combo_cache[_combo_cache["Marka"] == req.Marka]

    yillar_list = []
    if "Yil" in df_for_years.columns:
        yillar_list = unique_int_sorted(df_for_years["Yil"])
    elif "Yıl" in df_for_years.columns:
        yillar_list = unique_int_sorted(df_for_years["Yıl"])
        
    if len(yillar_list) >= 2:
        # Interpolate between min and max to ensure no gaps
        yillar_list = list(range(max(yillar_list), min(yillar_list) - 1, -1))

    return {
        "markalar": unique_sorted(_combo_cache["Marka"]),
        "seriler": unique_sorted(df["Seri"]) if "Seri" in df else [],
        "modeller": unique_sorted(df["Model"]) if "Model" in df else [],
        "yillar": yillar_list,
        "vitesler": unique_sorted(_combo_cache["Vites_Tipi"]) if "Vites_Tipi" in _combo_cache else [],
        "yakitlar": unique_sorted(_combo_cache["Yakit_Tipi"]) if "Yakit_Tipi" in _combo_cache else [],
        "kasalar": unique_sorted(_combo_cache["Kasa_Tipi"]) if "Kasa_Tipi" in _combo_cache else [],
        "renkler": unique_sorted(_combo_cache["Renk"]) if "Renk" in _combo_cache else [],
        "kimden": unique_sorted(_combo_cache["Kimden"]) if "Kimden" in _combo_cache else [],
        "garanti_durumu": unique_sorted(_combo_cache["Garanti_Durumu"]) if "Garanti_Durumu" in _combo_cache else [],
    }

@app.post("/api/auto_fill_specs")
def auto_fill_specs(req: AutoFillSpecsRequest):
    if _combo_cache is None or len(_combo_cache) == 0:
        return {}

    df = _combo_cache[
        (_combo_cache["Marka"] == req.Marka) & 
        (_combo_cache["Seri"] == req.Seri) & 
        (_combo_cache["Model"] == req.Model)
    ]
    
    if df.empty:
        return {}
        
    res = {}
    # Sadece Belirtilmemiş olmayan geçerli değerlerin modunu (en çok tekrar edeni) al
    for col in ["Motor_Hacmi", "Motor_Gucu", "Yakit_Tipi", "Vites_Tipi", "Kasa_Tipi", "Silindir_Sayisi", "Koltuk_Sayisi", "Cekis"]:
        if col in df.columns:
            valid = df[col].replace("Belirtilmemiş", pd.NA).dropna()
            if not valid.empty:
                res[col] = valid.mode().iloc[0]
                
    return res

@app.post("/api/predict")
@limiter.limit("30/minute")
def predict(req: CarFeaturesRequest, request: Request):
    if not is_model_loaded or model is None:
        raise HTTPException(status_code=503, detail="Yapay zeka modeli henüz yüklenmedi.")

    # Sanity Checks (Mantıksal Sınır Korumaları)
    if req.Yil is None or req.Yil < 1990:
        req.Yil = 1990
    elif req.Yil > 2026:
        req.Yil = 2026
        
    if req.Kilometre is None or req.Kilometre < 0:
        req.Kilometre = 0
    elif req.Kilometre > 1000000:
        req.Kilometre = 1000000

    hasar = _resolve_hasar(req)
    arac_yasi = max(0, 2026 - req.Yil)
    yillik_km = req.Kilometre / max(1, arac_yasi)

    # Aşama 2: Yapay Zeka Boşluk Doldurma (Imputation via Mode)
    motor_hacmi = req.Motor_Hacmi_cc
    motor_gucu = req.Motor_Gucu_hp
    
    if (motor_hacmi is None or motor_hacmi == 0) or (motor_gucu is None or motor_gucu == 0):
        if _combo_cache is not None and not _combo_cache.empty:
            df_fallback = _combo_cache[
                (_combo_cache["Marka"] == req.Marka) & 
                (_combo_cache["Seri"] == req.Seri)
            ]
            if req.Model and req.Model != "Belirtilmemiş":
                df_model = df_fallback[df_fallback["Model"] == req.Model]
                if not df_model.empty:
                    df_fallback = df_model
                    
            if not df_fallback.empty:
                if (motor_hacmi is None or motor_hacmi == 0) and "Motor_Hacmi" in df_fallback.columns:
                    valid_h = df_fallback["Motor_Hacmi"].replace("Belirtilmemiş", pd.NA).dropna()
                    if not valid_h.empty:
                        # "1461 cc" gibi string'den float çıkarma
                        h_mode = valid_h.mode().iloc[0]
                        import re
                        m = re.search(r"(\d+(?:\.\d+)?)", str(h_mode))
                        if m:
                            motor_hacmi = float(m.group(1))
                            
                if (motor_gucu is None or motor_gucu == 0) and "Motor_Gucu" in df_fallback.columns:
                    valid_g = df_fallback["Motor_Gucu"].replace("Belirtilmemiş", pd.NA).dropna()
                    if not valid_g.empty:
                        g_mode = valid_g.mode().iloc[0]
                        import re
                        m = re.search(r"(\d+(?:\.\d+)?)", str(g_mode))
                        if m:
                            motor_gucu = float(m.group(1))

    # Hala null ise fallback (eski uydurma 1600 yerine en azından 1300 mantıklı bir araç)
    if motor_hacmi is None or motor_hacmi == 0: motor_hacmi = 1300.0
    if motor_gucu is None or motor_gucu == 0: motor_gucu = 90.0

    input_data = {
        "Marka": req.Marka,
        "Seri": req.Seri,
        "Model": req.Model,
        "Kasa Tipi": req.Kasa_Tipi,
        "Vites Tipi": req.Vites_Tipi,
        "Yakıt Tipi": req.Yakit_Tipi,
        "Çekiş": req.Cekis,
        "Renk": req.Renk,
        "Kimden": req.Kimden,
        "Garanti Durumu": req.Garanti_Durumu,
        "Silindir Sayısı": str(req.Silindir_Sayisi or "4"),
        "Koltuk Sayısı": str(req.Koltuk_Sayisi or "5"),
        "Boya_Durumu": hasar["Boya_Durumu"],
        "Yıl": req.Yil,
        "Kilometre": req.Kilometre,
        "Motor_Hacmi_cc": motor_hacmi,
        "Motor_Gucu_hp": motor_gucu,
        "Tramer_TL": hasar["Tramer_TL"],
        "Has_Boya": hasar["Has_Boya"],
        "Has_Degisen": hasar["Has_Degisen"],
        "Has_Tramer": hasar["Has_Tramer"],
        "kaput": hasar["kaput"],
        "tavan": hasar["tavan"],
        "bagaj": hasar["bagaj"],
        "sol_on_camurluk": hasar["sol_on_camurluk"],
        "sag_on_camurluk": hasar["sag_on_camurluk"],
        "sol_arka_camurluk": hasar["sol_arka_camurluk"],
        "sag_arka_camurluk": hasar["sag_arka_camurluk"],
        "sol_on_kapi": hasar["sol_on_kapi"],
        "sag_on_kapi": hasar["sag_on_kapi"],
        "sol_arka_kapi": hasar["sol_arka_kapi"],
        "sag_arka_kapi": hasar["sag_arka_kapi"],
        "on_tampon": hasar["on_tampon"],
        "arka_tampon": hasar["arka_tampon"],
    }

    df_in = pd.DataFrame([input_data])

    try:
        pred = float(model.predict(df_in)[0])
    except Exception as e:
        logger.error(f"Tahmin hatası: {e}")
        raise HTTPException(status_code=500, detail="Fiyat tahmin edilirken sistemsel bir hata oluştu.")

    # Mantık Sınırları
    pred = max(100_000, min(15_000_000, pred))
    fiyat = int(round(pred, -3))
    min_fiyat = int(round(fiyat * 0.94, -3))
    max_fiyat = int(round(fiyat * 1.06, -3))

    # SHAP Analizi
    fiyat_etkenleri = []
    if 'explainer' in globals() and explainer and explainer.is_ready:
        try:
            shap_result = explainer.explain_prediction(df_in)
            if "error" not in shap_result:
                mapping = {
                    "brand_model_impact": "Marka ve Model Değeri",
                    "km_impact": "Kilometre Etkisi",
                    "age_impact": "Araç Yaşı Etkisi",
                    "gear_engine_impact": "Motor ve Donanım Etkisi",
                    "damage_impact": "Hasar / Ekspertiz Durumu",
                    "other_impact": "Diğer Faktörler"
                }
                for key, val in shap_result.items():
                    if key in mapping and abs(val) > 100:
                        fiyat_etkenleri.append({
                            "isim": mapping[key],
                            "miktar": abs(int(val)),
                            "yon": "pozitif" if val > 0 else "negatif"
                        })
                # Etki miktarına göre sırala
                fiyat_etkenleri.sort(key=lambda x: x["miktar"], reverse=True)
        except Exception as e:
            logger.warning(f"SHAP hatası: {e}")

    # ===== SANITY POST-PROCESSING (Mantık Tutarlılık Zorlaması) =====
    # Modelin kategorik değişken etkileşimleri yüzünden Tramer veya KM arttığında fiyatı 
    # bazen artırmasını (Monotonic Constraint'in kategoriler arası bypass edilmesini) önler.
    manuel_deger_kaybi = 0
    
    # 1. Aşırı KM Değer Kaybı
    if req.Kilometre > 100000:
        km_carpan = min(0.15, ((req.Kilometre - 100000) / 100000) * 0.02)
        manuel_deger_kaybi += int(fiyat * km_carpan)
        
    # 2. Değişen / Boya Kaybı
    if hasar["Has_Degisen"]:
        manuel_deger_kaybi += int(fiyat * 0.04)
    elif hasar["Has_Boya"]:
        manuel_deger_kaybi += int(fiyat * 0.01)
        
    # 3. Yüksek Tramer Kaybı
    if hasar["Tramer_TL"] > 5000:
        # Tramer'in maksimum %50'si kadar etki etsin, ama aracın fiyatının %15'ini geçmesin
        tramer_kaybi = min(fiyat * 0.15, hasar["Tramer_TL"] * 0.5)
        manuel_deger_kaybi += int(tramer_kaybi)

    # Toplam kayıp aracın %30'unu geçemez (Güvenlik)
    manuel_deger_kaybi = int(min(fiyat * 0.30, manuel_deger_kaybi))

    if manuel_deger_kaybi > 0:
        fiyat -= manuel_deger_kaybi
        min_fiyat = int(round(fiyat * 0.94, -3))
        max_fiyat = int(round(fiyat * 1.06, -3))
        
        # SHAP açıklamasını (UI) yeni fiyata göre dengele
        damage_found = False
        for e in fiyat_etkenleri:
            if e["isim"] in ["Hasar / Ekspertiz Durumu", "Kilometre Etkisi"]:
                e["miktar"] += manuel_deger_kaybi
                e["yon"] = "negatif"
                damage_found = True
                break
        
        if not damage_found:
            fiyat_etkenleri.append({
                "isim": "Hasar / Ekspertiz Durumu",
                "miktar": manuel_deger_kaybi,
                "yon": "negatif"
            })
    # ================================================================

    # Veritabanına Loglama
    try:
        log_prediction(
            brand=req.Marka,
            model=req.Seri,
            trim=req.Model,
            year=req.Yil,
            km=req.Kilometre,
            fuel_type=req.Yakit_Tipi,
            gear_type=req.Vites_Tipi,
            boya_degisen=hasar["Boya_Durumu"],
            predicted_price=fiyat,
            shap_explanation={"fiyat_etkenleri": fiyat_etkenleri},
            request_id=req.request_id,
            client_ip=request.client.host if request.client else "127.0.0.1"
        )
    except Exception as e:
        logger.warning(f"Tahmin loglanamadı: {e}")


    # Gerçek model metriklerini dogrudan model_data'dan ök
    real_r2 = model_metadata.get("r2", MODEL_R2) if model_metadata else MODEL_R2
    real_mae = model_metadata.get("mae", MODEL_MAE) if model_metadata else MODEL_MAE

    # Dinamik güven skoru: düşmesini (yüksek km, eski araç) yansıt
    guven = 95
    if req.Kilometre > 200_000:
        guven -= 5
    if req.Yil < 2005:
        guven -= 5
    if hasar["Has_Degisen"] or hasar["Has_Tramer"]:
        guven -= 3
    guven = max(75, guven)

    return {
        "tahmini_fiyat": fiyat,
        "fiyat_araligi": {
            "min": min_fiyat,
            "max": max_fiyat
        },
        "hasar_analizi": hasar,
        "fiyat_etkenleri": fiyat_etkenleri,
        "guven_skoru": guven,
        "model_r2": round(real_r2, 4),
        "mae": int(real_mae),
        "features_used": 34
    }
