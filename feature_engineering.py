"""
Değerinde — Advanced Feature Engineering Pipeline
Handles data extraction from DB, outlier rejection, derived features, and ML preprocessing pipelines.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OrdinalEncoder
import category_encoders as ce

from schema_clean import load_clean_dataframe, parse_hasar_flags, parse_tramer_tl

# Market-specific constants
CURRENT_YEAR = 2026

HIGH_CARDINALITY_CATS = ["Marka", "Seri", "Model", "Kasa_Tipi"]
LOW_CARDINALITY_CATS = [
    "Vites_Tipi", "Yakit_Tipi", "Cekis", "Renk", "Kimden", 
    "Garanti_Durumu", "Silindir_Sayisi", "Koltuk_Sayisi", "Boya_Durumu"
]
NUMERICAL_FEATURES = [
    "Arac_Yasi", "Kilometre", "Yillik_Ortalama_KM", "Motor_Hacmi_cc", 
    "Motor_Gucu_hp", "Tramer_TL", "Has_Boya", "Has_Degisen", "Has_Tramer"
]

def parse_numeric_first(val, scale=1.0):
    """Safely parse numeric values from strings (e.g., '1.6 CRDi' -> 1.6)"""
    import re
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val) * scale
    cleaned = str(val).replace(".", "").replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    return float(m.group(1)) if m else np.nan

def extract_raw_data() -> pd.DataFrame:
    """Loads raw data from araclar_clean table and maps column names to standard ML names."""
    df = load_clean_dataframe()
    
    df = df.rename(
        columns={
            "Yil": "Yıl",
            "Yakit_Tipi": "Yakit_Tipi",
            "Vites_Tipi": "Vites_Tipi",
            "Kasa_Tipi": "Kasa_Tipi",
            "Cekis": "Cekis",
            "Garanti_Durumu": "Garanti_Durumu",
            "Silindir_Sayisi": "Silindir_Sayisi",
            "Koltuk_Sayisi": "Koltuk_Sayisi",
            "Motor_Hacmi": "Motor_Hacmi",
            "Motor_Gucu": "Motor_Gucu",
        }
    )
    return df

def clean_damage_and_tramer(df: pd.DataFrame) -> pd.DataFrame:
    """Formalizes Tramer and Boya/Degisen logic."""
    # Reparse Tramer
    tramer_reparsed = df.apply(
        lambda r: parse_tramer_tl(
            r["Tramer_TL"] if pd.notna(r.get("Tramer_TL")) and float(r.get("Tramer_TL") or 0) > 0
            else r.get("Tramer_Tutari_Raw")
        ),
        axis=1,
    )
    df["Tramer_TL"] = tramer_reparsed.clip(0, 5_000_000)

    # Reparse Boya/Değişen flags if missing or Belirsiz
    need_reparse = df.get("Boya_Durumu").isna() if "Boya_Durumu" in df.columns else pd.Series(True, index=df.index)
    if "Boya_Durumu" in df.columns:
        need_reparse = need_reparse | df["Boya_Durumu"].astype(str).isin(["", "nan", "None", "Belirsiz"])
        need_reparse = need_reparse | (
            (df.get("Has_Boya", 0).fillna(0) == 0)
            & (df.get("Has_Degisen", 0).fillna(0) == 0)
            & df["Boya_Raw"].fillna("").astype(str).str.len().gt(0)
        )

    for idx in df.index[need_reparse.fillna(True)]:
        flags = parse_hasar_flags(
            df.at[idx, "Boya_Raw"] if "Boya_Raw" in df.columns else None,
            df.at[idx, "Boyanan_Parcalar"] if "Boyanan_Parcalar" in df.columns else None,
            df.at[idx, "Lokal_Boya"] if "Lokal_Boya" in df.columns else None,
            float(df.at[idx, "Tramer_TL"] or 0),
            df.at[idx, "Tramer_Tutari_Raw"] if "Tramer_Tutari_Raw" in df.columns else None,
        )
        df.at[idx, "Boya_Durumu"] = flags["Boya_Durumu"]
        df.at[idx, "Has_Boya"] = flags["Has_Boya"]
        df.at[idx, "Has_Degisen"] = flags["Has_Degisen"]
        df.at[idx, "Has_Tramer"] = flags["Has_Tramer"]

    # If Tramer is > 0, ensure Has_Tramer is 1
    df.loc[df["Tramer_TL"] > 0, "Has_Tramer"] = 1
    
    return df

def basic_numeric_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """Converts mixed types to numeric formats."""
    df["Fiyat"] = pd.to_numeric(df["Fiyat"], errors="coerce")
    df["Kilometre"] = pd.to_numeric(df["Kilometre"], errors="coerce")
    df["Yıl"] = pd.to_numeric(df["Yıl"], errors="coerce")
    df["Motor_Hacmi_cc"] = df["Motor_Hacmi"].apply(parse_numeric_first).clip(0, 8000)
    df["Motor_Gucu_hp"] = df["Motor_Gucu"].apply(parse_numeric_first).clip(0, 1000)
    
    df["Has_Boya"] = pd.to_numeric(df["Has_Boya"], errors="coerce").fillna(0).clip(0, 1)
    df["Has_Degisen"] = pd.to_numeric(df["Has_Degisen"], errors="coerce").fillna(0).clip(0, 1)
    df["Has_Tramer"] = pd.to_numeric(df["Has_Tramer"], errors="coerce").fillna(0).clip(0, 1)
    
    df["Silindir_Sayisi"] = df["Silindir_Sayisi"].apply(lambda x: parse_numeric_first(x) if pd.notna(x) else np.nan).fillna(4).astype(int).astype(str)
    df["Koltuk_Sayisi"] = df["Koltuk_Sayisi"].apply(lambda x: parse_numeric_first(x) if pd.notna(x) else np.nan).fillna(5).astype(int).astype(str)
    
    return df

def reject_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Removes absurdly low or high prices, out of bounds years, etc."""
    df = df[df["Fiyat"].between(50_000, 100_000_000)]
    df = df[df["Kilometre"].between(0, 1_000_000)]
    df = df[df["Yıl"].between(1990, CURRENT_YEAR)]
    df = df[df["Marka"].notna() & (df["Marka"] != "Diğer")]
    
    Q1 = df["Fiyat"].quantile(0.01)
    Q3 = df["Fiyat"].quantile(0.99)
    df = df[df["Fiyat"].between(Q1, Q3)]
    
    return df

def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adds age and yearly KM features."""
    df["Arac_Yasi"] = CURRENT_YEAR - df["Yıl"]
    df["Arac_Yasi"] = df["Arac_Yasi"].clip(lower=0)
    
    # Safe divide by replacing 0 age with 1
    safe_age = df["Arac_Yasi"].replace(0, 1)
    df["Yillik_Ortalama_KM"] = df["Kilometre"] / safe_age
    
    return df

def handle_missing_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Fills missing categorical features."""
    cat_fill = "Belirtilmemiş"
    all_cats = HIGH_CARDINALITY_CATS + LOW_CARDINALITY_CATS
    for col in all_cats:
        if col not in df.columns:
            df[col] = cat_fill
        df[col] = df[col].fillna(cat_fill).astype(str).str.strip()
        df[col] = df[col].replace({"": cat_fill, "nan": cat_fill, "None": cat_fill})
    return df

def prepare_dataset() -> pd.DataFrame:
    """Executes the full pipeline to prepare the raw dataset for training."""
    print("Extracting raw data from DB...")
    df = extract_raw_data()
    print(f"Extracted {len(df)} rows.")
    
    df = clean_damage_and_tramer(df)
    df = basic_numeric_cleaning(df)
    
    n_before = len(df)
    df = reject_outliers(df)
    print(f"Outlier rejection: {n_before} -> {len(df)} rows.")
    
    df = add_derived_features(df)
    df = handle_missing_categories(df)
    
    return df

def build_ml_preprocessor() -> ColumnTransformer:
    """
    Builds the Scikit-Learn ColumnTransformer pipeline.
    Uses TargetEncoder for high cardinality features to avoid data leakage and dimensionality explosion.
    Uses OrdinalEncoder for low cardinality features.
    """
    target_enc_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Belirtilmemiş")),
        ("target_enc", ce.TargetEncoder(smoothing=10, min_samples_leaf=20))
    ])
    
    ordinal_enc_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Belirtilmemiş")),
        ("ordinal_enc", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1))
    ])
    
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median"))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("target_cat", target_enc_pipeline, HIGH_CARDINALITY_CATS),
            ("ordinal_cat", ordinal_enc_pipeline, LOW_CARDINALITY_CATS),
            ("num", num_pipeline, NUMERICAL_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False
    )
    
    return preprocessor

if __name__ == "__main__":
    df = prepare_dataset()
    print("Feature engineering complete. Prepared dataframe shape:", df.shape)
