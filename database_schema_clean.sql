-- Değerinde — canonical clean listings table (P0 hygiene)
-- External scrapers MUST insert into araclar_clean (whitelist only).
-- Never use if_exists='replace' on production data.

CREATE TABLE IF NOT EXISTS araclar_clean (
    id BIGSERIAL PRIMARY KEY,
    ilan_url TEXT,
    "Baslik" TEXT,
    "Fiyat" DOUBLE PRECISION,
    "Marka" TEXT,
    "Seri" TEXT,
    "Model" TEXT,
    "Yil" INTEGER,
    "Kilometre" DOUBLE PRECISION,
    "Yakit_Tipi" TEXT,
    "Vites_Tipi" TEXT,
    "Kasa_Tipi" TEXT,
    "Cekis" TEXT,
    "Renk" TEXT,
    "Kimden" TEXT,
    "Garanti_Durumu" TEXT,
    "Silindir_Sayisi" TEXT,
    "Koltuk_Sayisi" TEXT,
    "Motor_Hacmi" TEXT,
    "Motor_Gucu" TEXT,
    "Il" TEXT,
    "Ilce" TEXT,
    "Tramer_Tutari_Raw" TEXT,
    "Tramer_TL" DOUBLE PRECISION DEFAULT 0,
    "Boya_Raw" TEXT,
    "Boyanan_Parcalar" TEXT,
    "Lokal_Boya" TEXT,
    "Boya_Durumu" TEXT,
    "Has_Boya" SMALLINT DEFAULT 0,
    "Has_Degisen" SMALLINT DEFAULT 0,
    "Has_Tramer" SMALLINT DEFAULT 0,
    scraped_at TIMESTAMPTZ,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_araclar_clean_ilan_url
    ON araclar_clean (ilan_url)
    WHERE ilan_url IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_araclar_clean_marka ON araclar_clean ("Marka");
CREATE INDEX IF NOT EXISTS idx_araclar_clean_seri ON araclar_clean ("Seri");
CREATE INDEX IF NOT EXISTS idx_araclar_clean_yil ON araclar_clean ("Yil");
CREATE INDEX IF NOT EXISTS idx_araclar_clean_fiyat ON araclar_clean ("Fiyat");

-- Legacy dirty table: best-effort unique URL (after dedupe)
-- CREATE UNIQUE INDEX IF NOT EXISTS uq_araclar_url ON araclar ("URL") WHERE "URL" IS NOT NULL;
