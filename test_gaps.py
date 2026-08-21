import pandas as pd
from sqlalchemy import create_engine
engine = create_engine('postgresql+psycopg2://postgres:sifre123@localhost:5432/postgres')
df = pd.read_sql("SELECT \"Marka\", \"Seri\", \"Yil\" FROM araclar_clean", engine)

# Find series that have missing years between their min and max
stats = df.groupby(["Marka", "Seri"])["Yil"].unique().reset_index()

gaps_found = 0
for idx, row in stats.iterrows():
    years = sorted([int(y) for y in row["Yil"] if pd.notna(y)])
    if not years:
        continue
    min_y = years[0]
    max_y = years[-1]
    expected_years = set(range(min_y, max_y + 1))
    actual_years = set(years)
    missing = expected_years - actual_years
    
    if len(missing) > 0:
        if gaps_found < 5:
            print(f"Gaps in {row['Marka']} {row['Seri']}: min={min_y}, max={max_y}, missing={sorted(list(missing))}")
        gaps_found += 1

print(f"\nTotal series with missing intermediate years: {gaps_found} out of {len(stats)} series.")
