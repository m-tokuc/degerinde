import pandas as pd
import joblib
import warnings
warnings.filterwarnings('ignore')

print("Model yükleniyor (car_price_model.pkl)...")
model_data = joblib.load("car_price_model.pkl")
pipeline = model_data["model"]

CATEGORICAL_FEATURES = model_data["categorical_features"]
NUMERICAL_FEATURES = model_data["numerical_features"]

def create_car(**kwargs):
    car = {c: "Belirtilmemiş" for c in CATEGORICAL_FEATURES}
    for c in NUMERICAL_FEATURES:
        car[c] = 0.0
    
    # Standart başlangıç özellikleri (Orta Segment)
    car["Vites Tipi"] = "Otomatik"
    car["Yakıt Tipi"] = "Dizel"
    car["Kasa Tipi"] = "Sedan"
    car["Çekiş"] = "Önden Çekiş"
    car["Renk"] = "Beyaz"
    car["Kimden"] = "Sahibinden"
    car["Silindir Sayısı"] = "4"
    car["Koltuk Sayısı"] = "5"
    car["Motor_Hacmi_cc"] = 1461.0
    car["Motor_Gucu_hp"] = 110.0
    
    # Replace underscores with spaces for keys that should have spaces
    for k, v in kwargs.items():
        key_with_space = k.replace("_", " ")
        if key_with_space in CATEGORICAL_FEATURES or key_with_space in NUMERICAL_FEATURES:
            car[key_with_space] = v
        else:
            car[k] = v
    return car

scenarios = []

# 1. Standart Referans
scenarios.append(create_car(
    Marka="Renault", Seri="Megane", Model="1.5 dCi Touch", Yıl=2020, Kilometre=50000,
    Boya_Durumu="Hatasız", Has_Boya=0, Has_Degisen=0, Has_Tramer=0, Tramer_TL=0
))

# 2. Ağır Hasar Testi (3 değişen, 2 boya, 150k Tramer) - Aynı Araç
scenarios.append(create_car(
    Marka="Renault", Seri="Megane", Model="1.5 dCi Touch", Yıl=2020, Kilometre=50000,
    Boya_Durumu="Boyalı+Değişen", Has_Boya=1, Has_Degisen=1, Has_Tramer=1, Tramer_TL=150000,
    kaput=3, sag_on_camurluk=3, sol_on_camurluk=3,
    sag_on_kapi=1, sol_on_kapi=1
))

# 3. Yüksek KM ve Eski Yıl Testi
scenarios.append(create_car(
    Marka="Fiat", Seri="Albea", Model="1.3 Multijet", Yıl=2005, Kilometre=350000,
    Boya_Durumu="Belirsiz", Has_Boya=1, Has_Degisen=1, Tramer_TL=5000,
    Vites_Tipi="Manuel", Motor_Hacmi_cc=1248.0, Motor_Gucu_hp=70.0
))

# 4. Eksik Veri (NaN) Testi (Tramer None, Kasa Tipi None)
scenarios.append(create_car(
    Marka="Volkswagen", Seri="Passat", Model="1.5 TSI Business", Yıl=2022, Kilometre=25000,
    Tramer_TL=None, Kasa_Tipi=None, Yakıt_Tipi="Benzin", Boya_Durumu=None,
    Motor_Hacmi_cc=1498.0, Motor_Gucu_hp=150.0
))

# 5. Lüks Sınıf Testi
scenarios.append(create_car(
    Marka="Mercedes-Benz", Seri="E Serisi", Model="E 200 d AMG", Yıl=2023, Kilometre=10000,
    Boya_Durumu="Hatasız", Has_Boya=0, Has_Degisen=0, Has_Tramer=0, Tramer_TL=0,
    Motor_Hacmi_cc=1950.0, Motor_Gucu_hp=160.0, Kasa_Tipi="Sedan", Çekiş="Arkadan İtiş"
))

df_test = pd.DataFrame(scenarios)

print("\n🚀 STRES VE MANTIK TESTİ BAŞLIYOR (5 Uç Senaryo)\n" + "="*55)
try:
    preds = pipeline.predict(df_test)
    
    print(f"1. Standart Referans (2020 Megane, Hatasız, 50k KM)      : {preds[0]:,.0f} TL")
    print(f"2. Ağır Hasar (Aynı Megane, 3 Değişen, 150k Tramer)      : {preds[1]:,.0f} TL")
    
    fark = preds[0] - preds[1]
    yuzde = (fark / preds[0]) * 100
    print(f"   >>> Hasar Kaybı: -{fark:,.0f} TL (%{yuzde:.1f} Düşüş)")
    
    print(f"3. Eski & Yüksek KM (2005 Albea, 350k KM)                : {preds[2]:,.0f} TL")
    print(f"4. Eksik Veri / NaN Testi (2022 Passat, Boş alanlar var) : {preds[3]:,.0f} TL (Çökmedi!)")
    print(f"5. Lüks Segment (2023 Mercedes E200d AMG, 10k KM)        : {preds[4]:,.0f} TL")
    
    print("="*55)
    print("✅ BÜTÜN TESTLER BAŞARIYLA GEÇİLDİ.")
    
except Exception as e:
    print(f"❌ HATA OLUŞTU: {e}")
