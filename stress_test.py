import requests
import random
import time

API_URL = "http://localhost:8000/api/predict"

markalar = ["Renault", "Fiat", "Ford", "Volkswagen", "BMW", "Mercedes-Benz", "Audi", "Toyota", "Honda", "Peugeot", "Tesla", "Togg", "BilinmeyenMarka", None, ""]
vitesler = ["Otomatik", "Manuel", "Yarı Otomatik", "Belirtilmemiş", None]
yakitlar = ["Dizel", "Benzin", "Elektrik", "Hibrit", "LPG & Benzin", "Belirtilmemiş", None]
hasar_durumlari = ["Temiz", "Boyalı", "Değişenli", "Boyalı+Değişen", "Tramerli", "Belirsiz", None]

# 13 Parça
parcalar = ["kaput", "tavan", "bagaj", "sol_on_camurluk", "sag_on_camurluk", "sol_arka_camurluk", "sag_arka_camurluk", "sol_on_kapi", "sag_on_kapi", "sol_arka_kapi", "sag_arka_kapi", "on_tampon", "arka_tampon"]

def generate_random_payload():
    payload = {
        "Marka": random.choice(markalar),
        "Seri": f"Seri_{random.randint(1, 100)}",
        "Model": f"Model_{random.randint(1, 500)}",
        "Yil": random.choice([random.randint(1950, 1989), random.randint(1990, 2026), random.randint(2027, 2100), None]),
        "Kilometre": random.choice([random.randint(-50000, -1), random.randint(0, 500000), random.randint(1000000, 5000000), None]),
        "Vites_Tipi": random.choice(vitesler),
        "Yakit_Tipi": random.choice(yakitlar),
        "Boya_Degisen": random.choice(hasar_durumlari),
        "Tramer_TL": random.choice([0, random.randint(1000, 500000), -5000, None]),
        "Motor_Hacmi_cc": random.choice([None, 0, random.randint(900, 3000), 50000]),
        "Motor_Gucu_hp": random.choice([None, 0, random.randint(70, 500), -10])
    }
    
    # Randomly assign parts damage (0: Orijinal, 1/2: Boyalı, 3: Değişen)
    for p in parcalar:
        payload[p] = random.choice([0, 1, 2, 3, None])
        
    return payload

def run_stress_test(num_tests=500):
    print(f"=== {num_tests} ARALIK STRES TESTİ BAŞLIYOR ===")
    
    success_count = 0
    failure_count = 0
    
    for i in range(1, num_tests + 1):
        payload = generate_random_payload()
        try:
            resp = requests.post(API_URL, json=payload, timeout=5)
            if resp.status_code == 200:
                success_count += 1
            else:
                failure_count += 1
                print(f"HATA #{i}: HTTP {resp.status_code} - Payload: {payload}")
                print(f"Response: {resp.text}")
        except Exception as e:
            failure_count += 1
            print(f"İSTİSNA #{i}: {e}")
            
    print("\n=== TEST SONUÇLARI ===")
    print(f"Toplam Test: {num_tests}")
    print(f"Başarılı (HTTP 200): {success_count}")
    print(f"Başarısız (Hatalı): {failure_count}")
    
    if failure_count == 0:
        print("\n✅ SAVUNMA KALKANI KUSURSUZ ÇALIŞIYOR. SIFIR HATA.")
    else:
        print("\n❌ SİSTEMDE AÇIK BULUNDU. KORUMA KATMANLARI YETERSİZ.")

if __name__ == "__main__":
    run_stress_test(500)
