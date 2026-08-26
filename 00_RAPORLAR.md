# Proje Raporları

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

---

## 📅 18 Ağustos Raporu

Bugün dünden planladığım gibi projenin domain ve sunucu yönlendirme işlerini hallettim. Sunucuya IP ve port yazıp girmek yerine doğrudan web sitesi gibi açılması için degerinde.duckdns.org adresini bağladım. Ardından SSL sertifikasını kurup siteyi güvenli bağlantıya (HTTPS) geçirdim. Nginx tarafında gerekli ayarları yapıp arayüz ile backend'i tek bir adreste topladım. Sunucuya aşırı yük binmesini engellemek için istek sınırlandırması ve sayfanın daha hızlı yüklenmesi için sıkıştırma ayarlarını açtım. Son olarak frontend tarafında mobil görünüm ve arama motoru etiketlerini güncelleyip Docker'ı sunucuda baştan derledim. Sistem şu an alan adı üzerinden sorunsuz çalışıyor.

Yarın model ve arayüz tarafında 13 parçalı ekspertiz (boya/değişen) durumlarını eklemeye odaklanacağım.

## 📅 19 Ağustos Raporu

Bugün ağırlıklı olarak backend ve arayüz entegrasyonundaki kritik hataları çözmeye odaklandım. Frontend tarafında 13 parçalı ekspertiz (boya/değişen) seçim ekranını sisteme bağladım, mobil görünümlerdeki grid kaymalarını düzelttim ve olası API kopmalarında sayfanın çökmesini engellemek için arayüze hata bildirim (toast) mekanizması ekledim. Tek kalan seçeneklerin otomatik seçilmesi özelliğindeki boş veri gönderme sorununu da hallettim. Backend tarafında ise yapay zeka modelinin tahmin sırasında Türkçe karakterli sütun isimleri yüzünden patlamasına sebep olan uyuşmazlığı giderdim. Ayrıca veritabanına fiyat tahmini loglanırken oluşan session hatasını çözdüm. Docker-compose tarafındaki inatçı güncelleme sorunlarından kurtulmak için sistemi sıfırdan temizleyip yeniden ayağa kaldırdım. Şu an arayüz ile yapay zeka modeli tam entegre, sorunsuz ve hızlı bir şekilde çalışıyor.

Sıradaki hedefim arka planda her gece çalışıp yeni ilanları toplayacak bir scraper (cron) yazmak ve yapay zekanın "Bu fiyatı neden verdiğini" açıklayabilmesi için (km düşük +15k, kaput değişen -30k gibi) SHAP entegrasyonunu sağlamak olacak. Modelin sunucuyu kapatmadan güncellenebilmesi (zero-downtime) için de bir endpoint eklemeyi planlıyorum.

---

## 📅 20 Ağustos Raporu

Bugün projede kurumsal tarafa (B2B) yönelik çok güzel güncellemeler yaptım. Öncelikle formu kullanıcıyı yormayacak şekilde inanılmaz sadeleştirdim; ekrandaki Motor Hacmi, Motor Gücü, Silindir Sayısı, Çekiş ve Kasa Tipi gibi karmaşık özellikleri tamamen kaldırdım. Bunun yerine arka planda kullanıcının seçtiği Marka/Seri/Model bilgisine göre bu verileri veritabanından çekip yapay zeka modeline sessizce gönderen bir sistem kurdum.

En büyük yenilik ise PDF raporu özelliği oldu. Galerici veya ekspertiz müşterileri için sonucu şık bir "Antetli Kağıt" gibi A4 formatında bilgisayara indiren bir buton ekledim. İlk başta PDF'i çizerken `html2canvas` kütüphanesi yeni nesil Tailwind renklerinde (oklch/lab) patladı ama onu çok daha modern bir SVG motoru olan `html-to-image` ile değiştirerek çözdüm. 

Bu güncellemeleri yaparken arayüzde bazı seçeneklerin (Renk, Kimden vs.) kaybolması ve canlıya çıkarken FastAPI sunucusunun koca modeli ve 140 bin satır veriyi RAM'e yüklemesi uzun sürdüğü için Nginx'in "502 Bad Gateway" atması gibi birkaç kriz yaşadım ama kodlara girip onları da düzelttim. Ayrıca veri temizliği yapıp veritabanında aynı markanın farklı yazımlarını (Citroen ve Citroën) tek isim altında birleştirdim. Şu an PDF çıktısı veren, sade ama arka planda tam güç çalışan harika bir ürün ortaya çıktı. Tüm bu emeğin sonucunu canlı olarak https://degerinde.duckdns.org/ adresinden inceleyebilirsiniz.

---

## 📅 21 Ağustos Raporu

Bugün projenin kararlılığını artırmak ve veri toplama süreçlerini optimize etmek üzerine çalıştım. Frontend tarafında form state yönetimini iyileştirerek formun istenmeyen durumlarda sıfırlanması sorununu çözdüm. PDF modülüne çoklu sayfa (multi-page) desteği ekleyerek uzun raporların eksiksiz oluşturulmasını sağladım.

Güvenlik tarafında, FastAPI backend'imize `slowapi` entegrasyonu ile dakikada 30 istek sınırı (rate limit) getirdim. Veri toplama (scraping) altyapımızı ise asenkron `curl_cffi` kütüphanesine geçirerek daha performanslı hale getirdim. İş yükünü Mac ve Oracle sunucuları arasında paylaştırarak, ban riski olmadan (anti-bot mekanizmalarıyla) çok daha hızlı veri çekebilecek bir yapı kurdum. Nginx ve Let's Encrypt SSL sertifika süreçlerini otomatize eden bir bash scripti hazırlayarak sunucu yapılandırmasını tamamladım.

---

## 📊 Haftalık Rapor (15 - 21 Ağustos)

Bu hafta, projemizi temel bir prototipten production ortamına hazır, kurumsal bir B2B ürününe dönüştürmek ana hedefimizdi. Arayüzü sadeleştirerek kullanıcıdan istenen karmaşık araç özelliklerini (motor hacmi, silindir sayısı vb.) arka planda otomatik tamamlayan bir API servisi devreye aldık. Kurumsal kullanıcılar için detaylı PDF ekspertiz raporu oluşturma özelliğini yayına aldık.

Sistem güvenliğini ve model kararlılığını artırmak için backend tarafında Pydantic doğrulama sınırlarını katılaştırdık; böylece hatalı verilerin modeli çökertmesini engelledik. Canlı sunucumuzu (Oracle) Docker iç ağıyla izole edip, Nginx ve SSL ile dışarıya güvenli şekilde açtık. Veri toplama botlarımızı iki sunucu üzerinden dağıtık çalışacak şekilde güncelledik. Önümüzdeki hafta, toplanan yeni ve kapsamlı verilerle yapay zeka modelimizi eğitmeye odaklanacağız.

---

## 📅 24 Ağustos Raporu

Hafta sonu boyunca veri toplama botlarını hem lokalde hem de Oracle sunucusunda kesintisiz çalıştırdım. Sunucunun performansını, Nginx ve Gunicorn loglarını takip ederek herhangi bir bellek sızıntısı veya 502/504 hatası olup olmadığını kontrol ettim. Ayrıca MLOps otomasyon betiğini (cron job ve venv entegrasyonu) arka planda test ederek sistemin her gece sıfır müdahaleyle yeni model eğitebilecek kararlılıkta olduğundan emin oldum.

Bugün ise sistemin genel kararlılığını ölçmek için son QA ve entegrasyon testlerini (`doomsday_test.py`, `qa_stress_test.py` gibi betiklerle) koştum. Ardından sitenin canlı linkini arkadaşlarıma atıp farklı telefon ve tarayıcılardan arayüzü, dinamik formları ve PDF raporu indirme butonunu test ettirdim. Gelen geri bildirimlere göre ufak tefek görsel kaymaları ve state hatalarını giderdim. Sistem şu an canlıda tamamen stabil ve sorunsuz bir şekilde yayında.

---

## 📅 25 Ağustos Raporu

Bugün genel olarak sistem üzerinde son manuel testleri gerçekleştirdim. Arayüzün farklı senaryolarda (hatalı veri girişleri, eksik ekspertiz bilgileri vb.) nasıl tepki verdiğini ve hata mesajlarını kontrol ettim. Ayrıca resmi staj raporunun taslağını oluşturarak hazırlıklarına başladım.

---

## 📅 26 Ağustos Raporu

Bugün resmi staj raporunun hazırlıklarını tamamladım ve raporu hazır hale getirdim. Modelin en son hangi veri boyutuyla eğitildiğine dair veritabanı analizlerini gerçekleştirdim.