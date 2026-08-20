#!/bin/bash
# Değerinde MLOps Automation Pipeline
# Bu script her gece CRON tarafından çalıştırılarak sistemi günceller.

set -e

PROJECT_DIR="/home/ubuntu/degerinde/degerinde" # Sunucudaki proje dizini
VENV_DIR="$PROJECT_DIR/.venv"

echo "========================================================="
echo "🚀 Değerinde MLOps Pipeline Başlıyor: $(date)"
echo "========================================================="

cd $PROJECT_DIR

# Sanal ortamı aktif et
source $VENV_DIR/bin/activate

echo "1. Linkler toplanıyor (arabam.com)..."
# Her gün en yeni 10 sayfa aracı çekmek yeterli (Günlük 500 ilan)
python3 link_toplayici.py --max_pages 10

echo "2. Detaylar çekiliyor ve araba_verileri.jsonl'e ekleniyor..."
python3 detay_cekici.py

echo "3. Yeni veriler NLP'den geçirilerek veritabanına aktarılıyor (Append)..."
# jsonl_import komutu sadece yeni ilanları ekler (URL deduplication sayesinde eskiler atlanır)
python3 schema_clean.py --jsonl araba_verileri.jsonl

echo "4. Model V3 yeni verilerle baştan eğitiliyor..."
python3 train_model.py

echo "5. Model güncellendi. FastAPI (Uvicorn) workers'a reload sinyali gönderiliyor..."
# Docker içindeki car_price_api container'ında çalışan Uvicorn'u kesintisiz (graceful) yeniden başlatır
docker exec car_price_api kill -s HUP 1 || echo "Docker API reload edilemedi, manuel reload API endpoint'i tetikleniyor..."

# Alternatif Reload (Eğer HUP çalışmazsa)
curl -X POST "http://localhost:8000/api/admin/reload-model" || true

echo "========================================================="
echo "✅ MLOps Pipeline Tamamlandı: $(date)"
echo "========================================================="
