from app_db import engine
import pandas as pd

with engine.connect() as conn:
    df = pd.read_sql('SELECT "Satici_Aciklamasi" FROM araclar WHERE "Satici_Aciklamasi" IS NOT NULL LIMIT 10', conn)
    print("Non-null Satici_Aciklamasi count:", len(df))
    for idx, row in df.iterrows():
        print(f"Row {idx}: {str(row['Satici_Aciklamasi'])[:50]}")
