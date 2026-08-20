"""
Değerinde — Explainable AI (XAI)
Generates SHAP values to explain individual price predictions.
"""
import joblib
import numpy as np
import pandas as pd
import shap
import warnings

warnings.filterwarnings("ignore")

class PriceExplainer:
    def __init__(self, model_path="models/v2/model.pkl"):
        try:
            self.model_data = joblib.load(model_path)
            self.pipeline = self.model_data["model"]
            self.preprocessor = self.pipeline.named_steps["preprocessor"]
            self.regressor = self.pipeline.named_steps["regressor"]
            
            # The features after preprocessing
            self.out_features = (
                self.model_data.get("high_cardinality_cats", []) + 
                self.model_data.get("low_cardinality_cats", []) + 
                self.model_data.get("numerical_features", [])
            )
            
            self.explainer = shap.TreeExplainer(self.regressor)
            self.is_ready = True
        except Exception as e:
            print(f"Failed to load explainer: {e}")
            self.is_ready = False

    def explain_prediction(self, df_input: pd.DataFrame) -> dict:
        """
        Takes a raw pandas DataFrame with a single row (the car to predict).
        Returns a dictionary explaining the price components.
        """
        if not self.is_ready:
            return {"error": "Explainer not ready"}
            
        try:
            # 1. Get raw prediction
            final_price = float(self.pipeline.predict(df_input)[0])
            
            # 2. Transform input
            X_trans = self.preprocessor.transform(df_input)
            
            # 3. Calculate SHAP values
            shap_values = self.explainer.shap_values(X_trans)
            
            # For a single prediction, shap_values is a 1D array
            impacts = shap_values[0]
            base_value = float(self.explainer.expected_value)
            
            # Group the impacts into readable categories for the frontend
            # We don't want to show 20 different features to a user, group them logically.
            grouped_impacts = {
                "base_price": base_value,
                "brand_model_impact": 0.0,
                "km_impact": 0.0,
                "age_impact": 0.0,
                "gear_engine_impact": 0.0,
                "damage_impact": 0.0,
                "other_impact": 0.0,
                "final_price": final_price
            }
            
            for feature_name, impact_val in zip(self.out_features, impacts):
                val = float(impact_val)
                if feature_name in ["Marka", "Seri", "Model", "Kasa_Tipi"]:
                    grouped_impacts["brand_model_impact"] += val
                elif feature_name in ["Kilometre", "Yillik_Ortalama_KM"]:
                    grouped_impacts["km_impact"] += val
                elif feature_name == "Arac_Yasi":
                    grouped_impacts["age_impact"] += val
                elif feature_name in ["Vites_Tipi", "Yakit_Tipi", "Motor_Hacmi_cc", "Motor_Gucu_hp", "Silindir_Sayisi"]:
                    grouped_impacts["gear_engine_impact"] += val
                elif feature_name in ["Tramer_TL", "Has_Boya", "Has_Degisen", "Has_Tramer", "Boya_Durumu",
                                      "kaput", "tavan", "bagaj", "sol_on_camurluk", "sag_on_camurluk", 
                                      "sol_arka_camurluk", "sag_arka_camurluk", "sol_on_kapi", "sag_on_kapi", 
                                      "sol_arka_kapi", "sag_arka_kapi", "on_tampon", "arka_tampon"]:
                    grouped_impacts["damage_impact"] += val
                else:
                    grouped_impacts["other_impact"] += val
                    
            # Ensure the sum adds up to final price (handle slight floating point differences)
            total_calc = sum([v for k, v in grouped_impacts.items() if k not in ["final_price"]])
            diff = final_price - total_calc
            grouped_impacts["other_impact"] += diff
            
            # Round values
            for k in grouped_impacts:
                grouped_impacts[k] = round(grouped_impacts[k], 2)
                
            return grouped_impacts
            
        except Exception as e:
            return {"error": str(e)}

# Quick test if run directly
if __name__ == "__main__":
    explainer = PriceExplainer()
    if explainer.is_ready:
        test_data = pd.DataFrame([{
            "Marka": "Renault", "Seri": "Clio", "Model": "1.5 dCi Touch", "Kasa_Tipi": "Hatchback",
            "Vites_Tipi": "Otomatik", "Yakit_Tipi": "Dizel", "Cekis": "Önden Çekiş", 
            "Renk": "Beyaz", "Kimden": "Sahibinden", "Garanti_Durumu": "Belirtilmemiş",
            "Silindir_Sayisi": "4", "Koltuk_Sayisi": "5", "Boya_Durumu": "Boyasız",
            "Arac_Yasi": 3.0, "Kilometre": 45000.0, "Yillik_Ortalama_KM": 15000.0,
            "Motor_Hacmi_cc": 1461.0, "Motor_Gucu_hp": 90.0, "Tramer_TL": 0.0,
            "Has_Boya": 0.0, "Has_Degisen": 0.0, "Has_Tramer": 0.0
        }])
        print("Test Prediction Explanation:")
        print(explainer.explain_prediction(test_data))
