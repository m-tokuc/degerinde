import os
import time
import warnings
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_percentage_error, mean_absolute_error
from sklearn.pipeline import Pipeline

from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor

from feature_engineering import (
    prepare_dataset, 
    build_ml_preprocessor,
    HIGH_CARDINALITY_CATS,
    LOW_CARDINALITY_CATS,
    NUMERICAL_FEATURES
)

warnings.filterwarnings("ignore")

def get_models():
    """Returns a dictionary of models with their default architectures."""
    return {
        "XGBoost": XGBRegressor(random_state=42, n_jobs=-1),
        "LightGBM": LGBMRegressor(random_state=42, n_jobs=-1, verbose=-1),
        "RandomForest": RandomForestRegressor(random_state=42, n_jobs=-1, n_estimators=100)
    }

def run_benchmark():
    print("--- 🏆 Phase 1: Multi-Model Benchmark ---")
    
    # 1. Load & Prepare Data
    print("Loading and preparing data...")
    df = prepare_dataset()
    
    target_col = "Fiyat"
    features = HIGH_CARDINALITY_CATS + LOW_CARDINALITY_CATS + NUMERICAL_FEATURES
    
    X = df[features]
    y = df[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Train size: {X_train.shape[0]}, Test size: {X_test.shape[0]}\\n")
    
    models = get_models()
    results = []
    
    # 2. Train and Evaluate Each Model
    for name, model in models.items():
        print(f"Training {name}...")
        start_time = time.time()
        
        pipeline = Pipeline([
            ("preprocessor", build_ml_preprocessor()),
            ("regressor", model)
        ])
        
        pipeline.fit(X_train, y_train)
        
        # Predict
        y_pred = pipeline.predict(X_test)
        # Avoid negative predictions just in case
        y_pred = np.clip(y_pred, a_min=1000, a_max=None)
        
        end_time = time.time()
        train_time = end_time - start_time
        
        r2 = r2_score(y_test, y_pred)
        mape = mean_absolute_percentage_error(y_test, y_pred) * 100
        mae = mean_absolute_error(y_test, y_pred)
        
        results.append({
            "Architecture": name,
            "R² Score": r2,
            "MAPE (%)": mape,
            "MAE (TL)": mae,
            "Time (s)": train_time
        })
        print(f"✅ {name} finished in {train_time:.1f}s\\n")
    
    # 3. Print Leaderboard
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by="MAPE (%)", ascending=True).reset_index(drop=True)
    
    print("=" * 65)
    print("🏆 MULTI-MODEL BENCHMARK LEADERBOARD 🏆")
    print("=" * 65)
    # Format for better display
    results_df["R² Score"] = results_df["R² Score"].apply(lambda x: f"{x:.4f}")
    results_df["MAPE (%)"] = results_df["MAPE (%)"].apply(lambda x: f"{x:.2f}%")
    results_df["MAE (TL)"] = results_df["MAE (TL)"].apply(lambda x: f"{x:,.0f} TL")
    results_df["Time (s)"] = results_df["Time (s)"].apply(lambda x: f"{x:.1f}s")
    
    print(results_df.to_string(index=True))
    print("=" * 65)
    
if __name__ == "__main__":
    run_benchmark()
