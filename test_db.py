from app_db import engine
import pandas as pd

with engine.connect() as conn:
    df = pd.read_sql('SELECT "Boya_Raw", "Baslik" FROM araclar_clean WHERE "Boya_Raw" IS NOT NULL LIMIT 20', conn)
    for idx, row in df.iterrows():
        print(f"{row['Baslik']} -> {row['Boya_Raw']}")
