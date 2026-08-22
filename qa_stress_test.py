import pandas as pd
import requests
import random
import time
import json

API_URL = "http://localhost:8000/api/predict"
CACHE_FILE = "dropdown_cache.csv"

def run_qa_test():
    print("Loading valid car configurations from cache...")
    try:
        df = pd.read_csv(CACHE_FILE)
        cars = df[['Marka', 'Seri', 'Model', 'Yil', 'Vites_Tipi', 'Yakit_Tipi', 'Kasa_Tipi']].drop_duplicates().dropna().sample(100).to_dict('records')
    except Exception as e:
        print(f"Error loading cache: {e}")
        return

    print(f"Loaded {len(cars)} unique cars for stress testing.")
    
    total_tests = 0
    crashes = 0
    logic_errors = 0
    
    for idx, car in enumerate(cars):
        # Base profile
        base_payload = {
            "Marka": car["Marka"], "Seri": car["Seri"], "Model": car["Model"], "Yil": int(car["Yil"]),
            "Kilometre": 50000, "Vites_Tipi": car["Vites_Tipi"], "Yakit_Tipi": car["Yakit_Tipi"], 
            "Kasa_Tipi": car["Kasa_Tipi"], "Renk": "Siyah", "Kimden": "Sahibinden", "Garanti_Durumu": "Garantisi Yok",
            "Boya_Degisen": "Boyasız", "Tramer_TL": 0, "Motor_Hacmi_cc": 1500, "Motor_Gucu_hp": 100,
            "kaput": 0, "tavan": 0, "bagaj": 0, "sol_on_camurluk": 0, "sag_on_camurluk": 0, 
            "sol_arka_camurluk": 0, "sag_arka_camurluk": 0, "sol_on_kapi": 0, "sag_on_kapi": 0, 
            "sol_arka_kapi": 0, "sag_arka_kapi": 0, "on_tampon": 0, "arka_tampon": 0
        }

        scenarios = {
            "Base": base_payload.copy(),
            "HighKM": {**base_payload, "Kilometre": 300000},
            "HighDamage": {**base_payload, "kaput": 3, "tavan": 3, "bagaj": 3, "Boya_Degisen": "Değişenli"},
            "HighTramer": {**base_payload, "Tramer_TL": 150000, "Boya_Degisen": "Tramerli"},
            "MissingData": {**base_payload, "Renk": "Belirtilmemiş", "Kimden": "Belirtilmemiş", "Garanti_Durumu": "Belirtilmemiş"}
        }
        
        prices = {}
        for name, payload in scenarios.items():
            total_tests += 1
            try:
                resp = requests.post(API_URL, json=payload, timeout=5)
                if resp.status_code != 200:
                    crashes += 1
                    print(f"CRASH [{name}] - {car['Marka']} {car['Seri']} {car['Yil']}: HTTP {resp.status_code}")
                else:
                    data = resp.json()
                    prices[name] = data.get("tahmini_fiyat", 0)
            except Exception as e:
                crashes += 1
                print(f"CRASH [{name}] - Network error: {e}")
        
        if len(prices) == 5:
            # Logic assertions
            if prices["HighKM"] >= prices["Base"]:
                logic_errors += 1
                print(f"LOGIC ERROR: High KM price ({prices['HighKM']}) >= Base price ({prices['Base']}) for {car['Marka']} {car['Model']} {car['Yil']}")
            
            if prices["HighDamage"] >= prices["Base"]:
                logic_errors += 1
                print(f"LOGIC ERROR: High Damage price ({prices['HighDamage']}) >= Base price ({prices['Base']}) for {car['Marka']} {car['Model']} {car['Yil']}")
                
            if prices["HighTramer"] >= prices["Base"]:
                logic_errors += 1
                print(f"LOGIC ERROR: High Tramer price ({prices['HighTramer']}) >= Base price ({prices['Base']}) for {car['Marka']} {car['Model']} {car['Yil']}")
                
    print("\n" + "="*40)
    print("QA STRESS TEST RESULTS")
    print("="*40)
    print(f"Total Scenarios Tested: {total_tests}")
    print(f"Server Crashes (5xx/4xx): {crashes}")
    print(f"Logic Inconsistencies: {logic_errors}")
    if crashes == 0 and logic_errors == 0:
        print("✅ SUCCESS: The ML Model and API passed all constraints perfectly!")
    else:
        print("❌ FAILED: The system needs bug fixes.")

if __name__ == "__main__":
    run_qa_test()
