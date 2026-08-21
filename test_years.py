import pandas as pd
from sqlalchemy import create_engine
engine = create_engine('postgresql+psycopg2://postgres:sifre123@localhost:5432/postgres')
df = pd.read_sql("SELECT \"Marka\", \"Seri\", \"Model\", \"Yil\" FROM araclar_clean", engine)

# Group by Marka, Seri, Model and count unique years
stats = df.groupby(["Marka", "Seri", "Model"])["Yil"].nunique().reset_index()
stats = stats.sort_values("Yil", ascending=True)

print("Models with only 1 available year in DB:")
print(stats.head(10))

print("\nAverage number of available years per Model trim:")
print(stats["Yil"].mean())
