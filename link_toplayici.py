import asyncio
from curl_cffi.requests import AsyncSession
import aiofiles
from bs4 import BeautifulSoup
import time
import random
import os
import json
import logging
import signal
import sys

# ================= CONSTANTS & CONFIG =================

BASE_URL = "https://www.arabam.com"
LINKS_FILE = "cleaned_links.txt" # Direct append to cleaned dataset
STATE_FILE = "scraper_state.json"
ERROR_LOG_FILE = "scraper_errors.log"

# Güvenlik Duvarı (Cloudflare) 403 Hatası Alırsanız Bu Sayıyı Düşürün (Örn: 3 veya 5)
# Sorunsuz çalışıyorsa daha hızlı tarama için 10-15 yapabilirsiniz.
CONCURRENCY_LIMIT = 3

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/114.0.1823.43',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/112.0'
]

# Load known links to avoid scraping cars we already have in the database
KNOWN_LINKS = set()
if os.path.exists('known_links.txt'):
    with open('known_links.txt', 'r', encoding='utf-8') as f:
        for line in f:
            KNOWN_LINKS.add(line.strip())
print(f"Loaded {len(KNOWN_LINKS)} known links to skip.")

CATEGORIES = ['otomobil', 'arazi-suv-pick-up', 'minivan-panelvan']
SORT_PARAMS = ['price-asc', 'price-desc']
YEARS = list(range(1990, 2026))

# Massive exhaustive fallback dictionary requested
BRANDS_MODELS = {
    'fiat': ['egea', 'linea', 'fiorino', 'doblo', 'punto', 'albea', 'palio', 'siena', 'brava', 'bravo', 'tempra', 'tipo', 'uno', '500', '500l', '500x', 'panda', 'stilo', 'marea'],
    'renault': ['clio', 'megane', 'symbol', 'fluence', 'kadjar', 'captur', 'kangoo', 'koleos', 'talisman', 'laguna', 'latitude', 'scenic', 'grand-scenic', 'twingo', 'r-9', 'r-11', 'r-12', 'r-19', 'r-21', 'safrane', 'modus', 'zoe', 'austral'],
    'volkswagen': ['passat', 'golf', 'polo', 'jetta', 'tiguan', 'caddy', 'transporter', 'amarok', 'touareg', 'touran', 'scirocco', 'cc', 'arteon', 't-roc', 't-cross', 'taigo', 'bora', 'vento', 'beetle', 'up', 'fox', 'sharan', 'caravelle', 'multivan'],
    'ford': ['focus', 'fiesta', 'courier', 'transit', 'mondeo', 'kuga', 'puma', 'ecosport', 'c-max', 'b-max', 's-max', 'galaxy', 'mustang', 'ranger', 'connect', 'custom', 'fusion', 'escort', 'taunus', 'ka', 'explorer', 'edge', 'tourneo-courier', 'tourneo-connect'],
    'toyota': ['corolla', 'yaris', 'auris', 'c-hr', 'rav4', 'hilux', 'avensis', 'camry', 'land-cruiser', 'proace', 'verso', 'prius', 'gt86', 'supra', 'urban-cruiser', 'corona', 'carina'],
    'hyundai': ['i20', 'accent', 'tucson', 'i30', 'elantra', 'i10', 'kona', 'bayon', 'getz', 'santa-fe', 'starex', 'h-100', 'ix35', 'matrix', 'era', 'blue', 'sonata', 'atos', 'staria', 'ioniq'],
    'peugeot': ['3008', '208', '2008', '308', '508', '5008', 'rifter', 'partner', 'bipper', 'expert', 'boxer', '206', '207', '307', '407', '106', '301', '406', 'rcz'],
    'dacia': ['duster', 'sandero', 'stepway', 'logan', 'lodgy', 'dokker', 'jogger', 'spring'],
    'honda': ['civic', 'cr-v', 'hr-v', 'jazz', 'city', 'accord', 'cr-z', 's2000'],
    'citroen': ['c3', 'c4', 'c5', 'c3-aircross', 'c5-aircross', 'c-elysee', 'berlingo', 'c4-cactus', 'c4-picasso', 'grand-c4-picasso', 'ds3', 'ds4', 'ds5', 'saxo', 'xsara', 'nemo', 'jumpy', 'jumper', 'c1', 'c2', 'ami'],
    'opel': ['astra', 'corsa', 'insignia', 'mokka', 'crossland', 'grandland', 'vectra', 'combo', 'zafira', 'meriva', 'tigra', 'omega', 'agila', 'vivaro', 'movano', 'adam', 'ampera', 'kadett', 'calibra'],
    'skoda': ['octavia', 'superb', 'fabia', 'karoq', 'kodiaq', 'scala', 'kamiq', 'yeti', 'rapid', 'roomster', 'felicia', 'favorit', 'enyaq'],
    'nissan': ['qashqai', 'micra', 'x-trail', 'juke', 'navara', 'almera', 'note', 'pulsar', 'primera', 'sunny', 'terrano', 'pathfinder', 'patrol', '350z', 'gt-r', 'leaf', 'ariya'],
    'audi': ['a3', 'a4', 'a6', 'a5', 'q3', 'q5', 'q7', 'a1', 'a7', 'a8', 'q2', 'q8', 'tt', 'r8', 'rs', 's-series', 'e-tron'],
    'mercedes-benz': ['c-serisi', 'e-serisi', 'a-serisi', 'b-serisi', 'cla', 'gla', 'glc', 'gle', 's-serisi', 'vito', 'sprinter', 'ml', 'gl', 'glk', 'g-serisi', 'sl', 'slk', 'cl', 'clk', 'cls', 'eqc', 'eqe', 'eqs'],
    'bmw': ['3-serisi', '5-serisi', '1-serisi', 'x1', 'x3', 'x5', '4-serisi', '2-serisi', '7-serisi', 'x4', 'x6', '6-serisi', '8-serisi', 'z4', 'i3', 'i8', 'ix', 'i4'],
    'kia': ['sportage', 'rio', 'ceed', 'picanto', 'stonic', 'sorento', 'bongo', 'cerato', 'niro', 'optima', 'soul', 'venga', 'ev6', 'xceed'],
    'seat': ['leon', 'ibiza', 'ateca', 'arona', 'tarraco', 'toledo', 'cordoba', 'altea', 'alhambra'],
    'chevrolet': ['cruze', 'aveo', 'captiva', 'kalos', 'spark', 'lacetti', 'epica', 'rezzo', 'trax', 'camaro', 'corvette', 'tahoe'],
    'chery': ['tiggo', 'tiggo-7-pro', 'tiggo-8-pro', 'omoda-5', 'alia', 'niche', 'kimo', 'chance'],
    'volvo': ['s60', 'xc60', 'xc90', 'v40', 's90', 's40', 's80', 'v60', 'c30', 'xc40', 'v90'],
    'suzuki': ['swift', 'vitara', 'jimny', 'sx4', 'grand-vitara', 'alto', 'baleno', 'splash', 's-cross'],
    'mitsubishi': ['l200', 'asx', 'lancer', 'outlander', 'colt', 'carisma', 'pajero', 'space-star', 'eclipse-cross'],
    'alfa-romeo': ['giulietta', '159', '147', '156', 'mito', 'stelvio', 'giulia', 'tonale', 'gt', 'brera'],
    'mazda': ['mazda3', 'mazda6', 'cx-5', 'mazda2', 'cx-3', 'rx-8', 'mx-5', '323', '626', 'lantis'],
    'land-rover': ['range-rover', 'range-rover-sport', 'range-rover-evoque', 'discovery', 'freelander', 'defender', 'range-rover-velar'],
    'jeep': ['renegade', 'compass', 'grand-cherokee', 'cherokee', 'wrangler', 'commander', 'patriot'],
    'porsche': ['cayenne', 'macan', 'panamera', '911', 'taycan', 'boxster', 'cayman'],
    'mini': ['cooper', 'countryman', 'clubman', 'one', 'paceman', 'cabrio'],
    'subaru': ['xv', 'forester', 'impreza', 'outback', 'legacy', 'brz', 'levorg'],
    'tofas': ['sahin', 'dogan', 'kartal', 'serce', 'murat'],
    'lada': ['vega', 'niva', 'samara', 'kalina'],
    'ds-automobiles': ['ds-7-crossback', 'ds-4', 'ds-3-crossback', 'ds-9'],
    'lexus': ['rx', 'nx', 'is', 'es', 'ls', 'ux', 'gs', 'ct'],
    'togg': ['t10x'],
    'tesla': ['model-y', 'model-3'],
    'mg': ['zs', 'hs', 'mg4', 'rx8'],
    'byd': ['atto-3', 'seal-u'],
    'ssangyong': ['tivoli', 'korando', 'rexton', 'actyon-sports'],
    'tata': ['indica', 'indigo', 'telcoline', 'vista'],
    'geely': ['emgrand', 'echo', 'familia'],
    'proton': ['gen-2', 'waja', 'persona'],
    'jaguar': ['xe', 'xf', 'f-pace', 'x-type'],
    'maserati': ['ghibli', 'levante', 'quattroporte'],
    'cupra': ['formentor', 'leon', 'ateca'],
    'leapmotor': ['t03'],
    'skywell': ['et5'],
    'seres': ['3'],
    'isuzu': ['d-max'],
    'smart': ['fortwo', 'forfour'],
    'daihatsu': ['terios', 'sirion']
}

# ================= LOGGING & GLOBALS =================

# Setup elegant live logging and error file logging
logger = logging.getLogger('ArabamScraper')
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%H:%M:%S')

# Console handler for Live Monitoring
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler for Error Log
file_handler = logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Global shutdown event for Graceful Shutdown
shutdown_event = asyncio.Event()

# ================= CORE ASYNC FUNCTIONS =================

def load_state():
    """Load the progress state (brand, model)."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Could not load state: {e}")
    return {}

def save_state(brand, model):
    """Save the progress state to know which model we just finished."""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'brand': brand, 'model': model}, f)

async def write_links_to_file(links, lock):
    """O(1) memory append to file with asyncio lock to prevent race conditions."""
    async with lock:
        async with aiofiles.open(LINKS_FILE, 'a', encoding='utf-8') as f:
            for link in links:
                await f.write(f"{link}\n")

async def fetch_with_retry(session, url, semaphore):
    """Fetches a URL with retries, graceful backoff, and 403 handling."""
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    async with semaphore:
        for attempt in range(1, 4):
            if shutdown_event.is_set():
                break
                
            try:
                # Add a human-like delay
                await asyncio.sleep(random.uniform(1.0, 2.5))
                
                response = await session.get(url, headers=headers, timeout=15)
                if response.status_code in [403, 429, 500, 502, 503, 504]:
                    logger.warning(f"Got {response.status_code} on {url}. Retrying ({attempt}/3)...")
                    await asyncio.sleep(2 ** attempt) # Exponential backoff
                    continue
                
                response.raise_for_status()
                html = response.text
                return html
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt}/3 failed for {url} | Error: {e}")
                if attempt == 3:
                    logger.error(f"Failed to fetch {url} after 3 attempts. Error: {e}")
                await asyncio.sleep(2 ** attempt)
                
    return None

def extract_links(html):
    """Extract unique, valid car listing URLs from HTML string."""
    soup = BeautifulSoup(html, 'html.parser')
    unique_links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href'].strip()
        if not href:
            continue
        if href.startswith('/'):
            full_url = BASE_URL + href
        elif href.startswith('http'):
            full_url = href
        else:
            continue
        
        # Clean query parameters / fragment anchors
        clean_url = full_url.split('?')[0].split('#')[0].rstrip('/')
        
        # Strict listing URL filter: must contain /ilan/ and end with numeric listing ID (digits)
        if '/ilan/' in clean_url and clean_url.split('/')[-1].isdigit():
            if clean_url not in KNOWN_LINKS:
                unique_links.add(clean_url)
            
    return list(unique_links)

async def find_correct_category(session, brand, model, semaphore):
    """Asynchronously determine the correct category (fallback mechanism)."""
    logger.info(f"Kategori aranıyor: {brand.capitalize()} {model.capitalize()}...")
    for cat in CATEGORIES:
        if shutdown_event.is_set(): return None
        test_url = f"{BASE_URL}/ikinci-el/{cat}/{brand}-{model}"
        html = await fetch_with_retry(session, test_url, semaphore)
        if html:
            links = extract_links(html)
            if links:
                logger.info(f"-> Kategori bulundu: {cat} ({len(links)} örnek link)")
                return cat
    logger.info(f"-> Hata: {brand} {model} için uygun kategori bulunamadı, atlanıyor.")
    return None

async def scrape_pages_task(session, base_url, max_pages, brand, model, semaphore, file_lock, seen_urls, seen_lock):
    """Scrapes up to max_pages from a given base URL. Returns the number of pages successfully scraped."""
    pages_scraped = 0
    for page in range(1, max_pages + 1):
        if shutdown_event.is_set():
            break
            
        url = f"{base_url}&page={page}" if "?" in base_url else f"{base_url}?page={page}"
        html = await fetch_with_retry(session, url, semaphore)
        
        if not html:
            break
            
        page_links = extract_links(html)
        if not page_links:
            break
            
        async with seen_lock:
            new_links = [l for l in page_links if l not in seen_urls]
            for l in new_links:
                seen_urls.add(l)
                
        if not new_links:
            break
            
        await write_links_to_file(new_links, file_lock)
        logger.info(f"[{brand.upper()} {model.upper()}] Sayfa {page} taranıyor... Eklenen Yeni Link: {len(new_links)}")
        pages_scraped += 1
        
    return pages_scraped

async def process_model(session, brand, model, semaphore, file_lock, seen_urls, seen_lock):
    """Processes an entire model. Only falls back to year-splitting if it hits the 50-page limit."""
    category = await find_correct_category(session, brand, model, semaphore)
    if not category:
        return
        
    base_model_url = f"{BASE_URL}/ikinci-el/{category}/{brand}-{model}"
    
    # First, try to scrape without year filtering.
    # If it hits 50 pages, it means we missed some cars (max 1000 cars limit).
    pages_scraped = await scrape_pages_task(session, base_model_url, 50, brand, model, semaphore, file_lock, seen_urls, seen_lock)
    
    if pages_scraped == 50:
        logger.warning(f"🚨 {brand} {model} 50 sayfa sınırına takıldı (>1000 araç)! Yıllara bölünerek detaylı taranıyor...")
        tasks = []
        for year in YEARS:
            for sort_param in SORT_PARAMS:
                url = f"{base_model_url}?minYear={year}&maxYear={year}&sort={sort_param}"
                task = asyncio.create_task(
                    scrape_pages_task(session, url, 50, brand, model, semaphore, file_lock, seen_urls, seen_lock)
                )
                tasks.append(task)
        await asyncio.gather(*tasks)

# ================= SHUTDOWN HANDLER =================

def handle_shutdown(sig, frame):
    """Graceful shutdown trigger on Ctrl+C."""
    logger.warning("🚨 Kapanış sinyali alındı (Ctrl+C). Mevcut görevler güvenli bir şekilde kapatılıyor... Lütfen bekleyin!")
    shutdown_event.set()

# ================= MAIN ENGINE =================

async def async_main():
    # Setup Signal Handler for graceful shutdown
    if sys.platform != 'win32':
        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(signal.SIGINT, lambda: shutdown_event.set())
            loop.add_signal_handler(signal.SIGTERM, lambda: shutdown_event.set())
        except NotImplementedError:
            pass # fallback for weird environments
    else:
        signal.signal(signal.SIGINT, handle_shutdown)
    
    state = load_state()
    start_brand = state.get('brand')
    start_model = state.get('model')
    
    resume_mode = bool(start_brand and start_model)
    if resume_mode:
        logger.info(f"🔄 Kaldığı Yerden Devam Ediyor: Son bitirilen -> {start_brand} {start_model}")

    # Load existing links to prevent duplicate scraping across runs
    seen_urls = set()
    source_file = "cleaned_links.txt" if os.path.exists("cleaned_links.txt") else LINKS_FILE
    if os.path.exists(source_file):
        logger.info(f"Hafızaya yükleniyor: '{source_file}'...")
        with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                u = line.strip()
                if u:
                    seen_urls.add(u)
        logger.info(f"Mevcut {len(seen_urls):,} tekil link hafızaya yüklendi.")

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT) # Jet Engine limit
    file_lock = asyncio.Lock()
    seen_lock = asyncio.Lock()
    
    async with AsyncSession(impersonate="chrome110") as session:
        for brand, models in BRANDS_MODELS.items():
            if shutdown_event.is_set(): break
            
            for model in models:
                if shutdown_event.is_set(): break
                
                # Resume Logic: Skip until we pass the last saved model
                if resume_mode:
                    if brand == start_brand and model == start_model:
                        resume_mode = False # Found the starting point, start processing the NEXT model
                    continue
                
                # Process the model concurrently via internal Year/Sort tasks
                await process_model(session, brand, model, semaphore, file_lock, seen_urls, seen_lock)
                
                if shutdown_event.is_set():
                    logger.warning(f"🛑 Kapanış nedeniyle {brand} {model} state kaydedilmedi (yarım kaldı).")
                    break
                
                # State Checkpoint after fully completing a model
                save_state(brand, model)
                logger.info(f"✅ Tamamlandı ve State Kaydedildi: {brand.upper()} {model.upper()}")

    logger.info("🚀 Scraper Motoru durdu. Tüm veriler güvenli.")

def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.warning("Program zorla kapatıldı.")

if __name__ == '__main__':
    main()