# 📅 Degerinde - Günlük İlerleme Raporları

### 📊 11 Ağustos 2026 - Proje Kurulumu ve Model Optimizasyonu
1. **Veri Toplama (Data Pipeline):** İlk çekilen veri setindeki (outlier) tutarsızlıklar nedeniyle scraping algoritması yeniden yazıldı ve yaklaşık 150.000 satırlık temiz, yeni bir veri seti elde edildi.
2. **Makine Öğrenmesi Modeli:** Fiyat tahmini için *Random Forest*, *LightGBM* ve *XGBoost* mimarileri test edildi. Hata payı en düşük olan **XGBoost** modeli canlı ortama entegre edildi.
3. **Mimariler:** FastAPI backend ve Next.js frontend mimarisi kuruldu, uçtan uca bağlandı.
4. **DevOps:** İzole çalışma ortamı için Dockerize işlemleri tamamlandı, günlük rapor formatıyla GitHub reposu yöneticilerin takibine açıldı.
