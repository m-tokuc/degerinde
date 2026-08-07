#!/usr/bin/env python3
"""
Batch 1 — Volkswagen + Ford + Opel
==================================
Kontrollü link toplama + detay scrape + PostgreSQL APPEND.

Mevcut Fiat/Renault verisine DOKUNMAZ.
Tek Chrome, marka başına üst limit — laptop CPU/RAM güvenliği.

Kullanım:
  python3 scripts/batch1_vw_ford_opel.py              # full pipeline
  python3 scripts/batch1_vw_ford_opel.py --links-only
  python3 scripts/batch1_vw_ford_opel.py --scrape-only
  python3 scripts/batch1_vw_ford_opel.py --import-only
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Set

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

# ── Batch config (CPU-safe) ──
MARKALAR = ["volkswagen", "ford", "opel"]
MAX_LINKS_PER_BRAND = 250
BAS_YIL = 2012
BIT_YIL = 2024
MAX_SAYFA = 15
MIN_BEKLEME = 2.5
MAX_BEKLEME = 4.5
MARKA_BEKLEME = (5, 8)
ILAN_BEKLEME = (2.5, 4.5)

LINK_FILE = "linkler_batch1.txt"
BATCH_JSONL = "batch1_vw_ford_opel.jsonl"
MAIN_JSONL = "dev_veriseti.jsonl"
PROGRESS_LOG = "batch1_progress.log"
DB_URL = os.getenv(
    "DB_URL",
    "postgresql+psycopg2://postgres:sifre123@localhost:5432/postgres",
)


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(PROGRESS_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def brand_from_url(url: str) -> Optional[str]:
    u = url.lower()
    for b in MARKALAR:
        if f"-{b}-" in u or f"/{b}-" in u or f"satilik-{b}-" in u:
            return b
    # slug variants
    if "volkswagen" in u or "-vw-" in u:
        return "volkswagen"
    return None


# ─────────────────────────────────────────────────────────────
# 1) LINK COLLECTION
# ─────────────────────────────────────────────────────────────
def collect_links() -> List[str]:
    from selenium.webdriver.common.by import By

    # Reuse link_toplayici browser setup
    from link_toplayici import tarayici_hazirla, cloudflare_kontrolu

    existing: Set[str] = set()
    if os.path.exists(LINK_FILE):
        with open(LINK_FILE, "r", encoding="utf-8") as f:
            existing = {ln.strip() for ln in f if ln.strip()}
        log(f"Mevcut batch linkleri: {len(existing)}")

    # Also skip URLs already in main jsonl
    scraped: Set[str] = set()
    if os.path.exists(MAIN_JSONL):
        with open(MAIN_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    u = json.loads(line).get("URL")
                    if u:
                        scraped.add(u)
                except Exception:
                    pass
    log(f"Ana JSONL'de işlenmiş URL: {len(scraped)}")

    per_brand: Dict[str, int] = {b: 0 for b in MARKALAR}
    for u in existing:
        b = brand_from_url(u)
        if b:
            per_brand[b] += 1

    driver = tarayici_hazirla()
    yeni_toplam = 0
    try:
        for marka in MARKALAR:
            if per_brand[marka] >= MAX_LINKS_PER_BRAND:
                log(f"{marka}: zaten {per_brand[marka]} link — atlanıyor")
                continue
            log(f"=== LINK TOPLAMA: {marka.upper()} "
                f"({per_brand[marka]}/{MAX_LINKS_PER_BRAND}) ===")

            for yil in range(BAS_YIL, BIT_YIL + 1):
                if per_brand[marka] >= MAX_LINKS_PER_BRAND:
                    break
                for sayfa in range(1, MAX_SAYFA + 1):
                    if per_brand[marka] >= MAX_LINKS_PER_BRAND:
                        break
                    url = (
                        f"https://www.arabam.com/ikinci-el/otomobil/{marka}"
                        f"?minYear={yil}&maxYear={yil}&page={sayfa}"
                    )
                    try:
                        driver.get(url)
                        time.sleep(random.uniform(MIN_BEKLEME, MAX_BEKLEME))
                        if not cloudflare_kontrolu(driver):
                            log(f"Cloudflare: {marka}/{yil} atlandı")
                            break
                        try:
                            els = driver.find_elements(By.CSS_SELECTOR, "a.link-overlay")
                        except Exception:
                            els = []
                        if not els:
                            break
                        batch_new = []
                        for el in els:
                            try:
                                href = el.get_attribute("href")
                            except Exception:
                                continue
                            if not href or "/ilan/" not in href:
                                continue
                            if href in existing or href in scraped:
                                continue
                            existing.add(href)
                            batch_new.append(href)
                            per_brand[marka] += 1
                            if per_brand[marka] >= MAX_LINKS_PER_BRAND:
                                break
                        if batch_new:
                            with open(LINK_FILE, "a", encoding="utf-8") as f:
                                for h in batch_new:
                                    f.write(h + "\n")
                            yeni_toplam += len(batch_new)
                        log(
                            f"  [{marka}] {yil} p{sayfa}: +{len(batch_new)} "
                            f"| brand={per_brand[marka]}"
                        )
                        if len(els) < 20:
                            break
                    except Exception as e:
                        log(f"  Hata {marka}/{yil}/p{sayfa}: {e}")
                        continue
            time.sleep(random.uniform(*MARKA_BEKLEME))
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    links = []
    if os.path.exists(LINK_FILE):
        with open(LINK_FILE, "r", encoding="utf-8") as f:
            links = [ln.strip() for ln in f if ln.strip().startswith("http")]
    log(f"Link toplama bitti. Yeni={yeni_toplam}, dosya toplam={len(links)}")
    for b, n in per_brand.items():
        log(f"  {b}: {n}")
    return links


# ─────────────────────────────────────────────────────────────
# 2) DETAIL SCRAPE
# ─────────────────────────────────────────────────────────────
def scrape_details(links: Optional[List[str]] = None) -> int:
    import bot as botmod

    if links is None:
        if not os.path.exists(LINK_FILE):
            log("Link dosyası yok — önce --links-only çalıştırın")
            return 0
        with open(LINK_FILE, "r", encoding="utf-8") as f:
            links = [ln.strip() for ln in f if ln.strip().startswith("http")]

    done: Set[str] = set()
    for path in (BATCH_JSONL, MAIN_JSONL):
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    o = json.loads(line)
                    u = o.get("URL")
                    if u and "Hata" not in o and len(o) >= 6:
                        done.add(u)
                except Exception:
                    pass

    todo = [u for u in links if u not in done]
    # Prefer brand-balanced order
    by_brand: Dict[str, List[str]] = {b: [] for b in MARKALAR}
    other: List[str] = []
    for u in todo:
        b = brand_from_url(u)
        if b:
            by_brand[b].append(u)
        else:
            other.append(u)
    ordered: List[str] = []
    caps = {b: 0 for b in MARKALAR}
    # Interleave brands up to MAX_LINKS_PER_BRAND each (remaining to scrape)
    while True:
        progressed = False
        for b in MARKALAR:
            if caps[b] >= MAX_LINKS_PER_BRAND or not by_brand[b]:
                continue
            ordered.append(by_brand[b].pop(0))
            caps[b] += 1
            progressed = True
        if not progressed:
            break
    ordered.extend(other)

    log(f"Scrape kuyruğu: {len(ordered)} (atlanacak done={len(done)})")
    if not ordered:
        log("Scrape edilecek yeni ilan yok.")
        return 0

    driver = botmod.tarayici_hazirla()
    botmod.aktif_driverlar.append(driver)
    ok = 0
    fail = 0
    try:
        for i, url in enumerate(ordered, 1):
            try:
                veri = botmod.tek_ilan_retry_ile(driver, url)
                alan = len([k for k in veri if k not in ("URL", "Hata")])
                if "Hata" in veri or alan < 5:
                    fail += 1
                    log(f"  [{i}/{len(ordered)}] FAIL alan={alan} {url[:70]}")
                else:
                    line = json.dumps(veri, ensure_ascii=False)
                    with open(BATCH_JSONL, "a", encoding="utf-8") as f:
                        f.write(line + "\n")
                    with open(MAIN_JSONL, "a", encoding="utf-8") as f:
                        f.write(line + "\n")
                    ok += 1
                    if ok % 10 == 0 or i == 1:
                        log(f"  [{i}/{len(ordered)}] OK={ok} FAIL={fail} "
                            f"baslik={str(veri.get('Baslik', ''))[:50]}")
                # Periodic Chrome recycle
                if i % 80 == 0:
                    log("  Chrome yeniden başlatılıyor (RAM)...")
                    driver = botmod.chrome_yeniden_baslat(driver, 0)
                time.sleep(random.uniform(*ILAN_BEKLEME))
            except Exception as e:
                fail += 1
                log(f"  [{i}] exception: {e}")
                try:
                    driver = botmod.chrome_yeniden_baslat(driver, 0)
                except Exception:
                    pass
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        botmod.tum_driverlari_kapat()

    log(f"Scrape bitti. OK={ok} FAIL={fail}")
    return ok


# ─────────────────────────────────────────────────────────────
# 3) DB APPEND (no delete)
# ─────────────────────────────────────────────────────────────
def clean_price(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = re.sub(r"[^\d]", "", str(val))
    return float(s) if s else None


def clean_km(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = re.sub(r"[^\d]", "", str(val))
    return float(s) if s else None


def append_to_db(source_jsonl: str = BATCH_JSONL) -> int:
    """Append scrape JSONL into araclar_clean only (whitelist + URL dedupe)."""
    from schema_clean import append_clean_rows, ensure_clean_table, get_engine

    if not os.path.exists(source_jsonl):
        log(f"JSONL yok: {source_jsonl}")
        return 0

    rows = []
    with open(source_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if "Hata" in o:
                continue
            rows.append(o)
    if not rows:
        log("Append edilecek kayıt yok")
        return 0

    engine = get_engine(DB_URL)
    ensure_clean_table(engine)
    stats = append_clean_rows(rows, engine=engine, source=f"batch1:{os.path.basename(source_jsonl)}")
    log(
        f"APPEND araclar_clean: inserted={stats['inserted']} "
        f"dup_skip={stats['skipped_dup']} no_url={stats['skipped_no_url']} "
        f"received={stats['received']}"
    )
    return int(stats["inserted"])


def summarize_db() -> None:
    from sqlalchemy import create_engine, text
    import pandas as pd
    import unicodedata

    engine = create_engine(DB_URL)
    df = pd.read_sql('SELECT "Baslik" FROM araclar WHERE "Baslik" IS NOT NULL', engine)

    def norm(s):
        s = str(s).replace("\u0131", "i").replace("\u0130", "i")
        nfkd = unicodedata.normalize("NFKD", s)
        return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()

    brands = ["volkswagen", "ford", "opel", "fiat", "renault", "vw"]
    counts = {b: 0 for b in brands}
    prefix = re.compile(r"^(Sahibinden|Galeriden|İkinci\s*El|Ikinci\s*El)\s+", re.I)
    for b in df["Baslik"].astype(str):
        s = prefix.sub("", b).strip()
        sn = norm(s)
        for brand in brands:
            if sn.startswith(brand):
                counts[brand] += 1
                break
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM araclar")).scalar()
    log("=== DB ÖZET ===")
    log(f"Toplam satır: {total}")
    for b, n in counts.items():
        if n:
            log(f"  {b}: {n}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--links-only", action="store_true")
    ap.add_argument("--scrape-only", action="store_true")
    ap.add_argument("--import-only", action="store_true")
    ap.add_argument("--skip-links", action="store_true")
    args = ap.parse_args()

    log("=" * 60)
    log("BATCH 1 START — VW / Ford / Opel")
    log(f"MAX_LINKS_PER_BRAND={MAX_LINKS_PER_BRAND}")
    log("=" * 60)

    if args.import_only:
        append_to_db()
        summarize_db()
        return

    if args.links_only:
        collect_links()
        return

    if args.scrape_only:
        scrape_details()
        append_to_db()
        summarize_db()
        return

    # Full pipeline
    if not args.skip_links:
        collect_links()
    scrape_details()
    append_to_db()
    summarize_db()
    log("BATCH 1 pipeline tamam. Şimdi train_model.py çalıştırın.")


if __name__ == "__main__":
    main()
