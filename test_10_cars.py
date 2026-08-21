import requests
import json
import time

API_URL = "http://localhost:8000/api/predict"

test_cases = [
    {
        "name": "Normal Aile Arabası (Renault Megane)",
        "payload": {
            "Kilometre": 85000, "Yil": 2020, "Marka": "Renault", "Seri": "Megane", "Model": "1.5 dCi Touch",
            "Vites_Tipi": "Otomatik", "Yakit_Tipi": "Dizel", "Boya_Degisen": "Boyasız", "Tramer_TL": 0, 
            "Motor_Hacmi_cc": 1461, "Motor_Gucu_hp": 115
        }
    },
    {
        "name": "Hasarlı Ekonomik Araç (Fiat Egea)",
        "payload": {
            "Kilometre": 45000, "Yil": 2021, "Marka": "Fiat", "Seri": "Egea", "Model": "1.4 Fire Urban",
            "Vites_Tipi": "Manuel", "Yakit_Tipi": "Benzin",
            "kaput": 3, "sol_on_camurluk": 2, "Tramer_TL": 15000, "Motor_Hacmi_cc": 1368, "Motor_Gucu_hp": 95
        }
    },
    {
        "name": "Eski ve Yüksek KM (Ford Focus)",
        "payload": {
            "Kilometre": 245000, "Yil": 2012, "Marka": "Ford", "Seri": "Focus", "Model": "1.6 TDCi Trend X",
            "Vites_Tipi": "Manuel", "Yakit_Tipi": "Dizel",
            "tavan": 2, "bagaj": 2, "Tramer_TL": 4500, "Motor_Hacmi_cc": 1560, "Motor_Gucu_hp": 95
        }
    },
    {
        "name": "Lüks Segment SUV (BMW X5)",
        "payload": {
            "Kilometre": 120000, "Yil": 2018, "Marka": "BMW", "Seri": "X5", "Model": "xDrive30d",
            "Vites_Tipi": "Otomatik", "Yakit_Tipi": "Dizel",
            "Kasa_Tipi": "Arazi/SUV & Pick-up", "Boya_Degisen": "Boyasız", "Tramer_TL": 0
        }
    },
    {
        "name": "Yeni ve Temiz SUV (Peugeot 3008)",
        "payload": {
            "Kilometre": 15000, "Yil": 2023, "Marka": "Peugeot", "Seri": "3008", "Model": "1.5 BlueHDi Allure",
            "Vites_Tipi": "Otomatik", "Yakit_Tipi": "Dizel", "Boya_Degisen": "Boyasız", "Tramer_TL": 0
        }
    },
    {
        "name": "Popüler Otomatik Hatchback (VW Golf)",
        "payload": {
            "Kilometre": 35000, "Yil": 2022, "Marka": "Volkswagen", "Seri": "Golf", "Model": "1.0 eTSI Impression",
            "Vites_Tipi": "Yarı Otomatik", "Yakit_Tipi": "Benzin", "sol_on_kapi": 1, "Tramer_TL": 2000
        }
    },
    {
        "name": "Yüksek Hasarlı Klasik (Honda Civic)",
        "payload": {
            "Kilometre": 95000, "Yil": 2018, "Marka": "Honda", "Seri": "Civic", "Model": "1.6 i-VTEC Eco Elegance",
            "Vites_Tipi": "Otomatik", "Yakit_Tipi": "LPG & Benzin",
            "kaput": 3, "tavan": 3, "bagaj": 3, "Tramer_TL": 120000
        }
    },
    {
        "name": "Kayıtlı Yıl Olmayan Model Fallback (Yıl 1995)",
        "payload": {
            "Kilometre": 350000, "Yil": 1995, "Marka": "Toyota", "Seri": "Corolla", "Model": "1.6 GLi",
            "Vites_Tipi": "Manuel", "Yakit_Tipi": "Benzin", "Boya_Degisen": "Belirsiz", "Tramer_TL": 0
        }
    },
    {
        "name": "Otomatik Doldurma Testi (Motor Hacmi/Gücü yok)",
        "payload": {
            "Kilometre": 60000, "Yil": 2021, "Marka": "Hyundai", "Seri": "i20", "Model": "1.4 MPI Jump",
            "Vites_Tipi": "Otomatik", "Yakit_Tipi": "Benzin", "Boya_Degisen": "Temiz", "Tramer_TL": 0
        }
    },
    {
        "name": "Eksik Bilgili Sıradan Sedan (Opel Astra)",
        "payload": {
            "Kilometre": 110000, "Yil": 2016, "Marka": "Opel", "Seri": "Astra", "Model": "1.6 CDTI Design",
            "Vites_Tipi": "Manuel", "Yakit_Tipi": "Dizel", "Tramer_TL": 0
        }
    }
]

print("=== 10 FARKLI ARAÇ İLE API TESTİ BAŞLIYOR ===\n")

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['name']}")
    try:
        response = requests.post(API_URL, json=test['payload'], timeout=5)
        if response.status_code == 200:
            data = response.json()
            price = data.get("tahmini_fiyat")
            r2 = data.get("model_r2", 0) * 100
            print(f"✅ BAŞARILI | Fiyat: {price:,} TL (Model R²: %{r2:.1f})")
        else:
            print(f"❌ HATA {response.status_code}: {response.text}")
    except Exception as e:
        print(f"⚠️ BAĞLANTI HATASI: {e}")
    print("-" * 50)
    time.sleep(0.5)

print("\nTEST TAMAMLANDI.")
