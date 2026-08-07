"""
Değerinde — Robust Model Training & Evaluation (v2)
Features: Optuna tuning, Monotonic Constraints, Stratified K-Fold, and Segmented Evaluation.
"""
from __future__ import annotations

import os
import joblib
import warnings
import numpy as np
import pandas as pd
import optuna
import xgboost as xgb
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from feature_engineering import (
    prepare_dataset, 
    build_ml_preprocessor,
    HIGH_CARDINALITY_CATS,
    LOW_CARDINALITY_CATS,
    NUMERICAL_FEATURES
)

warnings.filterwarnings("ignore")

MODEL_PATH = os.getenv("MODEL_PATH", "models/v2/model.pkl")
N_TRIALS = 25
RANDOM_STATE = 42

def mape(y_true, y_pred) -> float:
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)

def mdape(y_true, y_pred) -> float:
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if mask.sum() == 0:
        return float("nan")
    return float(np.median(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)

def get_monotonic_constraints(features: list) -> tuple:
    """Returns monotonic constraints mapped to the exact feature order out of the ColumnTransformer."""
    # Logic: 
    # age -> -1 (older -> cheaper)
    # km -> -1 (higher km -> cheaper)
    # hp -> 1 (more power -> expensive)
    # tramer -> -1, has_boya -> -1, has_degisen -> -1, has_tramer -> -1
    
    constraints = []
    for f in features:
        if f == "Arac_Yasi": constraints.append(-1)
        elif f == "Kilometre": constraints.append(-1)
        elif f == "Yillik_Ortalama_KM": constraints.append(-1)
        elif f == "Motor_Gucu_hp": constraints.append(1)
        elif f == "Tramer_TL": constraints.append(-1)
        elif f in ["Has_Boya", "Has_Degisen", "Has_Tramer"]: constraints.append(-1)
        else: constraints.append(0)
    return tuple(constraints)

def create_price_bins(y: pd.Series) -> pd.Series:
    """Bin prices for Stratified K-Fold (so each fold has a mix of cheap and expensive cars)."""
    return pd.qcut(y, q=10, labels=False, duplicates='drop')

def objective(trial, X, y, preprocessor):
    """Optuna objective function for tuning XGBoost with cross-validation."""
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 300, 1000, step=100),
        "max_depth": trial.suggest_int("max_depth", 5, 12),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 1.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 1.0, log=True),
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
        "verbosity": 0,
        "enable_categorical": False
    }

    # Transform data once per trial is faster than inside CV
    X_trans = preprocessor.fit_transform(X, y)
    
    # We must assume the output columns order is: TargetCats + OrdinalCats + NumCats
    out_features = HIGH_CARDINALITY_CATS + LOW_CARDINALITY_CATS + NUMERICAL_FEATURES
    monotone_constraints = get_monotonic_constraints(out_features)
    params["monotone_constraints"] = monotone_constraints

    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    price_bins = create_price_bins(y)
    
    cv_scores = []
    
    for train_idx, val_idx in skf.split(X_trans, price_bins):
        X_train, X_val = X_trans[train_idx], X_trans[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train)
        
        preds = model.predict(X_val)
        cv_scores.append(mape(y_val, preds))
        
    return np.mean(cv_scores)

def evaluate_segments(y_true: pd.Series, y_pred: np.ndarray):
    """Calculates MAE and MAPE for Low, Mid, and High-end segments based on percentiles."""
    q30 = y_true.quantile(0.30)
    q70 = y_true.quantile(0.70)
    
    segments = {
        "Low-end (Bottom 30%)": y_true <= q30,
        "Mid-range (Middle 40%)": (y_true > q30) & (y_true <= q70),
        "High-end (Top 30%)": y_true > q70
    }
    
    print("\\n11. Segmented Evaluation:")
    for seg_name, mask in segments.items():
        if mask.sum() == 0: continue
        seg_y = y_true[mask]
        seg_pred = y_pred[mask]
        seg_mae = mean_absolute_error(seg_y, seg_pred)
        seg_mape = mape(seg_y, seg_pred)
        print(f"  {seg_name:<25} n={mask.sum():<6} MAE={seg_mae:>10,.0f} TL  MAPE={seg_mape:>6.2f}%")

def train():
    print("=" * 60)
    print("  DEĞERİNDE — ARAÇ FİYAT TAHMİN MODELİ v2 (ENTERPRISE)")
    print("=" * 60)

    print("\\n1. Preparing dataset...")
    df = prepare_dataset()
    
    features = HIGH_CARDINALITY_CATS + LOW_CARDINALITY_CATS + NUMERICAL_FEATURES
    X = df[features]
    y = df["Fiyat"]
    
    print(f"   Shape: {X.shape}")

    print("\\n2. Splitting data (Stratified by Price)...")
    price_bins = create_price_bins(y)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    
    # We take the first fold as test set (20%), rest as train (80%)
    train_idx, test_idx = next(skf.split(X, price_bins))
    X_train, X_test = X.iloc[train_idx].copy(), X.iloc[test_idx].copy()
    y_train, y_test = y.iloc[train_idx].copy(), y.iloc[test_idx].copy()
    
    print(f"   Train: {len(X_train):,}, Test: {len(X_test):,}")

    preprocessor = build_ml_preprocessor()
    
    print(f"\\n3. Optuna Hyperparameter Tuning ({N_TRIALS} Trials)...")
    study = optuna.create_study(direction="minimize")
    # For tuning, we can use the training set
    study.optimize(lambda trial: objective(trial, X_train, y_train, preprocessor), n_trials=N_TRIALS)
    
    print("   Best parameters:")
    for k, v in study.best_params.items():
        print(f"     {k}: {v}")
        
    print("\\n4. Training Final Model on full Train set...")
    best_params = study.best_params
    best_params["random_state"] = RANDOM_STATE
    best_params["n_jobs"] = -1
    best_params["enable_categorical"] = False
    
    out_features = HIGH_CARDINALITY_CATS + LOW_CARDINALITY_CATS + NUMERICAL_FEATURES
    monotone_constraints = get_monotonic_constraints(out_features)
    best_params["monotone_constraints"] = monotone_constraints
    
    regressor = xgb.XGBRegressor(**best_params)
    pipeline = Pipeline([
        ("preprocessor", preprocessor), 
        ("regressor", regressor)
    ])
    
    pipeline.fit(X_train, y_train)
    
    print("\\n5. Dürüst değerlendirme (Test Set)...")
    y_pred = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = r2_score(y_test, y_pred)
    mape_v = mape(y_test, y_pred)
    mdape_v = mdape(y_test, y_pred)

    print("\\n" + "=" * 56)
    print(f"  {'MAE':<36} {mae:>14,.0f} TL")
    print(f"  {'RMSE':<36} {rmse:>14,.0f} TL")
    print(f"  {'R²':<36} {r2:>14.4f}")
    print(f"  {'MAPE':<36} {mape_v:>13.2f} %")
    print(f"  {'MdAPE (median)':<36} {mdape_v:>13.2f} %")
    print("=" * 56)

    evaluate_segments(y_test, y_pred)

    print("\\n6. Feature importances:")
    try:
        importances = pipeline.named_steps["regressor"].feature_importances_
        fi_df = pd.DataFrame({
            "feature": out_features,
            "importance": importances,
        }).sort_values("importance", ascending=False)
        for _, row in fi_df.iterrows():
            bar = "█" * int(row["importance"] * 50)
            print(f"  {row['feature']:<22} {row['importance']:.4f}  {bar}")
    except Exception as e:
        print(f"  (desteklenmiyor: {e})")

    model_data = {
        "model": pipeline,
        "categorical_features": HIGH_CARDINALITY_CATS + LOW_CARDINALITY_CATS,
        "high_cardinality_cats": HIGH_CARDINALITY_CATS,
        "low_cardinality_cats": LOW_CARDINALITY_CATS,
        "numerical_features": NUMERICAL_FEATURES,
        "model_name": "XGBoost_v2_TargetEncoded",
        "r2": float(r2),
        "mae": float(mae),
        "rmse": float(rmse),
        "mape": float(mape_v),
        "mdape": float(mdape_v),
        "version": 6,
        "monotone_constraints": monotone_constraints,
    }
    joblib.dump(model_data, MODEL_PATH)
    print(f"\\n✅ Model '{MODEL_PATH}' kaydedildi. R²={r2:.4f} MAPE={mape_v:.2f}% MAE={mae:,.0f}")

if __name__ == "__main__":
    train()
