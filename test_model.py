import pandas as pd
from explainability import PriceExplainer

print("Loading dataset...")
# Load a small sample of the 150k dataset
df = pd.read_json("araba_verileri.jsonl", lines=True, chunksize=50000)
sample_df = next(df).sample(5, random_state=42) # Get first chunk and sample 5

print("Initializing XGBoost Explainer...")
explainer = PriceExplainer()
if not explainer.is_ready:
    print("ERROR: Model is not ready!")
    exit(1)

print("\n" + "="*80)
print(f"{'Marka':<12} {'Seri':<10} {'Yıl':<6} {'Kilometre':<12} {'Gerçek Fiyat':<15} {'Tahmin Fiyatı'}")
print("="*80)

for idx, row in sample_df.iterrows():
    # Clean KM and Price strings
    km_str = str(row.get('Kilometre', '0')).replace('.', '').replace(',', '').replace(' km', '').strip()
    km_val = float(km_str) if km_str.isdigit() else 0.0
    
    price_str = str(row.get('Fiyat', '0')).replace('.', '').replace(',', '').replace(' TL', '').strip()
    true_price = float(price_str) if price_str.isdigit() else 0.0

    def parse_engine(val, default):
        try:
            val_str = str(val).split()[0].replace('.', '').replace('cc', '').replace('hp', '').strip()
            return float(val_str)
        except:
            return default

    # Construct input matching the expected format
    arac_yasi = max(0, 2026 - int(float(row.get('Yıl', 2020))))
    safe_age = 1 if arac_yasi == 0 else arac_yasi
    yillik_km = km_val / safe_age
    
    # Minimal fields required by model
    df_input = pd.DataFrame([{
        "Marka": row.get('Marka', 'Unknown'),
        "Seri": row.get('Seri', 'Unknown'),
        "Model": row.get('Model', 'Unknown'),
        "Kasa_Tipi": row.get('Kasa Tipi', 'Hatchback'),
        "Vites_Tipi": row.get('Vites Tipi', 'Manuel'),
        "Yakit_Tipi": row.get('Yakıt Tipi', 'Benzin'),
        "Cekis": row.get('Çekiş', 'Önden Çekiş'),
        "Renk": row.get('Renk', 'Beyaz'),
        "Kimden": row.get('Kimden', 'Sahibinden'),
        "Garanti_Durumu": row.get('Garanti Durumu', 'Belirtilmemiş'),
        "Silindir_Sayisi": row.get('Silindir Sayısı', '4'),
        "Koltuk_Sayisi": row.get('Koltuk Sayısı', '5'),
        "Boya_Durumu": row.get('Boya-değişen', 'Boyasız'),
        "Arac_Yasi": float(arac_yasi),
        "Kilometre": km_val,
        "Yillik_Ortalama_KM": yillik_km,
        "Motor_Hacmi_cc": parse_engine(row.get('Motor Hacmi'), 1400.0),
        "Motor_Gucu_hp": parse_engine(row.get('Motor Gücü'), 90.0),
        "Tramer_TL": 0.0,
        "Has_Boya": 0.0,
        "Has_Degisen": 0.0,
        "Has_Tramer": 0.0
    }])
    
    # Predict
    explanation = explainer.explain_prediction(df_input)
    predicted = explanation.get('final_price', 0) if "error" not in explanation else "ERROR"
    
    marka = str(row.get('Marka', ''))[:11]
    seri = str(row.get('Seri', ''))[:9]
    yil = str(row.get('Yıl', ''))
    km_formatted = f"{int(km_val):,}".replace(',', '.')
    
    true_str = f"{true_price:,.0f} TL".replace(',', '.')
    pred_str = f"{predicted:,.0f} TL".replace(',', '.') if isinstance(predicted, (int, float)) else predicted
    
    print(f"{marka:<12} {seri:<10} {yil:<6} {km_formatted:<12} {true_str:<15} {pred_str}")

print("="*80)
print("Model Sanity Check Complete!")
