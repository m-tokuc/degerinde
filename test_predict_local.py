from main import app
from fastapi.testclient import TestClient

client = TestClient(app)
payload = {
  "Yil": 2018,
  "Kilometre": 50000,
  "Marka": "Renault",
  "Seri": "Clio",
  "Model": "1.5 dCi Touch",
  "Vites_Tipi": "Manuel",
  "Yakit_Tipi": "Dizel",
  "Kasa_Tipi": "Hatchback 5 Kapı",
  "Tramer_TL": 0,
  "sol_on_camurluk": 0,
  "kaput": 0,
  "sag_on_camurluk": 0,
  "tavan": 0,
  "sol_on_kapi": 0,
  "sag_on_kapi": 0,
  "sol_arka_kapi": 0,
  "sag_arka_kapi": 0,
  "sol_arka_camurluk": 0,
  "bagaj": 0,
  "sag_arka_camurluk": 0,
  "on_tampon": 0,
  "arka_tampon": 0
}
response = client.post("/api/predict", json=payload)
print(response.status_code)
print(response.json())
