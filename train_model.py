"""
Değerinde — Araç Fiyat Tahmin Modeli v5
Clean hasar/tramer features + honest metrics (MAPE, brand MAE, stratified holdout)
"""
from __future__ import annotations

import os
import re
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
from dotenv import load_dotenv
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedShuffleSplit, train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from schema_clean import (
    load_clean_dataframe,
    normalize_str,
    parse_hasar_flags,
    parse_tramer_tl,
)

load_dotenv()

DB_URL = os.getenv(
    "DB_URL",
    "postgresql+psycopg2://postgres:sifre123@localhost:5432/postgres",
)
MODEL_PATH = os.getenv("MODEL_PATH", "car_price_model.pkl")

CATEGORICAL_FEATURES = [
    "Marka",
    "Seri",
    "Model",
    "Vites Tipi",
    "Yakıt Tipi",
    "Kasa Tipi",
    "Çekiş",
    "Renk",
    "Kimden",
    "Garanti Durumu",
    "Silindir Sayısı",
    "Koltuk Sayısı",
    "Boya_Durumu",
]

NUMERICAL_FEATURES = [
    "Yıl",
    "Kilometre",
    "Motor_Hacmi_cc",
    "Motor_Gucu_hp",
    "Tramer_TL",
    "Has_Boya",
    "Has_Degisen",
    "Has_Tramer",
]

# XGB monotone: + year, − km / tramer / damage flags (aligned to cat+num order after CT)
# Cats → 0; then nums in NUMERICAL_FEATURES order
MONOTONE_NUM = {
    "Yıl": 1,
    "Kilometre": -1,
    "Motor_Hacmi_cc": 0,
    "Motor_Gucu_hp": 0,
    "Tramer_TL": -1,
    "Has_Boya": -1,
    "Has_Degisen": -1,
    "Has_Tramer": -1,
}


def parse_numeric_first(val, scale=1.0):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val) * scale
    cleaned = str(val).replace(".", "").replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    return float(m.group(1)) if m else np.nan


def mape(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def mdape(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if mask.sum() == 0:
        return float("nan")
    return float(np.median(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


print("=" * 60)
print("  DEĞERİNDE — ARAÇ FİYAT TAHMİN MODELİ EĞİTİMİ v5")
print("=" * 60)

print("\n1. araclar_clean yükleniyor (yoksa legacy backfill)...")
df = load_clean_dataframe()
print(f"   Toplam {len(df):,} temiz kayıt.")

# Harmonize column names used by ML (legacy Turkish display names in pipeline)
df = df.rename(
    columns={
        "Yil": "Yıl",
        "Yakit_Tipi": "Yakıt Tipi",
        "Vites_Tipi": "Vites Tipi",
        "Kasa_Tipi": "Kasa Tipi",
        "Cekis": "Çekiş",
        "Garanti_Durumu": "Garanti Durumu",
        "Silindir_Sayisi": "Silindir Sayısı",
        "Koltuk_Sayisi": "Koltuk Sayısı",
        "Motor_Hacmi": "Motor Hacmi",
        "Motor_Gucu": "Motor Gücü",
    }
)

print("\n2. Hasar / Tramer yeniden parse (güvenli)...")
# Prefer stored clean flags; re-derive when Belirsiz / missing
tramer_reparsed = df.apply(
    lambda r: parse_tramer_tl(
        r["Tramer_TL"] if pd.notna(r.get("Tramer_TL")) and float(r.get("Tramer_TL") or 0) > 0
        else r.get("Tramer_Tutari_Raw")
    ),
    axis=1,
)
df["Tramer_TL"] = tramer_reparsed.clip(0, 5_000_000)

need_reparse = (
    df.get("Boya_Durumu").isna()
    if "Boya_Durumu" in df.columns
    else pd.Series(True, index=df.index)
)
if "Boya_Durumu" in df.columns:
    need_reparse = need_reparse | df["Boya_Durumu"].astype(str).isin(
        ["", "nan", "None", "Belirsiz"]
    )
    # Also reparse rows that only have junk stored
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

# Tramer_TL > 0 forces Has_Tramer
df.loc[df["Tramer_TL"] > 0, "Has_Tramer"] = 1

print("   Boya_Durumu:", df["Boya_Durumu"].value_counts(dropna=False).to_dict())
print(
    "   Has flags mean:",
    {
        "Has_Boya": float(df["Has_Boya"].mean()),
        "Has_Degisen": float(df["Has_Degisen"].mean()),
        "Has_Tramer": float(df["Has_Tramer"].mean()),
        "Tramer>0": float((df["Tramer_TL"] > 0).mean()),
    },
)
print(f"   Markalar: {df['Marka'].value_counts().head(12).to_dict()}")

print("\n3. Nümerik kolonlar...")
df["Fiyat"] = pd.to_numeric(df["Fiyat"], errors="coerce")
df["Kilometre"] = pd.to_numeric(df["Kilometre"], errors="coerce")
df["Yıl"] = pd.to_numeric(df["Yıl"], errors="coerce")
df["Motor_Hacmi_cc"] = df["Motor Hacmi"].apply(parse_numeric_first).clip(0, 8000)
df["Motor_Gucu_hp"] = df["Motor Gücü"].apply(parse_numeric_first).clip(0, 1000)
df["Has_Boya"] = pd.to_numeric(df["Has_Boya"], errors="coerce").fillna(0).clip(0, 1)
df["Has_Degisen"] = pd.to_numeric(df["Has_Degisen"], errors="coerce").fillna(0).clip(0, 1)
df["Has_Tramer"] = pd.to_numeric(df["Has_Tramer"], errors="coerce").fillna(0).clip(0, 1)

df["Silindir Sayısı"] = (
    df["Silindir Sayısı"]
    .apply(lambda x: parse_numeric_first(x) if pd.notna(x) else np.nan)
    .fillna(4)
    .astype(int)
    .astype(str)
)
df["Koltuk Sayısı"] = (
    df["Koltuk Sayısı"]
    .apply(lambda x: parse_numeric_first(x) if pd.notna(x) else np.nan)
    .fillna(5)
    .astype(int)
    .astype(str)
)

print("\n4. Outlier temizleme (eğitim seti)...")
n_before = len(df)
df = df[df["Fiyat"].between(50_000, 100_000_000)]
df = df[df["Kilometre"].between(0, 1_000_000)]
df = df[df["Yıl"].between(1990, 2026)]
df = df[df["Marka"].notna() & (df["Marka"] != "Diğer")]
Q1 = df["Fiyat"].quantile(0.01)
Q3 = df["Fiyat"].quantile(0.99)
df = df[df["Fiyat"].between(Q1, Q3)]
print(f"   {n_before:,} → {len(df):,} kayıt.")

cat_fill = "Belirtilmemiş"
for col in CATEGORICAL_FEATURES:
    if col not in df.columns:
        df[col] = cat_fill
    df[col] = df[col].fillna(cat_fill).astype(str).str.strip()
    df[col] = df[col].replace({"": cat_fill, "nan": cat_fill, "None": cat_fill})

for col in NUMERICAL_FEATURES:
    df[col] = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan)

print(
    f"\n5. Özellikler ({len(CATEGORICAL_FEATURES)} cat + {len(NUMERICAL_FEATURES)} num)"
)

print("\n6. ML Pipeline...")
monotone = [0] * len(CATEGORICAL_FEATURES) + [
    MONOTONE_NUM[c] for c in NUMERICAL_FEATURES
]
try:
    import xgboost as xgb

    regressor = xgb.XGBRegressor(
        n_estimators=800,
        max_depth=7,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        verbosity=0,
        enable_categorical=False,
        monotone_constraints=tuple(monotone),
    )
    model_name = "XGBoost"
    print(f"   ✅ XGBoost + monotone_constraints={monotone}")
except Exception as e:
    print(f"   ⚠️ XGBoost yok ({e}), RandomForest fallback.")
    from sklearn.ensemble import RandomForestRegressor

    regressor = RandomForestRegressor(
        n_estimators=400,
        max_depth=16,
        min_samples_leaf=3,
        n_jobs=-1,
        random_state=42,
    )
    model_name = "RandomForest"

cat_pipeline = Pipeline(
    [
        ("imputer", SimpleImputer(strategy="constant", fill_value=cat_fill)),
        (
            "encoder",
            OrdinalEncoder(
                handle_unknown="use_encoded_value",
                unknown_value=-1,
                encoded_missing_value=-1,
            ),
        ),
    ]
)
num_pipeline = Pipeline([("imputer", SimpleImputer(strategy="median"))])
preprocessor = ColumnTransformer(
    transformers=[
        ("cat", cat_pipeline, CATEGORICAL_FEATURES),
        ("num", num_pipeline, NUMERICAL_FEATURES),
    ],
    remainder="drop",
)
pipeline = Pipeline([("preprocessor", preprocessor), ("regressor", regressor)])

X = df[CATEGORICAL_FEATURES + NUMERICAL_FEATURES].copy()
y = df["Fiyat"].copy()

# Stratify by Marka (rare brands → Other) to fight Fiat dominance overfitting
brand_counts = df["Marka"].value_counts()
strat_labels = df["Marka"].where(df["Marka"].map(brand_counts) >= 40, "Other")
print("\n7. Stratified holdout (by Marka, test=20%)...")
try:
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(sss.split(X, strat_labels))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    brands_test = df.iloc[test_idx]["Marka"]
    years_test = df.iloc[test_idx]["Yıl"]
except ValueError as e:
    print(f"   Stratify başarısız ({e}) — random split fallback")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    brands_test = df.loc[X_test.index, "Marka"]
    years_test = df.loc[X_test.index, "Yıl"]

print(f"   train={len(X_train):,}, test={len(X_test):,}")
print(f"   test Marka dağılımı: {brands_test.value_counts().head(8).to_dict()}")

print(f"\n8. Eğitim ({model_name})...")
pipeline.fit(X_train, y_train)

print("\n9. Dürüst değerlendirme...")
y_pred = pipeline.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
r2 = r2_score(y_test, y_pred)
mape_v = mape(y_test, y_pred)
mdape_v = mdape(y_test, y_pred)

print("\n" + "=" * 56)
print(f"  {'MAE':<36} {mae:>14,.0f} TL")
print(f"  {'RMSE':<36} {rmse:>14,.0f} TL")
print(f"  {'R²':<36} {r2:>14.4f}")
print(f"  {'MAPE':<36} {mape_v:>13.2f} %")
print(f"  {'MdAPE (median)':<36} {mdape_v:>13.2f} %")
print("=" * 56)

print("\n10. Marka bazlı MAE / MAPE (test):")
brand_metrics = []
eval_df = pd.DataFrame(
    {"Marka": brands_test.values, "y_true": y_test.values, "y_pred": y_pred}
)
for brand, g in eval_df.groupby("Marka"):
    if len(g) < 5:
        continue
    b_mae = mean_absolute_error(g["y_true"], g["y_pred"])
    b_mape = mape(g["y_true"], g["y_pred"])
    brand_metrics.append(
        {"Marka": brand, "n": len(g), "MAE": b_mae, "MAPE": b_mape}
    )
    print(f"  {brand:<18} n={len(g):<5} MAE={b_mae:>10,.0f}  MAPE={b_mape:>6.2f}%")

# Year-band holdout report (proxy for time when scraped_at sparse)
print("\n11. Yıl bandı MAE (zaman proxy):")
eval_df["Yıl"] = years_test.values
for lo, hi, label in [
    (1990, 2010, "1990-2010"),
    (2011, 2016, "2011-2016"),
    (2017, 2020, "2017-2020"),
    (2021, 2026, "2021-2026"),
]:
    g = eval_df[(eval_df["Yıl"] >= lo) & (eval_df["Yıl"] <= hi)]
    if len(g) < 10:
        continue
    print(
        f"  {label:<12} n={len(g):<5} MAE={mean_absolute_error(g['y_true'], g['y_pred']):>10,.0f} "
        f"MAPE={mape(g['y_true'], g['y_pred']):>6.2f}%"
    )

print("\n12. Feature importances:")
try:
    importances = pipeline.named_steps["regressor"].feature_importances_
    fi_df = pd.DataFrame(
        {
            "feature": CATEGORICAL_FEATURES + NUMERICAL_FEATURES,
            "importance": importances,
        }
    ).sort_values("importance", ascending=False)
    for _, row in fi_df.iterrows():
        bar = "█" * int(row["importance"] * 50)
        print(f"  {row['feature']:<22} {row['importance']:.4f}  {bar}")
except AttributeError:
    print("  (desteklenmiyor)")

model_data = {
    "model": pipeline,
    "categorical_features": CATEGORICAL_FEATURES,
    "numerical_features": NUMERICAL_FEATURES,
    "model_name": model_name,
    "r2": float(r2),
    "mae": float(mae),
    "rmse": float(rmse),
    "mape": float(mape_v),
    "mdape": float(mdape_v),
    "brand_metrics": brand_metrics,
    "version": 5,
    "monotone_constraints": monotone,
}
joblib.dump(model_data, MODEL_PATH)
print(f"\n✅ Model '{MODEL_PATH}' kaydedildi. R²={r2:.4f} MAPE={mape_v:.2f}% MAE={mae:,.0f}")
