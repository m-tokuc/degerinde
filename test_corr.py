from app_db import engine
from sqlalchemy import text
import pandas as pd

with engine.connect() as conn:
    df = pd.read_sql('SELECT "Fiyat", "Has_Boya", "Has_Degisen", "Arac_Yasi", "Kilometre" FROM araclar_clean', conn)
    
print(df.corr())
