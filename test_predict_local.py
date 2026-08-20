from main import app
from fastapi.testclient import TestClient

client = TestClient(app)
payload = {
  "Yil": 2015,
  "Kilometre": 34232,
  "Marka": "Dacia",
  "Seri": "Sandero",
  "Model": "0.9 TCe Stepway",
  "Vites_Tipi": "Düz",
  "Yakit_Tipi": "Benzin",
  "Kasa_Tipi": "Hatchback/5",
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
print(response.json())
