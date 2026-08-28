import sys
import pandas as pd
from main import app
from fastapi.testclient import TestClient

app.state.limiter.enabled = False
client = TestClient(app)

car_pristine = {
    "Marka": "Renault", "Seri": "Belirtilmemiş", "Model": "Belirtilmemiş", 
    "Yil": 2015, "Kilometre": 100000, "Yakit_Tipi": "Benzin", "Vites_Tipi": "Otomatik", 
    "Kasa_Tipi": "Sedan", "Renk": "Beyaz", 
    "Tramer_TL": 0, "sol_on_camurluk": 0, "kaput": 0, "tavan": 0
}

car_damaged = car_pristine.copy()
car_damaged["Tramer_TL"] = 100000
car_damaged["sol_on_camurluk"] = 2
car_damaged["kaput"] = 2
car_damaged["tavan"] = 2

r1 = client.post("/api/predict", json=car_pristine).json()
r2 = client.post("/api/predict", json=car_damaged).json()

print(f"Pristine Price: {r1['tahmini_fiyat']}")
print(f"Damaged Price: {r2['tahmini_fiyat']}")
print(f"Pristine Tramer from API response (hasar_analizi): {r1['hasar_analizi'].get('Tramer_TL')}")
print(f"Damaged Tramer from API response (hasar_analizi): {r2['hasar_analizi'].get('Tramer_TL')}")
print(f"Pristine Has_Degisen: {r1['hasar_analizi'].get('Has_Degisen')}")
print(f"Damaged Has_Degisen: {r2['hasar_analizi'].get('Has_Degisen')}")
