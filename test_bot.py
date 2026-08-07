"""
test_bot.py — Tekli İlan Doğrulama ve Kalite Kontrol Sistemi (v2)
=================================================================
Tek bir ilan linkini ziyaret eder, TÜM verileri JavaScript ile çeker
ve terminale okunaklı JSON formatında yazdırır.

Dosyaya hiçbir şey YAZMAZ. bot.py'nin aynı extraction mantığını kullanır.

Kullanım:
  1. TEST_URL değişkenine ilan linkini yaz
  2. python test_bot.py
  3. Terminaldeki JSON çıktısını incele
"""

import time
import random
import json
import sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ============================================================================
#  TEST EDİLECEK İLAN LİNKİ — BURAYA KENDİ LİNKİNİ YAZ
# ============================================================================

TEST_URL = "https://www.arabam.com/ilan/sahibinden-satilik-fiat-egea-1-3-multijet-urban-plus/sahibinden-fiat-egea-1-3-multijet-urban-plus-2020-model-57-000-km-gri-titanyum/42264509"


# ============================================================================
#  BEKLEME SÜRELERİ
# ============================================================================

SAYFA_YUKLEME_BEKLEME = 5   # Sayfa açıldıktan sonra (saniye)
SEKME_TIKLAMA_BEKLEME = 3   # Sekme tıklandıktan sonra (saniye)


# ============================================================================
#  TARAYICI HAZIRLAMA (Headless KAPALI)
# ============================================================================

def tarayici_hazirla():
    """Ekranda görünür Chrome penceresi, anti-bot korumalı."""
    options = Options()

    # Headless KAPALI
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--start-maximized")

    # Anti-bot
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )

    options.page_load_strategy = "normal"

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# ============================================================================
#  JAVASCRIPT TABANLI VERİ ÇEKME (bot.py ile birebir aynı)
# ============================================================================

JS_OZELLIK_CEK = """
return (function() {
    var veri = {};
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
            var parts = li.innerText.trim().split('\\n');
            if (parts.length >= 2) {
                veri[parts[0].trim()] = parts.slice(1).join(' ').trim();
            }
        }
    });
    return veri;
})();
"""

JS_ARAC_BILGILERI_CEK = """
return (function() {
    var veri = {};
    var rows = document.querySelectorAll(
        '#car-information tr, [class*="car-information"] tr, .product-tab-content tr, table tr'
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
    if (Object.keys(veri).length === 0) {
        var liElements = document.querySelectorAll(
            '#car-information li, [class*="car-information"] li'
        );
        liElements.forEach(function(li) {
            var spans = li.querySelectorAll('span');
            if (spans.length >= 2) {
                veri[spans[0].innerText.trim()] = spans[1].innerText.trim();
            }
        });
    }
    return veri;
})();
"""

JS_BOYA_TRAMER_CEK = """
return (function() {
    var sonuc = {rapor: '', tramer_tutari: 'Belirtilmedi'};
    var icerik = document.querySelector(
        '#damage-information, [id*="damage"], [class*="damage-information"], .product-tab-content'
    );
    if (icerik) {
        var kategoriler = ['Orjinal', 'Orijinal', 'Boyalı', 'Lokal boyalı', 'Lokal Boyalı', 'Değişmiş', 'Belirtilmemiş'];
        var parcalar = [];
        kategoriler.forEach(function(kat) {
            var basliklar = icerik.querySelectorAll('strong, b, h3, h4, span[class*="title"], div[class*="title"]');
            basliklar.forEach(function(baslik) {
                if (baslik.innerText.trim().indexOf(kat) !== -1) {
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
            var tumMetin = icerik.innerText.trim();
            if (tumMetin.length > 5) {
                sonuc.rapor = tumMetin.replace(/\\n/g, ' | ');
            }
        }
    }
    // Tramer tutarı
    var allRows = document.querySelectorAll('tr, li, div');
    for (var j = 0; j < allRows.length; j++) {
        var rowText = allRows[j].innerText || '';
        if (rowText.match && rowText.match(/Tramer.*\\d.*TL/)) {
            var match = rowText.match(/([\\d\\.]+)\\s*TL/);
            if (match) { sonuc.tramer_tutari = match[0]; break; }
        }
    }
    return sonuc;
})();
"""

JS_ACIKLAMA_CEK = """
return (function() {
    var selectors = ['#description', '.description', 'div[class*="description"]',
                     '[id*="description"]', '.product-description'];
    for (var i = 0; i < selectors.length; i++) {
        try {
            var el = document.querySelector(selectors[i]);
            if (el) {
                var metin = el.innerText.trim();
                if (metin && metin.length > 10 && metin !== 'Açıklama') {
                    return metin;
                }
            }
        } catch(e) {}
    }
    var tabPanels = document.querySelectorAll('.tab-pane.active, .product-tab-content > div:not([style*="none"])');
    for (var j = 0; j < tabPanels.length; j++) {
        var txt = tabPanels[j].innerText.trim();
        if (txt && txt.length > 10 && txt !== 'Açıklama') return txt;
    }
    return 'Açıklama girilmemiş';
})();
"""

JS_DONANIM_CEK = """
return (function() {
    var selectors = ['#equipment-information', '[id*="equipment"]',
                     '[class*="equipment"]', '.product-tab-content'];
    for (var i = 0; i < selectors.length; i++) {
        try {
            var el = document.querySelector(selectors[i]);
            if (el) {
                var metin = el.innerText.trim();
                if (metin && metin.length > 10 && metin !== 'Donanım') return metin;
            }
        } catch(e) {}
    }
    return 'Donanım bilgisi girilmemiş';
})();
"""


# ============================================================================
#  SEKMEYE TIKLAMA
# ============================================================================

def sekmeye_tikla(driver, hedefler):
    """Tab ID veya metin ile eşleşen ilk sekmeyi tıklar."""
    for hedef in hedefler:
        try:
            if hedef.startswith("#"):
                element = driver.find_element(By.CSS_SELECTOR, hedef)
            else:
                element = driver.find_element(
                    By.XPATH,
                    f"//a[contains(text(), '{hedef}')] | "
                    f"//span[contains(text(), '{hedef}')] | "
                    f"//button[contains(text(), '{hedef}')]"
                )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();",
                element,
            )
            time.sleep(SEKME_TIKLAMA_BEKLEME)
            return True
        except Exception:
            continue
    return False


# ============================================================================
#  ANA VERİ ÇEKME
# ============================================================================

def veri_cek(driver, url):
    """Tek ilan sayfasından TÜM verileri çeker."""
    cekilen_veri = {"URL": url}

    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except Exception:
        pass

    time.sleep(SAYFA_YUKLEME_BEKLEME)

    # Başlık
    try:
        h1 = driver.find_element(By.TAG_NAME, "h1")
        cekilen_veri["Baslik"] = h1.text.strip()
    except Exception:
        cekilen_veri["Baslik"] = "Belirtilmedi"

    # Fiyat
    try:
        fiyat = driver.execute_script("""
            var selectors = ['span.product-price', '.product-price', '[class*="price"]'];
            for (var i = 0; i < selectors.length; i++) {
                var el = document.querySelector(selectors[i]);
                if (el) {
                    var txt = el.innerText.trim();
                    if (txt && /\\d/.test(txt) && txt.length < 50) return txt.split('\\n')[0].trim();
                }
            }
            return 'Belirtilmedi';
        """)
        cekilen_veri["Fiyat"] = fiyat
    except Exception:
        cekilen_veri["Fiyat"] = "Belirtilmedi"

    # Sidebar özellikleri
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-properties-details ul li"))
        )
    except Exception:
        time.sleep(3)

    sidebar = driver.execute_script(JS_OZELLIK_CEK)
    if isinstance(sidebar, dict):
        cekilen_veri.update(sidebar)
    print(f"    📋 Sidebar: {len(sidebar) if isinstance(sidebar, dict) else 0} özellik")

    # Araç Bilgileri sekmesi
    if sekmeye_tikla(driver, ["#head-tab-car-information", "Araç Bilgileri"]):
        arac = driver.execute_script(JS_ARAC_BILGILERI_CEK)
        if isinstance(arac, dict):
            for k, v in arac.items():
                if k not in cekilen_veri:
                    cekilen_veri[k] = v
        print(f"    🚗 Araç Bilgileri: {len(arac) if isinstance(arac, dict) else 0} özellik")

    # Boya/Tramer sekmesi
    if sekmeye_tikla(driver, ["#head-tab-damage-information", "Boya, Değişen ve Tramer"]):
        tramer = driver.execute_script(JS_BOYA_TRAMER_CEK)
        if isinstance(tramer, dict):
            cekilen_veri["Boya_Degisen_Tramer"] = tramer.get("rapor", "Girilmemiş")
            cekilen_veri["Tramer_Tutari"] = tramer.get("tramer_tutari", "Belirtilmedi")
        print(f"    🎨 Tramer: {tramer}")

    # Açıklama sekmesi
    if sekmeye_tikla(driver, ["#head-tab-description", "Açıklama"]):
        aciklama = driver.execute_script(JS_ACIKLAMA_CEK)
        cekilen_veri["Satici_Aciklamasi"] = aciklama if aciklama else "Açıklama girilmemiş"
        print(f"    📝 Açıklama: {str(aciklama)[:80]}...")

    # Donanım sekmesi
    if sekmeye_tikla(driver, ["#head-tab-equipment-information", "Donanım"]):
        donanim = driver.execute_script(JS_DONANIM_CEK)
        cekilen_veri["Donanim"] = donanim if donanim else "Donanım bilgisi girilmemiş"
        print(f"    ⚙️  Donanım: {str(donanim)[:80]}...")

    return cekilen_veri


# ============================================================================
#  ÇALIŞTIRMA
# ============================================================================

if __name__ == "__main__":
    print("\n🔬 TEST BOTU v2 BAŞLATILIYOR...")
    print(f"   URL: {TEST_URL}")
    print(f"   Headless: Hayır\n")

    if not TEST_URL or "arabam.com" not in TEST_URL:
        print("❌ HATA: Geçerli bir arabam.com ilan linki girin!")
        sys.exit(1)

    driver = None
    try:
        driver = tarayici_hazirla()
        print("✅ Chrome başlatıldı. Cloudflare gelirse elle geçin.\n")

        veri = veri_cek(driver, TEST_URL)

        # Terminale yazdır
        print("\n" + "=" * 70)
        print("  📋 ÇEKİLEN VERİ (JSON)")
        print("=" * 70)
        print(json.dumps(veri, indent=2, ensure_ascii=False))
        print("=" * 70)

        alan_sayisi = len([k for k in veri if k not in ("URL",)])
        print(f"\n  📊 Toplam {alan_sayisi} alan çekildi.")

        if alan_sayisi >= 10:
            print("  ✅ Veri kalitesi UYGUN! bot.py'ye geçebilirsin.\n")
        else:
            print("  ⚠️  Veri eksik olabilir. Selektörleri kontrol et.\n")

    except KeyboardInterrupt:
        print("\n⚠️  Durduruldu.")

    except Exception as e:
        print(f"\n❌ Hata: {e}")

    finally:
        if driver:
            input("\n⏸️  Tarayıcıyı kapatmak için Enter'a bas...")
            driver.quit()
            print("✅ Tarayıcı kapatıldı.")
