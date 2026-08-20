import pandas as pd
from sqlalchemy import create_engine
engine = create_engine('postgresql+psycopg2://postgres:sifre123@localhost:5432/postgres')
df = pd.read_sql("SELECT \"Yil\" FROM araclar_clean LIMIT 10", engine)
print(df["Yil"].tolist())
print(type(df["Yil"].tolist()[0]))
