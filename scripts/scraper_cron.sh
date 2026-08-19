#!/bin/bash
# Scraper Cron Script
# Bu script her gece crontab uzerinden calisarak verileri toplar ve DB'ye basar.

set -e

APP_DIR="/app"
cd $APP_DIR

echo "=== Gece Scraper Başlıyor: $(date) ==="

# 1. Link Toplama
echo "Linkler toplanıyor..."
python link_toplayici.py

# 2. Linkleri Temizleme (Opsiyonel / Genelde detay_cekici zaten yapiyor ama guvenlik amaciyla)
# script eklenebilir veya direkt detay_cekici.py ile devam edilebilir.

# 3. Detay Çekici
echo "Araç detayları çekiliyor (Anti-ban mod devrede)..."
python detay_cekici.py

# 4. Veritabanına Yazma
echo "Veritabanına aktarım başlıyor..."
python schema_clean.py --jsonl araba_verileri.jsonl

echo "=== Scraper Tamamlandı: $(date) ==="
