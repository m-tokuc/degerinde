import pandas as pd
import numpy as np
from explainability import PriceExplainer

exp = PriceExplainer()

def test_car(boya_durumu, has_boya, has_degisen):
    df = pd.DataFrame([{
        "Marka": "Dacia", "Seri": "Sandero", "Model": "0.9 TCe Stepway", "Kasa_Tipi": "Hatchback/5",
        "Vites_Tipi": "Düz", "Yakit_Tipi": "Benzin", "Cekis": "Belirtilmemiş", 
        "Renk": "Belirtilmemiş", "Kimden": "Belirtilmemiş", "Garanti_Durumu": "Belirtilmemiş",
        "Silindir_Sayisi": "Belirtilmemiş", "Koltuk_Sayisi": "Belirtilmemiş", 
        "Boya_Durumu": boya_durumu,
        "Arac_Yasi": 11.0, "Kilometre": 34232.0, "Yillik_Ortalama_KM": 34232.0/11.0,
        "Motor_Hacmi_cc": np.nan, "Motor_Gucu_hp": np.nan, "Tramer_TL": 0.0,
        "Has_Boya": has_boya, "Has_Degisen": has_degisen, "Has_Tramer": 0.0
    }])
    res = exp.explain_prediction(df)
    print(f"--- {boya_durumu} (Boya:{has_boya}, Degisen:{has_degisen}) ---")
    print(f"Predicted Price: {res['final_price']}")
    print(f"Damage Impact: {res['damage_impact']}")

test_car("Temiz", 0, 0)
