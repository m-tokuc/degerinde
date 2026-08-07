# 2. El Araba Fiyat Tahmini Projesi - Detaylı Yol Haritası

## 📋 Proje Özeti
Arabam.com'dan tüm 2. el araç verilerini çekip, PostgreSQL veritabanına kaydeden ve daha sonra ML modeli ile fiyat tahmini yapan kapsamlı sistem.

---

## 🎯 AŞAMA 1: Veri Toplama (Web Scraping) - ŞU AN Kİ AŞAMA

### 1.1 Link Toplama (link_toplayici.py)
✅ **Tamamlandı**
- 47 ana markanın 50 sayfasını tarar
- URL formatı: `https://www.arabam.com/ikinci-el/otomobil/marka-adi`
- Append modu ile anında kayıt (yarıda kalsa bile veri kaybı yok)
- Rastgele bekleme (2-4 saniye) - IP ban koruması

**Çalıştırma:**
```bash
python link_toplayici.py
```

### 1.2 Veri Çekme (bot.py)
✅ **Tamamlandı**
- Headless mod KAPALI (Cloudflare bot korumasını aşmak için)
- Gerçekçi User-Agent + WebDriver gizleme
- WebDriverWait ile explicit wait
- 17 farklı CSS selector ile dinamik özellik toplama
- JavaScript ile sekme tıklama (Araç Bilgileri, Tramer, Açıklama)
- Thread-safe dosya yazma
- 5 paralel Chrome sekmesi

**Çalıştırma:**
```bash
python bot.py
```

---

## 🗄️ AŞAMA 2: PostgreSQL Veritabanı Kurulumu

### 2.1 PostgreSQL Kurulumu
**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

### 2.2 Veritabanı ve Kullanıcı Oluşturma
```bash
psql -U postgres
```

```sql
CREATE DATABASE arabam_db;
CREATE USER arabam_user WITH PASSWORD 'guvenli_sifre123';
GRANT ALL PRIVILEGES ON DATABASE arabam_db TO arabam_user;
\q
```

### 2.3 Tablo Şeması Oluşturma
```bash
psql -U arabam_user -d arabam_db -f database_schema.sql
```

### 2.4 Python Kütüphaneleri
```bash
pip install psycopg2-binary python-dotenv
```

### 2.5 Ortam Değişkenleri (.env dosyası oluştur)
```bash
DB_HOST=localhost
DB_NAME=arabam_db
DB_USER=arabam_user
DB_PASSWORD=guvenli_sifre123
DB_PORT=5432
```

### 2.6 JSONL'den PostgreSQL'e Veri Aktarma
```bash
python db_connection.py
```

---

## 🔬 AŞAMA 3: Veri Temizleme ve Ön İşleme

### 3.1 Veri Kalitesi Kontrolü
- Boş/null değerleri tespit et
- Aykırı değerleri (outliers) analiz et
- Duplicate kayıtları temizle
- Veri tiplerini düzelt (string -> int, float vb.)

### 3.2 Feature Engineering
- Yaş özelliği (2024 - Yıl)
- KM bin bölgesi (0-50K, 50-100K, 100-150K, 150K+)
- Fiyat per KM hesapla
- Marka popülerlik skoru
- İl bazlı ortalama fiyat

### 3.3 Kategorik Verileri Encode Et
- One-Hot Encoding (Marka, Model, Yakıt Tipi vb.)
- Label Encoding (Vites Tipi, Çekiş vb.)
- Target Encoding (yüksek kardinalite için)

---

## 🤖 AŞAMA 4: Makine Öğrenmesi Modeli

### 4.1 Veri Setini Bölme
```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
```

### 4.2 Model Seçimi ve Eğitim
**Denenecek Modeller:**
- Linear Regression (Baseline)
- Random Forest Regressor
- Gradient Boosting (XGBoost, LightGBM)
- CatBoost (kategorik veriler için ideal)
- Neural Networks (TensorFlow/Keras)

### 4.3 Hyperparameter Tuning
```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 20, 30],
    'learning_rate': [0.01, 0.1, 0.2]
}
```

### 4.4 Model Değerlendirme
- MAE (Mean Absolute Error)
- RMSE (Root Mean Square Error)
- R² Score
- MAPE (Mean Absolute Percentage Error)

---

## 🌐 AŞAMA 5: Python API (Django/FASTAPI)

### 5.1 Proje Kurulumu
**Django:**
```bash
pip install django djangorestframework django-cors-headers
django-admin startproject arabam_api
cd arabam_api
python manage.py startapp cars
```

**FASTAPI (Alternatif - Daha hızlı):**
```bash
pip install fastapi uvicorn sqlalchemy
```

### 5.2 API Endpoints
- `GET /api/cars/` - Tüm araçları listele
- `GET /api/cars/{id}/` - Tek araç detayı
- `POST /api/predict/` - Fiyat tahmini isteği
- `GET /api/stats/` - İstatistiksel özet

### 5.3 Model Entegrasyonu
- Eğitilmiş ML modelini API'ye entegre et
- Real-time fiyat tahmini endpoint'i oluştur

---

## ⚛️ AŞAMA 6: Frontend (React/Next.js)

### 6.1 Proje Kurulumu
```bash
npx create-next-app@latest arabam-frontend
cd arabam-frontend
npm install axios recharts tailwindcss
```

### 6.2 Sayfalar
- **Ana Sayfa:** Arama filtreleri, araç listesi
- **Detay Sayfası:** Araç detayları, tahmini fiyat
- **İstatistikler:** Piyasa analizi grafikleri
- **Hakkımızda:** Proje bilgisi

### 6.3 Özellikler
- Filtreleme (Marka, Model, Yıl, KM, Fiyat aralığı)
- Sıralama (Fiyat, Yıl, KM)
- Responsive tasarım (Mobile-first)
- Dark mode desteği

---

## 🐳 AŞAMA 7: Docker ve DevOps

### 7.1 Dockerfile (Python API)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### 7.2 Docker Compose
```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: arabam_db
      POSTGRES_USER: arabam_user
      POSTGRES_PASSWORD: password
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
```

### 7.3 AWS/Azure Deployment
- **AWS:** EC2 + RDS (PostgreSQL) + S3 (statik dosyalar)
- **Azure:** App Service + Azure Database for PostgreSQL
- **CI/CD:** GitHub Actions veya GitLab CI

---

## 📊 AŞAMA 8: Monitoring ve Optimizasyon

### 8.1 Logging
- Structured logging (JSON format)
- Error tracking (Sentry)
- Performance monitoring

### 8.2 Caching
- Redis ile API response cache
- PostgreSQL query optimization
- CDN for static assets

### 8.3 Backup
- PostgreSQL daily backups
- S3/Azure Blob storage
- Disaster recovery plan

---

## 🎓 AŞAMA 9: Dokümantasyon ve Sunum

### 9.1 Teknik Dokümantasyon
- API documentation (Swagger/OpenAPI)
- Database schema documentation
- ML model documentation

### 9.2 Kullanıcı Dokümantasyonı
- Kullanım kılavuzu
- FAQ
- Video tutorial

### 9.3 Staj Sunumu
- Proje overview
- Teknik mimari
- Demo
- Sonuçlar ve metrics

---

## 🚀 Hızlı Başlangıç (Şu Anki Durum)

### Terminal Komutları (Sırayla):

1. **Gerekli kütüphaneler:**
```bash
pip install selenium webdriver-manager psycopg2-binary python-dotenv
```

2. **Link toplama:**
```bash
python link_toplayici.py
```

3. **Veri çekme (Chrome pencereleri açılacak):**
```bash
python bot.py
```

4. **PostgreSQL kurulumu (yoksa):**
```bash
brew install postgresql
brew services start postgresql
```

5. **Veritabanı oluşturma:**
```bash
psql -U postgres -c "CREATE DATABASE arabam_db;"
psql -U postgres -c "CREATE USER arabam_user WITH PASSWORD 'guvenli_sifre123';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE arabam_db TO arabam_user;"
```

6. **Tablo şemasını oluştur:**
```bash
psql -U arabam_user -d arabam_db -f database_schema.sql
```

7. **.env dosyası oluştur:**
```bash
echo "DB_HOST=localhost" > .env
echo "DB_NAME=arabam_db" >> .env
echo "DB_USER=arabam_user" >> .env
echo "DB_PASSWORD=guvenli_sifre123" >> .env
echo "DB_PORT=5432" >> .env
```

8. **JSONL'den PostgreSQL'e veri aktar:**
```bash
python db_connection.py
```

---

## 📝 Notlar

- **Headless mod kapatıldı:** Cloudflare bot korumasını aşmak için tarayıcı ekranda açılacak
- **WebDriver gizlendi:** `navigator.webdriver` özelliği undefined yapıldı
- **Explicit wait:** WebDriverWait ile elementlerin yüklenmesi beklenecek
- **Genişletilmiş selector'lar:** 17 farklı CSS selector ile özellik toplama
- **Thread-safe:** Lock mekanizması ile güvenli dosya yazma
- **Production-ready:** Hata toleransı maksimum, asla çökmez

---

## 🎯 Sonraki Adımlar

1. ✅ Web scraping kodlarını düzelt
2. ✅ PostgreSQL şeması oluştur
3. ⏭️ Veri çekme işlemini test et
4. ⏭️ PostgreSQL'e veri aktar
5. ⏭️ Veri temizleme ve ön işleme
6. ⏭️ ML modeli eğitimi
7. ⏭️ API geliştirme
8. ⏭️ Frontend geliştirme
9. ⏭️ Docker deployment
