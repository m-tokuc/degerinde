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
  "Boya_Degisen": "Orijinal"
}
response = client.post("/api/predict", json=payload)
print(response.status_code)
print(response.json())
