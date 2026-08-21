import pandas as pd
from sqlalchemy import create_engine
engine = create_engine('postgresql+psycopg2://postgres:sifre123@localhost:5432/postgres')
df = pd.read_sql("SELECT \"Marka\", \"Seri\", \"Yil\" FROM araclar_clean", engine)

# Group by Marka, Seri and count unique years
stats = df.groupby(["Marka", "Seri"])["Yil"].nunique().reset_index()
stats = stats.sort_values("Yil", ascending=True)

print("\nAverage number of available years per Seri:")
print(stats["Yil"].mean())
print(stats.tail(10))
