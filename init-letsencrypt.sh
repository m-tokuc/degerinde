#!/bin/bash

if ! [ -x "$(command -v docker-compose)" ]; then
  echo 'Hata: docker-compose yüklü değil.' >&2
  exit 1
fi

domains=(degerinde.com www.degerinde.com)
rsa_key_size=4096
data_path="./certbot"
email="destek@degerinde.com" # Let's Encrypt uyarıları için
staging=0 # Üretim (Production) ortamı için 0 olmalı

if [ -d "$data_path" ]; then
  read -p "Mevcut sertifika verisi bulundu. Üzerine yazılsın ve devam edilsin mi? (e/h) " decision
  if [ "$decision" != "e" ] && [ "$decision" != "E" ]; then
    exit
  fi
fi

echo "### 1. Nginx'i kandırmak için sahte (dummy) sertifika oluşturuluyor..."
path="/etc/letsencrypt/live/${domains[0]}"
mkdir -p "$data_path/conf/live/${domains[0]}"
docker-compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

echo "### 2. Nginx ayağa kaldırılıyor..."
docker-compose up --force-recreate -d nginx
echo

echo "### 3. Nginx çalıştı, sahte sertifika siliniyor..."
docker-compose run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/${domains[0]} && \
  rm -Rf /etc/letsencrypt/archive/${domains[0]} && \
  rm -Rf /etc/letsencrypt/renewal/${domains[0]}.conf" certbot
echo

echo "### 4. Gerçek Let's Encrypt sertifikası talep ediliyor..."
# Domainleri argüman olarak birleştir
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Email argümanı
case "$email" in
  "") email_arg="--register-unsafely-without-email" ;;
  *) email_arg="--email $email" ;;
esac

# Staging (Test) argümanı
if [ $staging != "0" ]; then staging_arg="--staging"; fi

docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    $email_arg \
    $domain_args \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot
echo

echo "### 5. Sertifika alındı, Nginx yeni sertifika ile yeniden yükleniyor..."
docker-compose exec nginx nginx -s reload
echo "✅ BAŞARILI: Nginx ve SSL Sertifikası hazır!"
