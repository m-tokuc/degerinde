import pandas as pd
from feature_engineering import extract_raw_data, clean_damage_and_tramer, reject_outliers, add_derived_features

def run_sanity_check():
    print("--- 🔍 Phase 1: Data Sanity Check ---")
    
    # Load raw data from PostgreSQL
    print("Loading raw data from database...")
    df = extract_raw_data()
    print(f"Raw shape: {df.shape}")
    
    # Initial Null Check on critical columns before cleaning
    critical_cols = ["Marka", "Fiyat", "Kilometre", "Yıl"]
    missing_critical = df[critical_cols].isna().sum()
    print("\\n1. Missing Values in Critical Columns:")
    print(missing_critical)
    
    # Process features
    print("\\nApplying standard cleaning and feature engineering...")
    df = clean_damage_and_tramer(df)
    df = reject_outliers(df)
    df = add_derived_features(df)
    
    print(f"Clean shape after outlier rejection: {df.shape}")
    
    # Logical Checks
    print("\\n2. Logical Integrity Checks:")
    
    # Check 1: Negative or zero prices
    bad_prices = df[df["Fiyat"] <= 0]
    print(f" - Cars with price <= 0: {len(bad_prices)}")
    
    # Check 2: Impossible Kilometers
    bad_km = df[(df["Kilometre"] < 0) | (df["Kilometre"] > 1_000_000)]
    print(f" - Cars with impossible KM (<0 or >1M): {len(bad_km)}")
    
    # Check 3: Impossible Ages
    bad_age = df[(df["Arac_Yasi"] < 0) | (df["Arac_Yasi"] > 40)]
    print(f" - Cars with negative or extreme age (<0 or >40): {len(bad_age)}")
    
    # Check 4: Missing Target or Key Features
    na_summary = df[["Fiyat", "Kilometre", "Arac_Yasi", "Marka", "Seri"]].isna().sum()
    print(f" - Remaining NaNs in key columns:\\n{na_summary.to_string()}")
    
    if len(bad_prices) == 0 and len(bad_km) == 0 and len(bad_age) == 0 and na_summary.sum() == 0:
        print("\\n✅ DATASET IS ROBUST AND READY FOR BENCHMARKING!")
    else:
        print("\\n⚠️ WARNING: Some data anomalies detected. Review logs before training.")

if __name__ == "__main__":
    run_sanity_check()
