-- Arabam.com Veri Seti için PostgreSQL Şeması
-- 2. El Araba Fiyat Tahmini Projesi

-- Veritabanı ve kullanıcı oluşturma (PostgreSQL admin olarak çalıştırın)
-- CREATE DATABASE arabam_db;
-- CREATE USER arabam_user WITH PASSWORD 'your_secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE arabam_db TO arabam_user;

-- Tablolar

-- 1. İlanlar Ana Tablosu
CREATE TABLE IF NOT EXISTS ilanlar (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    fiyat NUMERIC,
    fiyat_birim VARCHAR(10),
    marka VARCHAR(100),
    model VARCHAR(100),
    yil INTEGER,
    kilometre INTEGER,
    yakit_turu VARCHAR(50),
    vites_tipi VARCHAR(50),
    motor_gucu VARCHAR(50),
    motor_hacmi VARCHAR(50),
    cekis VARCHAR(50),
    kasa_tipi VARCHAR(50),
    kimden VARCHAR(50),
    il VARCHAR(100),
    ilce VARCHAR(100),
    renk VARCHAR(50),
    garanti VARCHAR(50),
    takas VARCHAR(10),
    ilan_no VARCHAR(50),
    ekspertiz_raporu TEXT,
    satici_aciklamasi TEXT,
    donanim_paketi TEXT,
    kaza_durumu VARCHAR(50),
    boya_degisen TEXT,
    tramer_tutari NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Dinamik Özellikler Tablosu (JSONB ile esnek yapı)
CREATE TABLE IF NOT EXISTS dinamik_ozellikler (
    id SERIAL PRIMARY KEY,
    ilan_id INTEGER REFERENCES ilanlar(id) ON DELETE CASCADE,
    ozellik_adi VARCHAR(100) NOT NULL,
    ozellik_degeri TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. İlan Resimleri Tablosu
CREATE TABLE IF NOT EXISTS ilan_resimleri (
    id SERIAL PRIMARY KEY,
    ilan_id INTEGER REFERENCES ilanlar(id) ON DELETE CASCADE,
    resim_url TEXT,
    resim_sira INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Veri Kalitesi Logları
CREATE TABLE IF NOT EXISTS veri_kalitesi_log (
    id SERIAL PRIMARY KEY,
    ilan_id INTEGER REFERENCES ilanlar(id) ON DELETE CASCADE,
    sorun_turu VARCHAR(50),
    aciklama TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexler (Performans için)

CREATE INDEX IF NOT EXISTS idx_ilanlar_marka ON ilanlar(marka);
CREATE INDEX IF NOT EXISTS idx_ilanlar_model ON ilanlar(model);
CREATE INDEX IF NOT EXISTS idx_ilanlar_yil ON ilanlar(yil);
CREATE INDEX IF NOT EXISTS idx_ilanlar_fiyat ON ilanlar(fiyat);
CREATE INDEX IF NOT EXISTS idx_ilanlar_kilometre ON ilanlar(kilometre);
CREATE INDEX IF NOT EXISTS idx_ilanlar_yakit ON ilanlar(yakit_turu);
CREATE INDEX IF NOT EXISTS idx_dinamik_ozellikler_ilan ON dinamik_ozellikler(ilan_id);
CREATE INDEX IF NOT EXISTS idx_dinamik_ozellikler_adi ON dinamik_ozellikler(ozellik_adi);

-- Trigger: updated_at otomatik güncelleme
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ilanlar_updated_at BEFORE UPDATE ON ilanlar
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- JSONB G-Index (Dinamik aramalar için)
-- ALTER TABLE ilanlar ADD COLUMN IF NOT EXISTS tum_ozellikler JSONB;
-- CREATE INDEX IF NOT EXISTS idx_ilanlar_tum_ozellikler ON ilanlar USING GIN (tum_ozellikler);
