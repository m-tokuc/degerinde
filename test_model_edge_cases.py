from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

print("=" * 60)
print("DEĞERİNDE - MODEL STRESS TEST & EDGE CASES")
print("=" * 60)

test_cases = [
    {
        "name": "Very old, high KM standard car",
        "payload": {
            "Marka": "Dacia",
            "Seri": "Logan",
            "Model": "1.4 Ambiance",
            "Yil": 2006,
            "Kilometre": 300000,
            "Vites_Tipi": "Manuel",
            "Yakit_Tipi": "Benzin",
            "Boya_Degisen": "Boyalı",
        }
    },
    {
        "name": "Brand new, zero KM luxury car",
        "payload": {
            "Marka": "BMW",
            "Seri": "3 Serisi",
            "Model": "320i M Sport",
            "Yil": 2024,
            "Kilometre": 0,
            "Vites_Tipi": "Otomatik",
            "Yakit_Tipi": "Benzin",
            "Boya_Degisen": "Boyasız / Tamamı Orijinal",
        }
    },
    {
        "name": "Average daily driver",
        "payload": {
            "Marka": "Renault",
            "Seri": "Megane",
            "Model": "1.5 dCi Touch",
            "Yil": 2017,
            "Kilometre": 120000,
            "Vites_Tipi": "Otomatik",
            "Yakit_Tipi": "Dizel",
            "Boya_Degisen": "Boyasız / Tamamı Orijinal",
        }
    },
    {
        "name": "Extreme mileage car",
        "payload": {
            "Marka": "Fiat",
            "Seri": "Linea",
            "Model": "1.3 Multijet Active Plus",
            "Yil": 2012,
            "Kilometre": 800000,
            "Vites_Tipi": "Manuel",
            "Yakit_Tipi": "Dizel",
            "Boya_Degisen": "Tramerli",
        }
    },
    {
        "name": "Very old, suspiciously low mileage",
        "payload": {
            "Marka": "Ford",
            "Seri": "Focus",
            "Model": "1.6 TDCi Trend",
            "Yil": 2005,
            "Kilometre": 20000,
            "Vites_Tipi": "Manuel",
            "Yakit_Tipi": "Dizel",
            "Boya_Degisen": "Boyasız / Tamamı Orijinal",
        }
    },
    {
        "name": "Ultra luxury hypercar logic test",
        "payload": {
            "Marka": "Porsche",
            "Seri": "911",
            "Model": "Carrera 4S",
            "Yil": 2023,
            "Kilometre": 5000,
            "Vites_Tipi": "Yarı Otomatik",
            "Yakit_Tipi": "Benzin",
            "Boya_Degisen": "Boyasız / Tamamı Orijinal",
        }
    }
]

for idx, tc in enumerate(test_cases, 1):
    print(f"\n[{idx}] {tc['name']}")
    print(f"INPUT: {tc['payload']['Yil']} {tc['payload']['Marka']} {tc['payload']['Seri']} {tc['payload']['Model']} | {tc['payload']['Kilometre']} KM | {tc['payload']['Boya_Degisen']}")
    
    response = client.post("/api/predict", json=tc['payload'])
    
    if response.status_code == 200:
        res = response.json()
        price = res.get("predicted_price", 0)
        low = res.get("confidence_low", 0)
        high = res.get("confidence_high", 0)
        is_outlier = res.get("is_outlier", False)
        warning = res.get("outlier_warning", "")
        
        print(f"OUTCOME:")
        print(f"  Price: {price:,.0f} TL")
        print(f"  Range: {low:,.0f} TL - {high:,.0f} TL")
        if is_outlier:
            print(f"  ⚠️ OUTLIER FLAGGED: {warning}")
        
        exp = res.get("explanation")
        if exp:
            print(f"  Explanation Breakdown:")
            print(f"    Base Avg: {exp.get('base_average',0):,.0f}")
            print(f"    KM Impact: {exp.get('km_impact',0):,.0f}")
            print(f"    Age Impact: {exp.get('age_impact',0):,.0f}")
            print(f"    Damage Impact: {exp.get('damage_impact',0):,.0f}")
    else:
        print(f"  ❌ ERROR {response.status_code}: {response.text}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
