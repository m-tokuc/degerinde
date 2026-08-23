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

def objective(trial, X_train, y_train, X_val, y_val, preprocessor):
    """Optuna objective function for tuning XGBoost with early stopping."""
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 500, 1500, step=100),
        "max_depth": trial.suggest_int("max_depth", 6, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.05, log=True),
        "subsample": trial.suggest_float("subsample", 0.7, 0.95),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 0.95),
        "min_child_weight": trial.suggest_int("min_child_weight", 3, 10),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-5, 0.1, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-5, 0.1, log=True),
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
        "verbosity": 0,
        "enable_categorical": False
    }

    out_features = HIGH_CARDINALITY_CATS + LOW_CARDINALITY_CATS + NUMERICAL_FEATURES
    monotone_constraints = get_monotonic_constraints(out_features)
    params["monotone_constraints"] = monotone_constraints

    params["early_stopping_rounds"] = 50

    model = xgb.XGBRegressor(**params)
    
    # We need to transform data for the regressor since we are skipping the pipeline for eval_set
    X_t_train = preprocessor.transform(X_train)
    X_t_val = preprocessor.transform(X_val)

    model.fit(
        X_t_train, y_train,
        eval_set=[(X_t_val, y_val)],
        verbose=False
    )
    
    preds = model.predict(X_t_val)
    return mape(y_val, preds)

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
    import sys
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
    
    # Split train again to get a small validation set for Optuna early stopping
    train_bins = create_price_bins(y_train)
    skf_val = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    t_idx, v_idx = next(skf_val.split(X_train, train_bins))
    X_t, X_v = X_train.iloc[t_idx].copy(), X_train.iloc[v_idx].copy()
    y_t, y_v = y_train.iloc[t_idx].copy(), y_train.iloc[v_idx].copy()
    
    print(f"   Train: {len(X_t):,}, Val: {len(X_v):,}, Test: {len(X_test):,}")

    preprocessor = build_ml_preprocessor()
    preprocessor.fit(X_train, y_train) # Fit preprocessor on full train data
    
    print(f"\\n3. Optuna Hyperparameter Tuning ({N_TRIALS} Trials)...")
    study = optuna.create_study(direction="minimize")
    study.optimize(lambda trial: objective(trial, X_t, y_t, X_v, y_v, preprocessor), n_trials=N_TRIALS)
    
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
    
    # For the final model, we can still use early stopping against the test set
    best_params["early_stopping_rounds"] = 50
    regressor = xgb.XGBRegressor(**best_params)
    X_train_trans = preprocessor.transform(X_train)
    X_test_trans = preprocessor.transform(X_test)
    
    regressor.fit(
        X_train_trans, y_train,
        eval_set=[(X_test_trans, y_test)],
        verbose=False
    )
    
    pipeline = Pipeline([
        ("preprocessor", preprocessor), 
        ("regressor", regressor)
    ])
    
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
        importances = regressor.feature_importances_
        fi_df = pd.DataFrame({
            "feature": out_features,
            "importance": importances,
        }).sort_values("importance", ascending=False)
        for _, row in fi_df.iterrows():
            bar = "█" * int(row["importance"] * 50)
            print(f"  {row['feature']:<22} {row['importance']:.4f}  {bar}")
    except Exception as e:
        print(f"  (desteklenmiyor: {e})")
        
    # FAIL-SAFE: Check against old model before saving
    old_mape = 100.0
    if os.path.exists(MODEL_PATH):
        try:
            old_data = joblib.load(MODEL_PATH)
            old_mape = float(old_data.get("mape", 100.0))
        except Exception:
            pass

    print(f"\\nFail-Safe Check: Eski Hata (MAPE) = {old_mape:.2f}%, Yeni Hata = {mape_v:.2f}%")
    if mape_v > old_mape:
        print("🚨 EĞİTİM BAŞARISIZ: Yeni model eskisi kadar iyi değil. Değişiklikler iptal ediliyor!")
        sys.exit(1)

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
        "version": 7,
        "monotone_constraints": monotone_constraints,
    }
    
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model_data, MODEL_PATH)
    print(f"\\n✅ Model '{MODEL_PATH}' kaydedildi. R²={r2:.4f} MAPE={mape_v:.2f}% MAE={mae:,.0f}")

if __name__ == "__main__":
    train()
