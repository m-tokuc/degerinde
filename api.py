"""
Değerinde — Production API & MLOps Module
FastAPI router for predictions with Pydantic validation, OOD handling, and Explainability.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field
import pandas as pd
import uuid

from explainability import PriceExplainer
from app_db import log_prediction
from ui_formatter import format_prediction_for_ui

router = APIRouter()
explainer = PriceExplainer()

class PredictionRequest(BaseModel):
    brand: str = Field(..., title="Marka", min_length=2)
    model: str = Field(..., title="Seri", min_length=1)
    trim: str = Field(..., title="Model/Paket")
    year: int = Field(..., ge=1990, le=2026, description="1990-2026 arası geçerli")
    km: float = Field(..., ge=0, le=1000000)
    fuel_type: str = Field(default="Benzin")
    gear_type: str = Field(default="Manuel")
    body_type: str = Field(default="Hatchback")
    color: str = Field(default="Belirtilmemiş")
    seller: str = Field(default="Belirtilmemiş")
    warranty: str = Field(default="Belirtilmemiş")
    cylinders: str = Field(default="4")
    seats: str = Field(default="5")
    engine_cc: float = Field(default=1400.0)
    engine_hp: float = Field(default=90.0)
    tramer_tl: float = Field(default=0.0)
    boya_durumu: str = Field(default="Boyasız")
    has_boya: float = Field(default=0.0)
    has_degisen: float = Field(default=0.0)
    has_tramer: float = Field(default=0.0)

# Fast OOD checking based on top brands. 
# In a real scenario, this would check against the DB or the pipeline's categories.
KNOWN_BRANDS = {
    "Renault", "Fiat", "Volkswagen", "Ford", "Opel", "Toyota", "Peugeot", "BMW", 
    "Hyundai", "Audi", "Mercedes-Benz", "Honda", "Citroen", "Dacia", "Skoda", "Nissan", 
    "Seat", "Kia", "Chevrolet", "Volvo", "Subaru", "Suzuki", "Mini", "Mitsubishi", 
    "Alfa Romeo", "Mazda", "Chery", "Porsche", "Jaguar", "Jeep", "Geely", "Lada"
}

@router.post("/predict_v2")
async def predict_price(req: PredictionRequest, background_tasks: BackgroundTasks, request: Request):
    if not explainer.is_ready:
        raise HTTPException(status_code=500, detail="Fiyat tahmin motoru şu an meşgul veya yüklenemedi.")
    
    # 1. Out-of-Distribution (OOD) Handling
    if req.brand not in KNOWN_BRANDS:
        # Prevent crashes from entirely unknown brands by returning a clean 400 error.
        raise HTTPException(status_code=400, detail=f"'{req.brand}' markası için yeterli piyasa verimiz bulunmuyor.")

    # 2. Derived Features
    arac_yasi = max(0, 2026 - req.year)
    safe_age = 1 if arac_yasi == 0 else arac_yasi
    yillik_km = req.km / safe_age
    
    # 3. Model DataFrame Construction
    df_input = pd.DataFrame([{
        "Marka": req.brand,
        "Seri": req.model,
        "Model": req.trim,
        "Kasa_Tipi": req.body_type,
        "Vites_Tipi": req.gear_type,
        "Yakit_Tipi": req.fuel_type,
        "Cekis": "Önden Çekiş",
        "Renk": req.color,
        "Kimden": req.seller,
        "Garanti_Durumu": req.warranty,
        "Silindir_Sayisi": req.cylinders,
        "Koltuk_Sayisi": req.seats,
        "Boya_Durumu": req.boya_durumu,
        "Arac_Yasi": float(arac_yasi),
        "Kilometre": req.km,
        "Yillik_Ortalama_KM": yillik_km,
        "Motor_Hacmi_cc": req.engine_cc,
        "Motor_Gucu_hp": req.engine_hp,
        "Tramer_TL": req.tramer_tl,
        "Has_Boya": req.has_boya,
        "Has_Degisen": req.has_degisen,
        "Has_Tramer": req.has_tramer
    }])
    
    # 4. Explainable AI Inference
    explanation = explainer.explain_prediction(df_input)
    if "error" in explanation:
        raise HTTPException(status_code=500, detail=explanation["error"])
        
    final_price = explanation["final_price"]
    
    # 5. Database Logging for Drift Monitoring
    client_ip = request.client.host if request.client else "unknown"
    req_id = "v2-" + str(uuid.uuid4())[:8]
    
    background_tasks.add_task(
        log_prediction,
        brand=req.brand,
        model=req.model,
        trim=req.trim,
        year=req.year,
        km=req.km,
        fuel_type=req.fuel_type,
        gear_type=req.gear_type,
        boya_degisen=req.boya_durumu,
        predicted_price=final_price,
        shap_explanation=explanation,
        request_id=req_id,
        client_ip=client_ip
    )
    
    # 6. UI Formatter Mapping
    ui_formatted = format_prediction_for_ui(explanation)
    
    return {
        "success": True,
        "request_id": req_id,
        "prediction": final_price,
        "explanation": explanation,
        "ui_formatted": ui_formatted
    }
