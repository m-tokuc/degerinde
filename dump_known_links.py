import pandas as pd
from sqlalchemy import create_engine
engine = create_engine('postgresql+psycopg2://postgres:sifre123@localhost:5432/postgres')
df = pd.read_sql("SELECT ilan_url FROM araclar_clean WHERE ilan_url IS NOT NULL", engine)
df['ilan_url'].to_csv('known_links.txt', index=False, header=False)
print(f"Dumped {len(df)} known links.")
