import asyncio
import aiofiles
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
import json
import logging
import random
import os
import sys
import gc
import re

# --- CONFIGURATION ---
INPUT_FILE = "cleaned_links.txt"
OUTPUT_FILE = "araba_verileri.jsonl"
CHECKPOINT_FILE = "islenen_linkler.txt"
CONCURRENCY_LIMIT = 5  # Anti-Ban / Rate-Limit Safe Limit
MAX_RETRIES = 5

# --- LOGGING SETUP ---
logger = logging.getLogger('DetayCekici')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%H:%M:%S')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def load_processed_links():
    """Load already processed links to avoid duplicate work and enable resuming."""
    processed = set()
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url:
                    processed.add(url)
    logger.info(f"🔄 Checkpoint yüklendi: {len(processed):,} link zaten işlenmiş.")
    return processed

def parse_html(html, url):
    """
    Parse the HTML using lxml and extract all car specs.
    Returns a dict of properties.
    """
    soup = BeautifulSoup(html, 'lxml')
    details = {"url": url}
    
    try:
        title_el = soup.find('h1')
        if title_el:
            details["Baslik"] = title_el.get_text(strip=True)
            
        price_el = soup.find(class_=lambda c: c and isinstance(c, str) and 'price' in c.lower() and 'old' not in c.lower())
        if price_el:
            details["Fiyat_Ham"] = price_el.get_text(separator=' ', strip=True).replace('Fiyat', '').strip()

        BLACKLIST = {"Trink sat!", "Araç Sat", "Hizmetlerimiz", "arabam Blog", "Kurumsal", "Garaj", "Ekspertiz", "Anasayfa"}

        for li in soup.find_all('li'):
            text = li.get_text(separator='|', strip=True)
            if '|' in text:
                parts = text.split('|', 1)
                key = parts[0].strip().replace(':', '')
                val = parts[1].strip()
                
                if key in BLACKLIST:
                    continue
                    
                # 1. Filter Breadcrumb Noise
                if re.search(r'\d+\|\w+', val) or '|' in val:
                    continue
                    
                if len(key) < 40 and len(val) < 200:
                    if key == "İlan No" and "Kopyalandı" in val:
                        val = val.replace("Kopyalandı", "").replace("|", "").strip()
                    
                    if key not in details:
                        details[key] = val

        # 3. Donanımlar (Equipment)
        donanim_list = []
        for eq in soup.select('ul.hardware-list li, ul.equipment-list li, .equipment-item, .hardware-item'):
            t = eq.get_text(strip=True)
            if t: donanim_list.append(t)
            
        if donanim_list:
            details["Donanimlar"] = ", ".join(list(set(donanim_list)))
        else:
            details["Donanimlar"] = "Belirtilmemiş"

        # 4. Açıklama (Description)
        desc_el = soup.select_one('#js-hook-description, .description, .detail-text, .ilan-aciklamasi')
        if desc_el:
            details["Aciklama"] = desc_el.get_text(separator=' ', strip=True).replace('\n', ' ')
        else:
            details["Aciklama"] = "Belirtilmemiş"

        # --- CRITICAL FIXES FOR AI TRAINING ---
        # Look directly in the raw html for dataLayer/script variables for 100% clean data
        dl_vars = {}
        for match in re.finditer(r'[\"\']CD_([^\"\']+)[\"\']\s*:\s*[\"\']([^\"\']+)[\"\']', html):
            key, val = match.groups()
            dl_vars[key.lower()] = val.replace('\\u002F', '/').strip()

        details["Boya_Degisen"] = dl_vars.get('boya-degisen', 'Belirtilmemiş')
        details["Ilan_Tarihi"] = dl_vars.get('ilan_tarihi', 'Belirtilmemiş')
        details["Ilan_No"] = dl_vars.get('ilan_no', 'Belirtilmemiş')

        if 'marka' in dl_vars: details["Marka"] = dl_vars['marka']
        if 'seri' in dl_vars: details["Seri"] = dl_vars['seri']
        if 'model' in dl_vars: details["Model"] = dl_vars['model']
        if 'yil' in dl_vars: details["Yil"] = dl_vars['yil']
        if 'agir_hasarli' in dl_vars: details["Agir_Hasarli"] = dl_vars['agir_hasarli']
        if 'kimden' in dl_vars: details["Kimden"] = dl_vars['kimden']
        if 'kasa_tipi' in dl_vars: details["Kasa_Tipi"] = dl_vars['kasa_tipi']
        if 'yakit_tipi' in dl_vars: details["Yakit_Tipi"] = dl_vars['yakit_tipi']
        if 'vites_tipi' in dl_vars: details["Vites_Tipi"] = dl_vars['vites_tipi']
        
        loc = "Belirtilmemiş"
        if 'il' in dl_vars and 'ilce' in dl_vars:
            loc = f"{dl_vars['il']} / {dl_vars['ilce']}"
        elif 'il' in dl_vars:
            loc = dl_vars['il']
        details["Konum"] = loc
        
        # Extract Tramer
        page_text = soup.get_text(separator=' ', strip=True)
        tramer_text = "Belirtilmemiş"
        match = re.search(r'(?:Tramer|Hasar Kayd[ıi]).{0,30}?(\d{1,3}(?:\.\d{3})+|\d+)\s*TL', page_text, re.I)
        if match:
            tramer_text = match.group(1) + " TL"
        details["Tramer"] = tramer_text
            
    except Exception as e:
        logger.error(f"⚠️ Parsing hatası ({url}): {e}")
    finally:
        soup.decompose()
        
    return details

async def fetch_and_process(url, session, semaphore, output_lock, processed_lock, processed_set):
    """Fetch URL, parse it, and stream to JSONL instantly."""
    async with semaphore:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Anti-Ban Pacing
                await asyncio.sleep(random.uniform(0.5, 1.2))
                
                response = await session.get(url, timeout=15)
                
                if response.status_code == 429:
                    logger.warning(f"⚠️ Rate Limit (HTTP 429) algılandı. {attempt * 10} sn bekleniyor... ({url})")
                    await asyncio.sleep(10 * attempt)
                    continue
                elif response.status_code in [403, 500, 502, 503, 504]:
                    logger.warning(f"HTTP {response.status_code} on {url} (Deneme {attempt}/{MAX_RETRIES})")
                    await asyncio.sleep(3 * attempt)
                    continue
                    
                response.raise_for_status()
                
                # Parse
                car_data = parse_html(response.text, url)
                
                # Check for category breadcrumb noise
                if ("Yıl" in car_data or "Kilometre" in car_data) and "Fiyat_Ham" in car_data:
                    
                    async with output_lock:
                        async with aiofiles.open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                            await f.write(json.dumps(car_data, ensure_ascii=False) + '\n')
                            
                    async with processed_lock:
                        async with aiofiles.open(CHECKPOINT_FILE, 'a', encoding='utf-8') as f:
                            await f.write(url + '\n')
                        processed_set.add(url)
                        
                    logger.info(f"✅ Çekildi: {car_data.get('Baslik', '')[:30]}...")
                else:
                    logger.warning(f"⚠️ Geçersiz/Boş/Kategori sayfası atlandı: {url}")
                
                return
                
            except Exception as e:
                logger.debug(f"Hata ({url}) Deneme {attempt}/{MAX_RETRIES}: {e}")
                await asyncio.sleep(2 ** attempt)
                
        logger.error(f"❌ Başarısız: {url} ({MAX_RETRIES} deneme sonu)")

async def main():
    if not os.path.exists(INPUT_FILE):
        logger.error(f"'{INPUT_FILE}' bulunamadı! Önce linkleri toplamalısınız.")
        return

    processed_set = load_processed_links()
    
    logger.info(f"'{INPUT_FILE}' dosyasından linkler okunuyor (O(1) Stream)...")
    
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    output_lock = asyncio.Lock()
    processed_lock = asyncio.Lock()
    
    tasks = []
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
        
    total_urls = len(urls)
    urls_to_process = [u for u in urls if u not in processed_set]
    
    logger.info(f"Toplam Link: {total_urls:,} | İşlenecek Link: {len(urls_to_process):,}")
    
    if not urls_to_process:
        logger.info("Tüm linkler zaten işlenmiş. Motor durduruluyor.")
        return

    logger.info("👻 Hayalet Motor (Ghost Engine) Ultimate Ver. Başlatılıyor...")
    
    async with AsyncSession(impersonate="chrome110") as session:
        for url in urls_to_process:
            tasks.append(
                asyncio.create_task(
                    fetch_and_process(url, session, semaphore, output_lock, processed_lock, processed_set)
                )
            )
            
            if len(tasks) >= 5000:
                await asyncio.gather(*tasks)
                tasks = [] 
                gc.collect() 
                
        if tasks:
            await asyncio.gather(*tasks)

    logger.info("🎉 İşlem Tamamlandı! Tüm veriler araba_verileri.jsonl içine kaydedildi.")

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Program durduruldu.")
