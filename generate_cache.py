import pandas as pd
print("Reading chunks...")
chunks = []
rename_map = {
    "Yıl": "Yil", "Vites Tipi": "Vites_Tipi", "Yakıt Tipi": "Yakit_Tipi", "Kasa Tipi": "Kasa_Tipi",
    "Kimden": "Kimden", "Renk": "Renk", "Garanti Durumu": "Garanti_Durumu"
}
for chunk in pd.read_json("araba_verileri.jsonl", lines=True, chunksize=10000):
    chunk = chunk.rename(columns=rename_map)
    cols = ["Marka", "Seri", "Model", "Yil", "Vites_Tipi", "Yakit_Tipi", "Kasa_Tipi", "Renk", "Kimden", "Garanti_Durumu"]
    existing = [c for c in cols if c in chunk.columns]
    chunks.append(chunk[existing].drop_duplicates())

print("Concatenating...")
df = pd.concat(chunks).drop_duplicates()
df.to_csv("dropdown_cache.csv", index=False)
print(f"Done! {len(df)} unique combinations saved to dropdown_cache.csv")
