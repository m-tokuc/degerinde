"""
Değerinde — Ultimate Sanity & Stress Test (1000 Simulations)
Tests the API against strict business rules and XGBoost monotonic constraints.
"""
import random
import time
from fastapi.testclient import TestClient
from main import app

# Disable rate limiter for stress testing
app.state.limiter.enabled = False

client = TestClient(app)

BRANDS = ["Renault", "Fiat", "Volkswagen", "Ford", "Hyundai", "Toyota", "Peugeot", "BMW", "Mercedes-Benz"]
BODY_TYPES = ["Sedan", "Hatchback", "SUV", "Station Wagon"]
FUEL_TYPES = ["Benzin", "Dizel", "LPG", "Hibrit"]
GEAR_TYPES = ["Manuel", "Otomatik", "Yarı Otomatik"]

def generate_random_car():
    return {
        "Marka": random.choice(BRANDS),
        "Seri": "Belirtilmemiş", # Modelin base val'u bulması için yeterli
        "Model": "Belirtilmemiş",
        "Yil": random.randint(1995, 2026),
        "Kilometre": random.randint(0, 500000),
        "Yakit_Tipi": random.choice(FUEL_TYPES),
        "Vites_Tipi": random.choice(GEAR_TYPES),
        "Kasa_Tipi": random.choice(BODY_TYPES),
        "Renk": "Beyaz",
        "Tramer_TL": random.choice([0, 1000, 5000, 20000, 100000]),
        "sol_on_camurluk": random.choice([0, 1, 2]), # 0: Orijinal, 1: Boyalı, 2: Değişen
        "kaput": random.choice([0, 1, 2]),
        "tavan": random.choice([0, 1, 2])
    }

def run_stress_test():
    print("=" * 60)
    print("  ULTIMATE SANITY & STRESS TEST (1000 SIMULATIONS)")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for i in range(1000):
        car = generate_random_car()
        resp = client.post("/api/predict", json=car)
        
        if resp.status_code != 200:
            print(f"❌ [Sim {i}] HTTP Error: {resp.status_code}")
            fail_count += 1
            continue
            
        data = resp.json()
        fiyat = data["tahmini_fiyat"]
        etkenler = data["fiyat_etkenleri"]
        
        # 1. Assertion: Fiyat asla negatif olamaz
        assert fiyat > 0, f"Sim {i} Failed: Fiyat negatif! ({fiyat})"
        
        # 2. Assertion: Hasar Etkisi asla pozitif olamaz (EĞER HASAR VARSA)
        hasar_var_mi = (
            car["Tramer_TL"] > 0 or 
            car["sol_on_camurluk"] > 0 or 
            car["kaput"] > 0 or 
            car["tavan"] > 0
        )
        
        for etken in etkenler:
            if etken["isim"] == "Hasar / Ekspertiz Durumu":
                if hasar_var_mi and etken["yon"] == "pozitif" and etken["miktar"] > 0:
                    assert False, f"Sim {i} Failed: Araç hasarlı ama Hasar araca değer kattı! Etken: {etken}, Car: {car}"
                    
        success_count += 1
        
        if (i+1) % 200 == 0:
            print(f"✅ {i+1} simülasyon tamamlandı...")
            
    print(f"\\nStress Test Result: {success_count} Passed, {fail_count} Failed.")
    assert fail_count == 0, "Stress Test Failed!"
    

def run_monotonicity_test():
    print("\\n=" * 60)
    print("  MONOTONICITY CHECK (KM & DAMAGE)")
    print("=" * 60)
    
    for i in range(50):
        car_low_km = generate_random_car()
        car_low_km["Kilometre"] = 10000
        
        car_high_km = car_low_km.copy()
        car_high_km["Kilometre"] = 300000
        
        resp_low = client.post("/api/predict", json=car_low_km).json()
        resp_high = client.post("/api/predict", json=car_high_km).json()
        
        price_low = resp_low["tahmini_fiyat"]
        price_high = resp_high["tahmini_fiyat"]
        
        # 10 bin KM'deki araç, AYNI özelliklerdeki 300 bin KM araçtan düşük olamaz (veya eşit olabilir)
        if price_low < price_high:
            print(f"❌ Monotonicity Failed! 10k KM: {price_low} TL | 300k KM: {price_high} TL")
            print(f"   Car: {car_low_km}")
            assert False, "Monotonicity Failed!"
            
    print("✅ Monotonicity Check (KM): PASSED 50/50")
    
if __name__ == "__main__":
    start_time = time.time()
    run_stress_test()
    run_monotonicity_test()
    print(f"\\n🚀 ALL SANITY TESTS PASSED in {time.time() - start_time:.2f} seconds!")
