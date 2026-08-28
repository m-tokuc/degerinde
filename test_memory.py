import pandas as pd
import tracemalloc

tracemalloc.start()
chunks = []
rename_map = {
    "Yıl": "Yil", "Vites Tipi": "Vites_Tipi", "Yakıt Tipi": "Yakit_Tipi", "Kasa Tipi": "Kasa_Tipi"
}
for chunk in pd.read_json("araba_verileri.jsonl", lines=True, chunksize=10000):
    chunk = chunk.rename(columns=rename_map)
    cols_to_keep = ["Marka", "Seri", "Model", "Yil", "Vites_Tipi", "Yakit_Tipi", "Kasa_Tipi"]
    existing_cols = [c for c in cols_to_keep if c in chunk.columns]
    chunks.append(chunk[existing_cols].drop_duplicates())
    
df = pd.concat(chunks).drop_duplicates()
current, peak = tracemalloc.get_traced_memory()
print(f"Peak memory: {peak / 1024**2:.2f} MB")
print(f"Final df size: {len(df)} rows")
