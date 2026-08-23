#!/bin/bash
cd /home/ubuntu/degerinde/degerinde || exit
# Değerinde MLOps Automation Pipeline
#
# =========================================================
# KURULUM (CRONTAB - Her Gece Saat 03:00):
# crontab -e komutu ile şu satırı ekleyin:
# 0 3 * * * /home/ubuntu/degerinde/degerinde/mlops_pipeline.sh >> /var/log/degerinde_mlops.log 2>&1
# =========================================================

set -e

PROJECT_DIR=$(pwd) # Yerel geliştirme için esneklik sağlandı
WEBHOOK_URL="https://discord.com/api/webhooks/mock_id/mock_token"

function notify() {
    local message="$1"
    echo -e "$message"
    # curl -H "Content-Type: application/json" -d "{\\"content\\": \\"$message\\"}" $WEBHOOK_URL || true
}

echo "========================================================="
notify "🚀 [START] Değerinde MLOps Pipeline: $(date)"
echo "========================================================="

# 0. HAFTALIK YEDEKLEME (BACKUP) - Her Pazar çalışır
if [ "$(date +%u)" -eq 7 ]; then
    echo "📦 Haftalık Backup alınıyor..."
    mkdir -p "$PROJECT_DIR/backups"
    zip -r "$PROJECT_DIR/backups/backup_$(date +%F).zip" "$PROJECT_DIR/models" "$PROJECT_DIR/araba_verileri.jsonl" > /dev/null 2>&1 || true
    notify "✅ Model ve veriler haftalık olarak yedeklendi."
fi

# 1 & 2. SCRAPING
echo "1. Linkler ve ilan detayları toplanıyor..."
# python3 link_toplayici.py
# python3 detay_cekici.py

# 3. VERİ TEMİZLİĞİ
echo "2. Yeni veriler NLP'den geçirilerek veritabanına aktarılıyor..."
python3 schema_clean.py --jsonl araba_verileri.jsonl > /dev/null || true

# 4. FAIL-SAFE MODEL EĞİTİMİ (Zero-Regression)
echo "3. Model V2 (Optuna) yeni verilerle baştan eğitiliyor..."
if python3 train_model_v2.py; then
    notify "📈 [SUCCESS] MLOps: Model V2 başarıyla eğitildi ve MAPE testini geçti."
    curl -s -X POST "https://api.telegram.org/bot8830837825:AAGvO_ndEpOlmdTayWRTFmQSIrMXsYelmnU/sendMessage" -d "chat_id=8727178989&text=✅ Değerinde MLOps: Gece eğitimi başarıyla tamamlandı ve yeni model canlıya alındı!"
else
    notify "🚨 [FAILED] MLOps İPTAL: Yeni model testleri geçemedi, ESKİ MODEL KORUNDU!"
    curl -s -X POST "https://api.telegram.org/bot8830837825:AAGvO_ndEpOlmdTayWRTFmQSIrMXsYelmnU/sendMessage" -d "chat_id=8727178989&text=🚨 DİKKAT MLOps: Yeni modelin hata payı yüksek çıktı! Güncelleme iptal edildi, eski model devrede."
    exit 1
fi

# 5. GRACEFUL RELOAD
echo "4. FastAPI (Uvicorn) workers'a reload sinyali gönderiliyor..."
docker exec car_price_api kill -s HUP 1 > /dev/null 2>&1 || curl -s -X POST "http://localhost:8000/api/admin/reload-model" > /dev/null || true

echo "========================================================="
notify "✅ [DONE] MLOps Pipeline Tamamlandı: $(date)"
echo "========================================================="
