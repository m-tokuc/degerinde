# Proje Raporları

---

## 📅 13 Ağustos Raporu

Bugün projemizi lokalden canlı sunucuya taşıma işlerine başladım. İlk olarak frontend (Next.js) ve backend (FastAPI) için ayrı ayrı Dockerfile dosyaları yazdım. Sonra PostgreSQL veritabanını da dahil edip hepsini tek bir docker-compose dosyasında birleştirdim ki sunucuda tek komutla çalışabilsinler. Yapay zeka modelinin dosya yollarını da yeni klasör yapısına göre güncelledim. Günün sonunda Oracle Cloud üzerinden ücretsiz bir Ubuntu sunucu açtım, SSH ile terminalden bağlanıp temel kurulumları hallettim.

---

## 📅 14 Ağustos Raporu

Bugün projeyi Oracle sunucusunda çalıştırırken epey hatayla boğuştum. Docker ile sistemi ayağa kaldırdığımda Next.js arayüzünden backend'e istek atarken bağlantı reddedildi hatası aldım. Bayağı araştırdıktan sonra Oracle'ın güvenlik duvarından 8000 portunu dışarı açmam gerektiğini buldum, sunucu üzerinden port izinlerini ayarlayıp bu sorunu çözdüm. Arayüzü de epey toparladım; eski tasarım yerine daha sade, beyaz ağırlıklı bir tasarıma geçtim. Marka seçince modelin gelmesi gibi dinamik formları ekledim. Arayüz kısmını hallettim ama günün sonunda backend loglarına bakarken "araclar" tablosunun bulunamadığına dair bir SQL hatası (relation does not exist) aldım. Veritabanı boş olduğu için seçenekler yüklenmedi, haftayı bu sorunla kapatıyorum.

---

## 📊 Haftalık Rapor (10 - 14 Ağustos)

Bu hafta genel olarak geliştirdiğim araç değerleme projesini bulut ortamına, yani canlıya taşıma süreçleriyle ilgilendim. Hafta başında lokalde Next.js arayüzü ve FastAPI backend'inin sorunsuz haberleştiğinden emin olduktan sonra projeyi Docker ile paketledim. Sonrasında Oracle Cloud üzerinde kurduğum Ubuntu sunucuya tüm dosyaları taşıdım. Canlıya alma kısmında özellikle port izinleri ve Docker içindeki bağlantı sorunları beni epey oyaladı ama araştırarak çözdüm. Arayüz tasarımını da baştan yenileyip daha profesyonel bir hale getirdim ve dinamik formları bağladım. Haftanın sonunda sistemi sunucuda ayağa kaldırmayı başardım ancak PostgreSQL veritabanındaki tabloları henüz oluşturmadığım için backend tarafında bir SQL hatası alıyorum. Önümüzdeki haftanın ilk işi veritabanı şemasını sunucuda oluşturup araç verilerini içeri aktarmak ve projeyi tam anlamıyla çalışır duruma getirmek olacak.

---

## 📅 17 Ağustos Raporu

Bugün projenin frontend tarafını hazır şablon görüntüsünden kurtarmaya odaklandım. Klasik dönen yükleme ikonu yerine SVG ve CSS kullanarak arabayı tarayan bir lazer animasyonu ekledim, genel logo ve tasarımları biraz daha modern hale getirdim. Ayrıca kullanıcı kilometre girerken yanlışlıkla fazla sıfır koyup hata yapmasın diye formlara binlik ayracı maskelemesi koydum.

Backend tarafında ise XGBoost modelinin uç verilerde sapıtıp eksi veya çok mantıksız fiyatlar vermesini engellemek için kod tarafına min ve max fiyat sınırları (hurda limiti vs.) ekledim. Son olarak da `test_model_edge_cases.py` adında bir script yazıp modeli çok yüksek km, çok eski araç veya 0 km lüks araç gibi uç senaryolarla test ettim. Sistem outlier (aykırı) durumlarını patlamadan ve mantıklı bir şekilde yakalayabiliyor.

Yarın domain yönlendirmeleri ve nginx/sunucu ayarlarına geçeceğim.
