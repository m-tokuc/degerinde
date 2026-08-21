"""
bot.py — Ana Otonom Veri Çekme Operasyonu (v2 — Tank Modu)
============================================================
linkler.txt dosyasındaki ilan linklerini okuyarak her birinden
TÜM verileri eksiksiz çeker ve dev_veriseti.jsonl dosyasına kaydeder.

v2 Farkları:
  - max_workers=2 (RAM güvenliği, cihaz kilitlenmez)
  - Her worker kalıcı (persistent) tek Chrome — URL güncelleme ile gezinir
  - JavaScript tabanlı doğrudan DOM extraction (güvenilir, hızlı)
  - Sağlam WebDriverWait + time.sleep (özellikler tam yüklenene kadar bekler)
  - Retry mekanizması: < 10 alan gelirse 2 kez daha dener
  - Zombi Chrome koruması: atexit ile garanti temizlik

Kullanım:
  python bot.py
"""

import os
import sys
import time
import json
import atexit
import signal
import threading
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


# ============================================================================
#  YAPILANDIRMA
# ============================================================================

# Cloudflare Bypass - Concurrency düşürüldü
PARALEL_ISCI = 4

# Giriş/çıkış dosyaları
LINK_DOSYASI = "cleaned_links.txt"
CIKTI_DOSYASI = "araba_verileri.jsonl"

# Bekleme süreleri (saniye) — Jitter
SAYFA_YUKLEME_BEKLEME = 1.5      # Sayfa açıldıktan sonra
SEKME_TIKLAMA_BEKLEME = 1        # Sekme tıklandıktan sonra
ILAN_ARASI_BEKLEME_MIN = 2.1     # İlanlar arası minimum bekleme (Cloudflare bypass)
ILAN_ARASI_BEKLEME_MAX = 5.7     # İlanlar arası maksimum bekleme

# Eksik veri durumunda retry
MIN_ALAN_SAYISI = 10             # Bu kadar alandan az gelirse retry
MAX_RETRY = 3                    # Maksimum tekrar deneme (3 defa)

# Ardışık hata tespiti — bu kadar arka arkaya 0 alan gelirse Chrome yeniden başlar
ARDISIK_HATA_LIMITI = 5

# Bellek koruması — bu kadar ilandan sonra Chrome otomatik yeniden başlatılır
# (Chrome uzun süre açık kalınca RAM şişer, bu onu önler)
PERIYODIK_RESTART_ILANI = 200

# Thread-safe mekanizmalar
dosya_kilidi = threading.Lock()
ilerleme_kilidi = threading.Lock()
ilerleme = {"basarili": 0, "hatali": 0, "toplam": 0}

# Zombi Chrome temizliği için global driver listesi
aktif_driverlar = []
driver_listesi_kilidi = threading.Lock()


# ============================================================================
#  ZOMBİ CHROME TEMİZLİĞİ
# ============================================================================

def tum_driverlari_kapat():
    """
    Program kapanırken (normal veya Ctrl+C) tüm Chrome'ları kesin kapatır.
    Arkada zombi chrome process kalmasını %100 engeller.
    """
    with driver_listesi_kilidi:
        for d in aktif_driverlar:
            try:
                d.quit()
            except Exception:
                pass
        aktif_driverlar.clear()
    print("\n🧹 Tüm Chrome pencereleri temizlendi.")

# Program kapanırken otomatik çağrılır
atexit.register(tum_driverlari_kapat)

# Ctrl+C sinyali — os._exit ile thread-safe temizlik
def sinyal_yakalayici(sig, frame):
    print("\n\n⚠️  Ctrl+C algılandı. Temizlik yapılıyor...")
    tum_driverlari_kapat()
    os._exit(0)  # sys.exit değil — thread içinden güvenli

signal.signal(signal.SIGINT, sinyal_yakalayici)


# ============================================================================
#  TARAYICI HAZIRLAMA
# ============================================================================

def tarayici_hazirla():
    """
    RAM-dostu, anti-bot korumalı Chrome tarayıcı.
    - Headless KAPALI (Cloudflare için)
    - Resimler kapalı (RAM + hız)
    - Tek seferlik açılır, URL güncellenerek kullanılır
    """
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Yarı-headless: Cloudflare'i daha kolay geçer

    # RAM tasarrufu ayarları
    # RAM tasarrufu ve Lightweight Mod (Images/CSS/Fonts Disabled)
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-image-loading")
    options.add_argument("--disable-css")
    options.add_argument("--disable-fonts")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")

    # Anti-bot önlemleri
    # Anti-bot önlemleri undetected-chromedriver tarafından otomatik halledilir.

    # Gerçekçi User-Agent (Rotasyonlu)
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")

    options.page_load_strategy = "eager"

    driver = uc.Chrome(options=options, version_main=151)
    driver.implicitly_wait(3)
    driver.set_page_load_timeout(30)

    # navigator.webdriver gizle
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    # Global listeye ekle (zombi koruması)
    with driver_listesi_kilidi:
        aktif_driverlar.append(driver)

    return driver


# ============================================================================
#  JAVASCRIPT TABANLI VERİ ÇEKME (Tüm verileri tek seferde çeker)
# ============================================================================

# Bu JavaScript fonksiyonu sayfa DOM'undan TÜM verileri çeker.
# Selenium find_elements'a göre çok daha güvenilir ve hızlıdır.
JS_OZELLIK_CEK = """
return (function() {
    var veri = {};

    // 1. SIDEBAR ÖZELLİKLER (div.product-properties-details ul li)
    //    Her <li> içinde 2 adet <span>: birinci=label, ikinci=değer
    var liElements = document.querySelectorAll('div.product-properties-details ul li');
    if (liElements.length === 0) {
        liElements = document.querySelectorAll('div[class*="product-properties"] ul li');
    }
    liElements.forEach(function(li) {
        var spans = li.querySelectorAll('span');
        if (spans.length >= 2) {
            var key = spans[0].innerText.trim();
            var val = spans[1].innerText.trim();
            if (key && val && key.length < 60) {
                veri[key] = val;
            }
        } else {
            // Span yoksa innerText'i satır bazlı böl
            var parts = li.innerText.trim().split('\\n');
            if (parts.length >= 2) {
                var key2 = parts[0].trim();
                var val2 = parts.slice(1).join(' ').trim();
                if (key2 && val2 && key2.length < 60) {
                    veri[key2] = val2;
                }
            }
        }
    });

    return veri;
})();
"""

JS_ARAC_BILGILERI_CEK = """
return (function() {
    var veri = {};

    // Araç Bilgileri sekmesindeki tablo satırlarını tara
    // Yapı: <table> veya <div> içinde satırlar, her satırda 2 hücre
    var rows = document.querySelectorAll(
        '#car-information tr, ' +
        '[class*="car-information"] tr, ' +
        '.product-tab-content tr, ' +
        'table tr'
    );

    rows.forEach(function(row) {
        var cells = row.querySelectorAll('td');
        if (cells.length >= 2) {
            var key = cells[0].innerText.trim();
            var val = cells[1].innerText.trim();
            if (key && val && key.length < 60 && key.length > 1) {
                veri[key] = val;
            }
        }
    });

    // Tablo yoksa, li elementlerini de tara
    if (Object.keys(veri).length === 0) {
        var liElements = document.querySelectorAll(
            '#car-information li, ' +
            '[class*="car-information"] li, ' +
            '.product-tab-content li'
        );
        liElements.forEach(function(li) {
            var spans = li.querySelectorAll('span');
            if (spans.length >= 2) {
                var key = spans[0].innerText.trim();
                var val = spans[1].innerText.trim();
                if (key && val && key.length < 60) {
                    veri[key] = val;
                }
            }
        });
    }

    return veri;
})();
"""

JS_BOYA_TRAMER_CEK = """
return (function() {
    var sonuc = {rapor: '', tramer_tutari: 'Belirtilmedi'};

    // Tüm aktif tab içeriğini tara
    var icerik = document.querySelector(
        '#damage-information, ' +
        '[id*="damage"], ' +
        '[class*="damage-information"], ' +
        '.product-tab-content'
    );

    if (icerik) {
        // Boya durumlarını kategorilere göre topla
        var kategoriler = ['Orjinal', 'Orijinal', 'Boyalı', 'Lokal boyalı', 'Lokal Boyalı', 'Değişmiş', 'Belirtilmemiş'];
        var parcalar = [];

        kategoriler.forEach(function(kat) {
            // Her kategoriyi ve altındaki parçaları bul
            var basliklar = icerik.querySelectorAll('strong, b, h3, h4, span[class*="title"], div[class*="title"]');
            basliklar.forEach(function(baslik) {
                if (baslik.innerText.trim().indexOf(kat) !== -1) {
                    // Kategori başlığının yanındaki/altındaki metni al
                    var parent = baslik.parentElement;
                    if (parent) {
                        var tumMetin = parent.innerText.trim();
                        if (tumMetin.length > 1) {
                            parcalar.push(tumMetin);
                        }
                    }
                }
            });
        });

        if (parcalar.length > 0) {
            sonuc.rapor = parcalar.join(' | ');
        } else {
            // Fallback: tüm içeriği al
            var tumMetin = icerik.innerText.trim();
            if (tumMetin.length > 5) {
                sonuc.rapor = tumMetin.replace(/\\n/g, ' | ');
            }
        }
    }

    // Tramer tutarını bul
    var tramerElements = document.querySelectorAll('*');
    for (var i = 0; i < tramerElements.length; i++) {
        var el = tramerElements[i];
        if (el.children.length === 0) { // Sadece yaprak düğümler
            var txt = el.innerText || '';
            if (txt.indexOf('Tramer') !== -1 && txt.indexOf('TL') !== -1) {
                sonuc.tramer_tutari = txt.trim();
                break;
            }
        }
    }

    // Daha spesifik Tramer arama
    if (sonuc.tramer_tutari === 'Belirtilmedi') {
        var allRows = document.querySelectorAll('tr, li, div');
        for (var j = 0; j < allRows.length; j++) {
            var rowText = allRows[j].innerText || '';
            if (rowText.match(/Tramer.*\\d.*TL/) || rowText.match(/\\d.*TL.*Tramer/)) {
                // Tramer tutarını parse et
                var match = rowText.match(/([\\d\\.]+)\\s*TL/);
                if (match) {
                    sonuc.tramer_tutari = match[0];
                    break;
                }
            }
        }
    }

    return sonuc;
})();
"""

JS_ACIKLAMA_CEK = """
return (function() {
    // Açıklama sekmesinin içeriğini bul
    var selectors = [
        '#description',
        '.description',
        'div[class*="description"]',
        '[id*="description"]',
        '.product-description',
        '.classified-description'
    ];

    for (var i = 0; i < selectors.length; i++) {
        try {
            var el = document.querySelector(selectors[i]);
            if (el) {
                var metin = el.innerText.trim();
                // Tab başlığını değil, gerçek içeriği al (en az 10 karakter)
                if (metin && metin.length > 10 && metin !== 'Açıklama') {
                    return metin;
                }
            }
        } catch(e) {}
    }

    // Fallback: aktif tab panelinin içeriğini al
    var tabPanels = document.querySelectorAll('.tab-pane.active, .product-tab-content > div:not([style*="none"])');
    for (var j = 0; j < tabPanels.length; j++) {
        var panel = tabPanels[j];
        var txt = panel.innerText.trim();
        if (txt && txt.length > 10 && txt !== 'Açıklama') {
            return txt;
        }
    }

    return 'Açıklama girilmemiş';
})();
"""

JS_DONANIM_CEK = """
return (function() {
    var selectors = [
        '#equipment-information',
        '[id*="equipment"]',
        '[class*="equipment"]',
        '.product-tab-content'
    ];

    for (var i = 0; i < selectors.length; i++) {
        try {
            var el = document.querySelector(selectors[i]);
            if (el) {
                var metin = el.innerText.trim();
                if (metin && metin.length > 10 && metin !== 'Donanım') {
                    return metin;
                }
            }
        } catch(e) {}
    }

    return 'Donanım bilgisi girilmemiş';
})();
"""


# ============================================================================
#  SEKMEYE TIKLAMA (JavaScript ile güvenli tıklama)
# ============================================================================

def sekmeye_tikla(driver, hedefler, bekleme=None):
    """
    Tab ID veya metin listesinden ilk eşleşeni JavaScript ile tıklar.
    Tıklamadan sonra içeriğin yüklenmesini bekler.
    """
    if bekleme is None:
        bekleme = SEKME_TIKLAMA_BEKLEME

    for hedef in hedefler:
        try:
            if hedef.startswith("#"):
                # CSS selector ile bul
                element = driver.find_element(By.CSS_SELECTOR, hedef)
            else:
                # Metin ile bul
                element = driver.find_element(
                    By.XPATH,
                    f"//a[contains(text(), '{hedef}')] | "
                    f"//span[contains(text(), '{hedef}')] | "
                    f"//button[contains(text(), '{hedef}')]"
                )

            # Görünür alana kaydır ve tıkla
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'}); "
                "arguments[0].click();",
                element,
            )
            time.sleep(bekleme)
            return True
        except Exception:
            continue

    return False


# ============================================================================
#  FİYAT ÇEKME
# ============================================================================

def fiyat_cek(driver):
    """Fiyat bilgisini sayfanın üst kısmındaki sticky header'dan çeker."""
    try:
        # Sticky header'daki fiyat (her zaman görünür)
        fiyat = driver.execute_script("""
            var selectors = [
                'span.product-price', 'div.product-price', '.product-price',
                '[class*="classified-price"]', '[class*="price"]'
            ];
            for (var i = 0; i < selectors.length; i++) {
                var el = document.querySelector(selectors[i]);
                if (el) {
                    var txt = el.innerText.trim();
                    if (txt && /\\d/.test(txt) && txt.length < 50) {
                        return txt.split('\\n')[0].trim();
                    }
                }
            }
            return 'Belirtilmedi';
        """)
        return fiyat
    except Exception:
        return "Belirtilmedi"


# ============================================================================
#  İLAN BAŞLIĞI ÇEKME
# ============================================================================

def baslik_cek(driver):
    """İlan başlığını <h1> etiketinden çeker."""
    try:
        baslik = driver.execute_script("""
            var h1 = document.querySelector('h1');
            return h1 ? h1.innerText.trim() : 'Belirtilmedi';
        """)
        return baslik if baslik else "Belirtilmedi"
    except Exception:
        return "Belirtilmedi"


# ============================================================================
#  TEK İLAN — TAM VERİ ÇEKME
# ============================================================================

def tek_ilan_tam_cek(driver, url):
    """
    Tek bir ilan sayfasından TÜM verileri eksiksiz çeker.
    Sırasıyla:
      1. Sayfa yükleme + bekleme
      2. Sidebar özellikleri (20 alan)
      3. Araç Bilgileri sekmesi (37 alan)
      4. Boya/Tramer sekmesi
      5. Açıklama sekmesi
      6. Donanım sekmesi
    """
    cekilen_veri = {"URL": url}

    try:
        # Sayfaya git (mevcut sekmede URL güncelle — yeni Chrome AÇMA)
        driver.get(url)

        # Sayfanın tam yüklenmesini bekle
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception:
            pass

        # JavaScript'in DOM'u doldurması için sağlam bekleme
        time.sleep(SAYFA_YUKLEME_BEKLEME)

        # BOŞ SAYFA / YANLIŞ SAYFA KONTROLÜ
        # driver.get() başarısız olduysa veya Chrome yeni sekme sayfasında kaldıysa tespit et
        try:
            mevcut_url = driver.current_url
        except Exception:
            # Session tamamen ölmüş — invalid session id
            cekilen_veri["Hata"] = "invalid_session_olu_driver_yeniden_baslatilmali"
            return cekilen_veri

        if not mevcut_url or "arabam.com" not in mevcut_url:
            cekilen_veri["Hata"] = f"Sayfa_acilmadi_mevcut_url={mevcut_url[:80] if mevcut_url else 'BOS'}"
            return cekilen_veri

        # Cloudflare kontrolü
        baslik_text = driver.title.lower()
        if "just a moment" in baslik_text or "attention" in baslik_text:
            time.sleep(10)
            if "just a moment" in driver.title.lower():
                cekilen_veri["Hata"] = "Cloudflare_engeli"
                return cekilen_veri

        # --- 1. İLAN BAŞLIĞI ---
        cekilen_veri["Baslik"] = baslik_cek(driver)

        # --- 2. FİYAT ---
        cekilen_veri["Fiyat"] = fiyat_cek(driver)

        # --- 3. SIDEBAR ÖZELLİKLER (product-properties-details) ---
        #     Sayfanın sağ panelindeki temel özellikler: İlan No, Marka, Model, Yıl, KM...
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.product-properties-details ul li")
                )
            )
        except Exception:
            # Element bulunamazsa 3 sn daha bekle
            time.sleep(3)

        sidebar_veri = driver.execute_script(JS_OZELLIK_CEK)
        if isinstance(sidebar_veri, dict):
            cekilen_veri.update(sidebar_veri)

        # --- 4. ARAÇ BİLGİLERİ SEKMESİ ---
        #     Genel Bakış, Motor/Performans, Yakıt, Boyut/Kapasite (37 alan)
        tiklandi = sekmeye_tikla(driver, [
            "#head-tab-car-information",
            "Araç Bilgileri",
            "Araç bilgileri",
        ])

        if tiklandi:
            arac_bilgi = driver.execute_script(JS_ARAC_BILGILERI_CEK)
            if isinstance(arac_bilgi, dict):
                for k, v in arac_bilgi.items():
                    if k not in cekilen_veri:
                        cekilen_veri[k] = v

        # --- 5. BOYA, DEĞİŞEN VE TRAMER SEKMESİ ---
        tiklandi = sekmeye_tikla(driver, [
            "#head-tab-damage-information",
            "Boya, Değişen ve Tramer",
            "Boya, Değişen",
        ])

        if tiklandi:
            tramer_veri = driver.execute_script(JS_BOYA_TRAMER_CEK)
            if isinstance(tramer_veri, dict):
                cekilen_veri["Boya_Degisen_Tramer"] = tramer_veri.get("rapor", "Girilmemiş")
                cekilen_veri["Tramer_Tutari"] = tramer_veri.get("tramer_tutari", "Belirtilmedi")
        else:
            cekilen_veri["Boya_Degisen_Tramer"] = "Sekme bulunamadı"
            cekilen_veri["Tramer_Tutari"] = "Belirtilmedi"

        # --- 6. AÇIKLAMA SEKMESİ ---
        tiklandi = sekmeye_tikla(driver, [
            "#head-tab-description",
            "Açıklama",
        ])

        if tiklandi:
            aciklama = driver.execute_script(JS_ACIKLAMA_CEK)
            cekilen_veri["Satici_Aciklamasi"] = aciklama if aciklama else "Açıklama girilmemiş"
        else:
            cekilen_veri["Satici_Aciklamasi"] = "Sekme bulunamadı"

        # --- 7. DONANIM SEKMESİ ---
        tiklandi = sekmeye_tikla(driver, [
            "#head-tab-equipment-information",
            "Donanım",
        ])

        if tiklandi:
            donanim = driver.execute_script(JS_DONANIM_CEK)
            cekilen_veri["Donanim"] = donanim if donanim else "Donanım bilgisi girilmemiş"
        else:
            cekilen_veri["Donanim"] = "Sekme bulunamadı"

        return cekilen_veri

    except Exception as e:
        cekilen_veri["Hata"] = str(e)[:200]
        return cekilen_veri


# ============================================================================
#  RETRY MEKANİZMASI
# ============================================================================

def tek_ilan_retry_ile(driver, url):
    """
    Tek bir ilanı çeker. Eğer veri eksik gelirse (< MIN_ALAN_SAYISI alan),
    sayfayı yeniden yükleyip tekrar dener.
    Driver ölmüşse (invalid session) hemen döner — worker seviyesinde yeniden başlatılır.
    """
    for deneme in range(1, MAX_RETRY + 2):  # 1. deneme + MAX_RETRY tekrar
        veri = tek_ilan_tam_cek(driver, url)

        # Driver ölmüşse retry anlamsız — hemen döndür
        hata_mesaji = veri.get("Hata", "")
        if "invalid_session" in hata_mesaji or "Sayfa_acilmadi" in hata_mesaji:
            return veri

        alan_sayisi = len([k for k in veri if k not in ("URL", "Hata")])

        if alan_sayisi >= MIN_ALAN_SAYISI:
            return veri  # Yeterli veri geldi

        if deneme <= MAX_RETRY:
            print(f"      ⚠️  Sadece {alan_sayisi} alan geldi. Tekrar deneniyor ({deneme}/{MAX_RETRY})...")
            # Rastgele bekleme (Jitter) ekle
            time.sleep(random.uniform(3.5, 7.2))
        else:
            print(f"      ⚠️  {MAX_RETRY} denemeden sonra sadece {alan_sayisi} alan alınabildi.")

    return veri


# ============================================================================
#  WORKER FONKSİYONU (Kalıcı Chrome — URL güncelleme ile gezinir)
# ============================================================================

def chrome_yeniden_baslat(driver, worker_id):
    """
    Ölü veya takılmış Chrome'u kapatıp yeni bir tane başlatır.
    Eski driver'ı global listeden çıkarır.
    """
    # Eski driver'ı temizle
    try:
        with driver_listesi_kilidi:
            if driver in aktif_driverlar:
                aktif_driverlar.remove(driver)
        driver.quit()
    except Exception:
        pass

    # Yenisini başlat
    try:
        yeni_driver = tarayici_hazirla()
        print(f"  🔄 Worker-{worker_id}: Chrome yeniden başlatıldı.")
        return yeni_driver
    except Exception:
        print(f"  ❌ Worker-{worker_id}: Chrome başlatılamadı!")
        return None


def worker(url_listesi, worker_id):
    """
    Kalıcı tek Chrome penceresi açar. Linkleri aynı pencerede
    URL güncelleyerek gezinir. İşlem bitince driver.quit() çağırır.

    Güvenlik mekanizmaları:
      - URL validasyonu (boş/geçersiz satırları atlar)
      - Boş sayfa tespiti (arabam.com'da olup olmadığını kontrol eder)
      - Ardışık hata tespiti (5 arka arkaya başarısız → Chrome restart)
      - invalid session id → otomatik Chrome restart
    """
    driver = None
    basarili = 0
    hatali = 0
    ardisik_hata = 0          # Ardışık başarısız ilan sayacı
    restart_sonrasi_sayac = 0  # Son Chrome restarttan bu yana işlenen ilan

    try:
        driver = tarayici_hazirla()
        print(f"  🟢 Worker-{worker_id}: Chrome başlatıldı. {len(url_listesi)} ilan işlenecek.")

        for i, url in enumerate(url_listesi, 1):
            # --- URL VALİDASYONU ---
            if not url or not url.startswith("http"):
                print(f"  [W{worker_id}] [{i}/{len(url_listesi)}] ⏭️  Geçersiz URL atlandı: '{url[:50] if url else 'BOS'}'")
                continue

            try:
                veri = tek_ilan_retry_ile(driver, url)

                # --- ÖLÜ SESSION TESPİTİ ---
                hata_mesaji = veri.get("Hata", "")
                if "invalid_session" in hata_mesaji or "Sayfa_acilmadi" in hata_mesaji:
                    print(f"  [W{worker_id}] 💀 Chrome session öldü! Yeniden başlatılıyor...")
                    driver = chrome_yeniden_baslat(driver, worker_id)
                    if driver is None:
                        print(f"  ❌ Worker-{worker_id} durduruluyor.")
                        break
                    # Session yenilendi, bu URL'yi tekrar dene
                    veri = tek_ilan_retry_ile(driver, url)

                alan_sayisi = len([k for k in veri if k not in ("URL", "Hata")])

                if "Hata" not in veri and alan_sayisi >= 5:
                    # Thread-safe dosyaya yaz
                    with dosya_kilidi:
                        with open(CIKTI_DOSYASI, "a", encoding="utf-8") as f:
                            f.write(json.dumps(veri, ensure_ascii=False) + "\n")
                    basarili += 1
                    ardisik_hata = 0  # Başarılı ilan → sayacı sıfırla
                    restart_sonrasi_sayac += 1
                    durum = f"✅ {alan_sayisi} alan"
                else:
                    # Hatalı/eksik veriyi KAYDETME (kaldığı yerden devam'ı bozmasın)
                    hatali += 1
                    ardisik_hata += 1
                    durum = f"⚠️  {alan_sayisi} alan (eksik)"

                # İlerleme güncelle
                with ilerleme_kilidi:
                    if "✅" in durum:
                        ilerleme["basarili"] += 1
                    else:
                        ilerleme["hatali"] += 1
                    toplam_islenen = ilerleme["basarili"] + ilerleme["hatali"]

                print(
                    f"  [W{worker_id}] [{i}/{len(url_listesi)}] "
                    f"{durum} | Genel: {toplam_islenen}/{ilerleme['toplam']}"
                )

                # --- ARDIŞIK HATA TESPİTİ ---
                if ardisik_hata >= ARDISIK_HATA_LIMITI:
                    print(f"  [W{worker_id}] 🔥 {ARDISIK_HATA_LIMITI} ardışık hata! Chrome yeniden başlatılıyor...")
                    driver = chrome_yeniden_baslat(driver, worker_id)
                    if driver is None:
                        print(f"  ❌ Worker-{worker_id} durduruluyor.")
                        break
                    ardisik_hata = 0

                # --- PERİYODİK CHROME RESTART (BELLEK KORUMASI) ---
                if restart_sonrasi_sayac >= PERIYODIK_RESTART_ILANI:
                    print(f"  [W{worker_id}] 🧹 {PERIYODIK_RESTART_ILANI} ilan işlendi — Chrome RAM temizliği için yeniden başlatılıyor...")
                    driver = chrome_yeniden_baslat(driver, worker_id)
                    if driver is None:
                        print(f"  ❌ Worker-{worker_id} durduruluyor.")
                        break
                    restart_sonrasi_sayac = 0

                # Her 50 ilandan sonra detaylı rapor
                if i % 50 == 0:
                    with ilerleme_kilidi:
                        b = ilerleme["basarili"]
                        h = ilerleme["hatali"]
                    print(f"\n  📊 DURUM RAPORU: ✅ {b} başarılı | ⚠️  {h} eksik | "
                          f"Toplam: {b + h}/{ilerleme['toplam']}\n")

            except Exception as e:
                hatali += 1
                ardisik_hata += 1
                hata_str = str(e)
                print(f"  [W{worker_id}] ❌ Hata: {hata_str[:80]}")

                # invalid session veya connection refused → Chrome öldü
                if "invalid session" in hata_str or "connection refused" in hata_str or "no such session" in hata_str:
                    print(f"  [W{worker_id}] 💀 Chrome çöktü! Yeniden başlatılıyor...")
                    driver = chrome_yeniden_baslat(driver, worker_id)
                    if driver is None:
                        break
                    ardisik_hata = 0
                else:
                    # Chrome hayatta ama sayfa hatalı — about:blank ile temizle
                    try:
                        driver.get("about:blank")
                        time.sleep(2)
                    except Exception:
                        driver = chrome_yeniden_baslat(driver, worker_id)
                        if driver is None:
                            break
                        ardisik_hata = 0

            # İlanlar arası bekleme (ban koruması)
            time.sleep(random.uniform(ILAN_ARASI_BEKLEME_MIN, ILAN_ARASI_BEKLEME_MAX))

    except Exception as e:
        print(f"  ❌ Worker-{worker_id} kritik hata: {e}")

    finally:
        if driver:
            try:
                with driver_listesi_kilidi:
                    if driver in aktif_driverlar:
                        aktif_driverlar.remove(driver)
                driver.quit()
            except Exception:
                pass

    print(f"  🏁 Worker-{worker_id} tamamlandı: ✅ {basarili} | ⚠️  {hatali}")
    return basarili, hatali


# ============================================================================
#  KALDIĞI YERDEN DEVAM ETME
# ============================================================================

def islenmis_urlleri_oku():
    """
    Daha önce BAŞARIYLA işlenmiş URL'leri okur (kaldığı yerden devam).
    Sadece hatasız ve yeterli alan içeren kayıtları 'işlenmiş' sayar.
    Hatalı kayıtlar (invalid session, 0 alan vs.) tekrar denenecek.
    """
    islenmis = set()
    hatali_sayisi = 0
    if os.path.exists(CIKTI_DOSYASI):
        try:
            with open(CIKTI_DOSYASI, "r", encoding="utf-8") as f:
                for satir in f:
                    try:
                        veri = json.loads(satir.strip())
                        url = veri.get("URL", "")
                        if not url:
                            continue

                        # Sadece başarılı kayıtları atla
                        # Hata içerenleri ve çok az alan içerenleri TEKRAR dene
                        if "Hata" in veri:
                            hatali_sayisi += 1
                            continue

                        alan_sayisi = len([k for k in veri if k != "URL"])
                        if alan_sayisi >= 5:
                            islenmis.add(url)
                        else:
                            hatali_sayisi += 1

                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    if hatali_sayisi > 0:
        print(f"  🔄 {hatali_sayisi} hatalı/eksik kayıt bulundu — bunlar tekrar denenecek.")

    return islenmis


# ============================================================================
#  ANA ÇALIŞTIRMA
# ============================================================================

if __name__ == "__main__":
    print(f"\n{'=' * 70}")
    print(f"  🤖 ARABAM.COM OTONOM VERİ ÇEKME — TANK MODU v2")
    print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 70}\n")

    # linkler.txt kontrolü
    if not os.path.exists(LINK_DOSYASI):
        print(f"❌ HATA: '{LINK_DOSYASI}' bulunamadı!")
        print(f"   Önce link_toplayici.py'yi çalıştırın.")
        sys.exit(1)

    # Linkleri oku (boş satırları ve geçersiz URL'leri filtrele)
    with open(LINK_DOSYASI, "r", encoding="utf-8") as f:
        ham_satirlar = [satir.strip() for satir in f]

    tum_linkler = [url for url in ham_satirlar if url and url.startswith("http")]
    filtrelenen = len(ham_satirlar) - len(tum_linkler)
    if filtrelenen > 0:
        print(f"  ⚠️  {filtrelenen} boş/geçersiz satır filtrelendi.")

    print(f"  📂 '{LINK_DOSYASI}': {len(tum_linkler)} link okundu.")

    # Kaldığı yerden devam
    islenmis = islenmis_urlleri_oku()
    if islenmis:
        print(f"  📊 Daha önce {len(islenmis)} ilan işlenmiş (atlanacak).")
        tum_linkler = [url for url in tum_linkler if url not in islenmis]
        print(f"  📊 Kalan: {len(tum_linkler)} ilan")

    if not tum_linkler:
        print("\n  ✅ Tüm ilanlar zaten işlenmiş!")
        sys.exit(0)

    ilerleme["toplam"] = len(tum_linkler)

    print(f"\n  ⚙️  Ayarlar:")
    print(f"     Paralel Chrome  : {PARALEL_ISCI}")
    print(f"     İşlenecek ilan  : {len(tum_linkler)}")
    print(f"     Min alan sayısı : {MIN_ALAN_SAYISI} (altında retry)")
    print(f"     Max retry       : {MAX_RETRY}")
    print(f"     Çıktı           : {CIKTI_DOSYASI}")
    print()

    # URL'leri worker'lara dağıt
    url_paketleri = [[] for _ in range(PARALEL_ISCI)]
    for idx, url in enumerate(tum_linkler):
        url_paketleri[idx % PARALEL_ISCI].append(url)

    for i, paket in enumerate(url_paketleri):
        print(f"  📦 Worker-{i}: {len(paket)} ilan")

    print(f"\n  🚀 Operasyon başlatılıyor...\n")

    baslangic = time.time()

    with ThreadPoolExecutor(max_workers=PARALEL_ISCI) as executor:
        futures = {
            executor.submit(worker, url_paketleri[i], i): i
            for i in range(PARALEL_ISCI)
        }

        toplam_basarili = 0
        toplam_hatali = 0

        for future in as_completed(futures):
            wid = futures[future]
            try:
                b, h = future.result()
                toplam_basarili += b
                toplam_hatali += h
            except Exception as e:
                print(f"  ❌ Worker-{wid} sonuç alınamadı: {e}")

    # Son özet
    toplam_sure = time.time() - baslangic
    saat = int(toplam_sure // 3600)
    dakika = int((toplam_sure % 3600) // 60)
    saniye = int(toplam_sure % 60)

    print(f"\n{'=' * 70}")
    print(f"  🏁 OPERASYON TAMAMLANDI!")
    print(f"{'=' * 70}")
    print(f"  ✅ Başarılı (≥{MIN_ALAN_SAYISI} alan) : {toplam_basarili}")
    print(f"  ⚠️  Eksik veri                : {toplam_hatali}")
    print(f"  ⏱️  Süre                       : {saat}s {dakika}dk {saniye}sn")
    print(f"  📂 Çıktı                       : {CIKTI_DOSYASI}")

    if os.path.exists(CIKTI_DOSYASI):
        boyut_mb = os.path.getsize(CIKTI_DOSYASI) / (1024 * 1024)
        print(f"  💾 Dosya boyutu                : {boyut_mb:.2f} MB")

    print(f"{'=' * 70}\n")