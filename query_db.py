import pandas as pd
from sqlalchemy import create_engine
import json

engine = create_engine('postgresql+psycopg2://postgres:sifre123@localhost:5432/postgres')
query = 'SELECT * FROM araclar_clean LIMIT 1'
df = pd.read_sql(query, engine)
print("Columns:", list(df.columns))
