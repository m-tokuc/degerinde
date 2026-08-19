#!/bin/bash
# Veritabanı Yedekleme (Backup) Scripti
# Her gece çalışarak araclar_clean ve predictions tablolarını PostgreSQL'den pg_dump ile yedekler.

set -e

BACKUP_DIR="/app/backups"
DB_NAME="arabam_db"
DB_USER="arabam_user"
# DB_PASSWORD ortam değişkenlerinden veya pgpass'tan alınır
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql.gz"

# Yedek klasörü yoksa oluştur
mkdir -p ${BACKUP_DIR}

echo "=== Veritabanı Yedekleme Başlıyor: $(date) ==="

# Sadece araclar_clean ve predictions tablolarını yedekle
# Eger tüm DB isteniyorsa -t flag'i kaldırılabilir.
pg_dump -U ${DB_USER} -d ${DB_NAME} -t araclar_clean -t predictions | gzip > ${BACKUP_FILE}

echo "Yedek başarıyla alındı: ${BACKUP_FILE}"

# 7 günden eski yedekleri sil (Disk dolmasın)
find ${BACKUP_DIR} -name "${DB_NAME}_*.sql.gz" -type f -mtime +7 -exec rm -f {} \;
echo "7 günden eski yedekler temizlendi."

echo "=== Veritabanı Yedekleme Tamamlandı: $(date) ==="
