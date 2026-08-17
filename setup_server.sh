#!/bin/bash

# Hata durumunda scriptin durmasını sağla
set -e

echo "1. Sistemin paket listesini güncelleniyor ve gerekli araçlar kuruluyor..."
sudo apt-get update -y
sudo apt-get install -y nginx certbot python3-certbot-nginx

echo "2. Eski Nginx ayarları (varsa) temizleniyor..."
sudo rm -f /etc/nginx/sites-enabled/default

echo "3. Nginx konfigürasyonu kopyalanıyor..."
# nginx_degerinde.conf dosyasının bu script ile aynı dizinde olduğunu varsayıyoruz
sudo cp nginx_degerinde.conf /etc/nginx/sites-available/degerinde

echo "4. Konfigürasyon aktifleştiriliyor (symlink oluşturuluyor)..."
sudo ln -sf /etc/nginx/sites-available/degerinde /etc/nginx/sites-enabled/degerinde

echo "5. Nginx konfigürasyonu test ediliyor..."
sudo nginx -t

echo "6. Nginx yeniden başlatılıyor..."
sudo systemctl restart nginx

echo "7. SSL (HTTPS) Sertifikası Kurulumu (Certbot)..."
echo "Bu aşamada Let's Encrypt tarafından sertifika alınacak ve Nginx konfigürasyonu otomatik güncellenecektir."
echo "Lütfen kurulum esnasında yönergeleri takip edin."

# read komutu ile terminalden interaktif olarak domaini almak yerine
# doğrudan manuel düzenlenmiş config üzerinden okumasını tetiklemek daha güvenli olabilir.
# Ancak kullanıcıya sorarak da yapabiliriz:
read -p "Nginx konfigürasyonuna yazdığınız Domainleri giriniz (Örn: degerinde.com www.degerinde.com): " DOMAINS

# DOMAINS değişkenini certbot formatına uygun hale getirelim (boşlukları -d parametresi ile değiştirerek)
CERTBOT_ARGS=""
for DOMAIN in $DOMAINS; do
    CERTBOT_ARGS="$CERTBOT_ARGS -d $DOMAIN"
done

sudo certbot --nginx $CERTBOT_ARGS

echo "========================================================="
echo "✅ Kurulum Tamamlandı!"
echo "Uygulamanıza artık güvenli (HTTPS) bir şekilde erişebilirsiniz."
echo "Not: SSL sertifikanız 90 gün geçerlidir, Certbot otomatik yenileme işlemini arka planda (cron) halledecektir."
echo "========================================================="
