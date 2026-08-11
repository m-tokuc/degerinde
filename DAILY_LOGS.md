# 📅 Degerinde - Günlük İlerleme Raporları (Daily Logs)

Bu dosya, proje sürecinde gerçekleştirilen teknik geliştirmeleri ve tamamlanan görevleri gün bazında takip etmek amacıyla oluşturulmuştur.

### 📊 1. Gün (20 Temmuz 2026) - Proje Planlaması ve Mimari Tasarım
* Uçtan uca MLOps mimarisinin temel bileşenleri (Backend, Frontend, ML Motoru) belirlendi.
* Projede kullanılacak teknoloji yığını (FastAPI, Next.js, XGBoost) standartlaştırılarak yerel geliştirme ortamı kuruldu.

### 📊 2. Gün (21 Temmuz 2026) - Veri Kaynakları ve DOM Analizi
* Araç verilerinin toplanacağı kaynaklar incelendi. Web scraping işlemleri için hedef HTML yapıları ve DOM elementleri analiz edildi.

### 📊 3. Gün (22 Temmuz 2026) - Temel Scraping Algoritmasının Yazılması
* Python (Requests/BeautifulSoup) kullanılarak veri çekme betikleri oluşturuldu. Sayfalama yapıları çözümlendi.

### 📊 4. Gün (23 Temmuz 2026) - Veri Toplama Fazı 1
* Hedef sunucuların istek sınırlarına takılmamak için betiklere gecikme (delay) mekanizmaları eklendi.

### 📊 5. Gün (24 Temmuz 2026) - İlk Veri Setinin Elde Edilmesi
* Yaklaşık 17.000 satırlık ilk veri seti elde edildi ve kaydedildi.

### 📊 6. Gün (27 Temmuz 2026) - Keşifsel Veri Analizi (EDA)
* Elde edilen veri üzerinde analizler yapıldı. Kilometre ve fiyat sütunlarında eksik veriler ve hatalı piyasa girişleri (outlier) tespit edildi.

### 📊 7. Gün (28 Temmuz 2026) - Algoritma Revizyonu
* Model güvenilirliğini sağlamak adına veri çekme algoritması daha kapsamlı parametreler içerecek şekilde baştan yazıldı.

### 📊 8. Gün (29 Temmuz 2026) - Scraping Fazı 2 Başlangıcı
* Güncellenen algoritma ile geniş çaplı veri kazıma başlatıldı. Kesintilere karşı parçalı (batch) kaydetme yapısı kuruldu.

### 📊 9. Gün (30 Temmuz 2026) - Veri Kazıma Optimizasyonu
* Bozuk HTML yapısına sahip sayfalarda betiğin çökmesini engelleyen güvenlik blokları (try-except) geliştirildi.

### 📊 10. Gün (31 Temmuz 2026) - Büyük Veri Setinin Elde Edilmesi
* Parçalı veriler birleştirilerek Türkiye pazarını yansıtan temiz (~150.000 satırlık) final veri seti oluşturuldu.

### 📊 11. Gün (3 Ağustos 2026) - Veri Ön İşleme (Preprocessing)
* Fiyat ve kilometre sütunları sayısal değerlere dönüştürüldü. Eksik (NaN) değerler temizlendi.

### 📊 12. Gün (4 Ağustos 2026) - Özellik Mühendisliği (Feature Engineering)
* Kategorik değişkenler için One-Hot ve Label Encoding işlemleri uygulandı. Veri seti Eğitim ve Test olarak bölündü.

### 📊 13. Gün (5 Ağustos 2026) - Model Eğitimi (Random Forest & LightGBM)
* Hazırlanan veri seti üzerinde Random Forest ve LightGBM mimarileri eğitildi. Hata metrikleri incelendi.

### 📊 14. Gün (6 Ağustos 2026) - Model Eğitimi (XGBoost) ve Final Kararı
* Aynı veri seti XGBoost ile eğitildi. En düşük hatayı veren ve en kararlı model olan XGBoost canlı sistem modeli olarak dışa aktarıldı.

### 📊 15. Gün (7 Ağustos 2026) - Backend API Geliştirmesi
* Eğitilen model için FastAPI kullanılarak asenkron REST API uç noktaları yazıldı.

### 📊 16. Gün (10 Ağustos 2026) - Frontend Entegrasyonu (Next.js)
* Next.js ile modern tasarımlı web arayüzü kodlandı. Backend ile API entegrasyonu başarıyla sağlandı.

### 📊 17. Gün (11 Ağustos 2026) - DevOps, Kod Temizliği ve Canlıya Alma
* Servisler için `Dockerfile` ve `docker-compose.yml` yapılandırmaları tamamlandı.
* Sistem kalıntıları ve gereksiz dosyalar kalıcı olarak temizlendi.
* Kodlar GitHub'a pushlandı. Azure üzerinde canlıya alma hazırlıklarına başlandı.
