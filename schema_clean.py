"""
Değerinde — clean schema, hasar/tramer parsers, safe append import.

Canonical ML/API table: ``araclar_clean`` (whitelist columns only).
Legacy dirty ``araclar`` (247 cols) is read-only for backfill; never grow it.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ─── Whitelist (canonical column names in araclar_clean) ───
CLEAN_COLUMNS: list[str] = [
    "ilan_url",
    "Baslik",
    "Fiyat",
    "Marka",
    "Seri",
    "Model",
    "Yil",
    "Kilometre",
    "Yakit_Tipi",
    "Vites_Tipi",
    "Kasa_Tipi",
    "Cekis",
    "Renk",
    "Kimden",
    "Garanti_Durumu",
    "Silindir_Sayisi",
    "Koltuk_Sayisi",
    "Motor_Hacmi",
    "Motor_Gucu",
    "Il",
    "Ilce",
    "Tramer_Tutari_Raw",
    "Tramer_TL",
    "Boya_Raw",
    "Boyanan_Parcalar",
    "Lokal_Boya",
    "Boya_Durumu",
    "Has_Boya",
    "Has_Degisen",
    "Has_Tramer",
    "scraped_at",
    "source",
]

# Raw scrape / legacy araclar key aliases → clean field
_RAW_ALIASES: dict[str, tuple[str, ...]] = {
    "ilan_url": ("ilan_url", "URL", "url", "Url", "ilan_url"),
    "Baslik": ("Baslik", "Başlık", "baslik", "title"),
    "Fiyat": ("Fiyat", "fiyat", "price", "Fiyat_Ham"),
    "Marka": ("Marka", "marka"),
    "Seri": ("Seri", "seri"),
    "Model": ("Model", "model", "Trim"),
    "Yil": ("Yil", "Yıl", "yil", "year"),
    "Kilometre": ("Kilometre", "km", "Km"),
    "Yakit_Tipi": ("Yakit_Tipi", "Yakıt Tipi", "Yakit Tipi"),
    "Vites_Tipi": ("Vites_Tipi", "Vites Tipi"),
    "Kasa_Tipi": ("Kasa_Tipi", "Kasa Tipi"),
    "Cekis": ("Cekis", "Çekiş", "Cekiş"),
    "Renk": ("Renk",),
    "Kimden": ("Kimden",),
    "Garanti_Durumu": ("Garanti_Durumu", "Garanti Durumu"),
    "Silindir_Sayisi": ("Silindir_Sayisi", "Silindir Sayısı"),
    "Koltuk_Sayisi": ("Koltuk_Sayisi", "Koltuk Sayısı"),
    "Motor_Hacmi": ("Motor_Hacmi", "Motor Hacmi"),
    "Motor_Gucu": ("Motor_Gucu", "Motor Gücü"),
    "Il": ("Il", "İl", "Sehir", "Şehir"),
    "Ilce": ("Ilce", "İlçe"),
    "Tramer_Tutari_Raw": ("Tramer_Tutari", "Tramer Tutarı", "Tramer_TL", "Tramer Kaydı:"),
    "Boya_Raw": ("Boya_Degisen_Tramer", "Boya_Degisen", "Boya:", "boya_degisen"),
    "Boyanan_Parcalar": ("Boyanan Parçalar", "Boyanan_Parcalar"),
    "Lokal_Boya": ("Lokal Boyalı Parçalar", "Lokal_Boya"),
    "scraped_at": ("scraped_at", "Scraped_At", "created_at"),
    "source": ("source", "Source"),
}

KNOWN_BRANDS = sorted(
    [
        "Fiat", "Renault", "Volkswagen", "Ford", "Toyota",
        "Hyundai", "BMW", "Mercedes-Benz", "Mercedes", "Peugeot", "Honda",
        "Dacia", "Opel", "Skoda", "Audi", "Kia", "Seat", "Mazda",
        "Volvo", "Nissan", "Mitsubishi", "Subaru", "Suzuki",
        "Citroën", "Citroen", "Jeep", "Mini", "Alfa Romeo", "Alfa",
        "Tofaş", "Tofas", "Porsche", "Land Rover", "SsangYong", "Ssangyong",
        "Chery", "Cupra", "DS", "Infiniti", "Lexus", "Jaguar", "Chrysler",
        "MG", "BYD", "Tesla", "Geely", "Haval", "Changan",
    ],
    key=len,
    reverse=True,
)

TITLE_PREFIX_RE = re.compile(
    r"^(Sahibinden|Galeriden|İkinci\s*El|Ikinci\s*El|2\.\s*El)\s+",
    re.IGNORECASE,
)

# Tab titles / empty scrape noise — NOT real damage status
_BOYA_JUNK = {
    "boya, degisen ve tramer",
    "boya degisen ve tramer",
    "sekme bulunamadi",
    "belirtilmedi",
    "belirtilmemis",
    "none",
    "nan",
    "null",
    "-",
    "",
}


def normalize_str(val: Any) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).replace("\u0131", "i").replace("\u0130", "i")
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def strip_title_prefix(baslik: str) -> str:
    s = baslik.strip()
    for _ in range(3):
        new = TITLE_PREFIX_RE.sub("", s).strip()
        if new == s:
            break
        s = new
    return s


def parse_marka(baslik: Any) -> str:
    if not isinstance(baslik, str):
        return "Diğer"
    s = strip_title_prefix(baslik)
    s_norm = normalize_str(s)
    for brand in KNOWN_BRANDS:
        b_norm = normalize_str(brand)
        if s_norm.startswith(b_norm):
            rest = s_norm[len(b_norm) :]
            if rest == "" or rest[0] in (" ", "-", "/"):
                if brand == "Citroen":
                    return "Citroën"
                if brand == "Tofas":
                    return "Tofaş"
                if brand == "Mercedes":
                    return "Mercedes-Benz"
                if brand == "Alfa":
                    return "Alfa Romeo"
                if brand == "Ssangyong":
                    return "SsangYong"
                return brand
    return "Diğer"


def parse_seri(baslik: Any, marka: str) -> str:
    if not isinstance(baslik, str) or not marka or marka == "Diğer":
        return "Diğer"
    s = strip_title_prefix(baslik)
    parts = s.split()
    s_norm = normalize_str(s)
    for brand in KNOWN_BRANDS:
        b_norm = normalize_str(brand)
        if s_norm.startswith(b_norm):
            rest = s_norm[len(b_norm) :]
            if rest == "" or rest[0] in (" ", "-", "/"):
                n = len(brand.split())
                return parts[n].title() if len(parts) > n else "Diğer"
    n = len(marka.split())
    return parts[n].title() if len(parts) > n else "Diğer"


def parse_yil_from_baslik(baslik: Any) -> Optional[int]:
    if not isinstance(baslik, str):
        return None
    m = re.search(r"\b((?:19|20)\d{2})\s*Model\b", baslik, re.I)
    if m:
        return int(m.group(1))
    for y in re.findall(r"\b((?:19|20)\d{2})\b", baslik):
        yi = int(y)
        if 1990 <= yi <= 2026:
            return yi
    return None


def parse_model(baslik: Any, seri: str, yil: Any) -> str:
    if not isinstance(baslik, str) or not isinstance(seri, str) or seri == "Diğer":
        return "Belirtilmemiş"
    try:
        yil_int = None
        if yil is not None and not (isinstance(yil, float) and pd.isna(yil)):
            yil_int = int(float(yil))
        if yil_int is None:
            yil_int = parse_yil_from_baslik(baslik)
        if yil_int is None:
            return "Belirtilmemiş"
        pattern = re.compile(
            re.escape(seri)
            + r"\s+(.*?)\s+"
            + re.escape(str(yil_int))
            + r"(?:\s*Model)?\b",
            re.IGNORECASE,
        )
        match = pattern.search(baslik)
        if match:
            var = match.group(1).strip()
            if not var or re.search(r"fiyatlar[ıi]|modelleri", var, re.I):
                return "Belirtilmemiş"
            return var
    except Exception:
        pass
    return "Belirtilmemiş"


def clean_price(val: Any) -> Optional[float]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    digits = re.sub(r"[^\d]", "", str(val))
    return float(digits) if digits else None


def clean_km(val: Any) -> Optional[float]:
    return clean_price(val)


def parse_tramer_tl(val: Any) -> float:
    """Rigid numeric Tramer TL. JS dumps / Belirtilmedi → 0."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return 0.0
    if isinstance(val, (int, float)):
        v = float(val)
        if v < 0 or v > 5_000_000:
            return 0.0
        return v

    s = str(val).strip()
    if not s:
        return 0.0
    if len(s) > 120:
        return 0.0
    low = normalize_str(s)
    if any(
        junk in low
        for junk in (
            "window.productdetail",
            "belirtilmedi",
            "belirtilmemis",
            "sekme bulunamadi",
            "yok",
            "none",
            "null",
            "nan",
            "{",
            "}",
        )
    ):
        # Explicit "tramer yok" etc. already 0; also reject JS
        if re.search(r"\d", s) and "tramer" in low and "yok" not in low and "{" not in s:
            pass  # fall through to digit parse for short strings
        else:
            return 0.0
    if low in {"-", "0", "0 tl", "0.0"}:
        return 0.0

    # Keep digits with Turkish thousand separators: 1.250.000 → 1250000
    cleaned = re.sub(r"[^\d,\.]", "", s)
    if not cleaned:
        return 0.0
    if cleaned.count(".") > 1 or (cleaned.count(".") == 1 and cleaned.count(",") == 0 and len(cleaned.split(".")[-1]) == 3):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        v = float(cleaned)
    except ValueError:
        return 0.0
    if v < 0 or v > 5_000_000:
        return 0.0
    return v


def parse_hasar_flags(
    boya_raw: Any = None,
    boyanan_parcalar: Any = None,
    lokal_boya: Any = None,
    tramer_tl: float = 0.0,
    tramer_raw: Any = None,
) -> dict[str, Any]:
    """
    Derive Has_Boya / Has_Degisen / Has_Tramer and Boya_Durumu.

    Tab-title noise ('Boya, Değişen ve Tramer') → Belirsiz (flags 0),
    so dead scrape labels do not fake damage.
    """
    chunks: list[str] = []
    for part in (boya_raw, boyanan_parcalar, lokal_boya, tramer_raw):
        if part is None or (isinstance(part, float) and pd.isna(part)):
            continue
        t = str(part).strip()
        if not t or len(t) > 500:
            continue
        if "window.productDetail" in t or t.startswith("{"):
            continue
        chunks.append(t)

    combined = " | ".join(chunks)
    norm = normalize_str(combined)

    # Pure junk / empty
    if not norm or all(normalize_str(c) in _BOYA_JUNK for c in chunks) or norm in _BOYA_JUNK:
        has_tramer = 1 if float(tramer_tl or 0) > 0 else 0
        return {
            "Boya_Durumu": "Tramerli" if has_tramer else "Belirsiz",
            "Has_Boya": 0,
            "Has_Degisen": 0,
            "Has_Tramer": has_tramer,
        }

    has_boya = 0
    has_degisen = 0
    has_tramer = 1 if float(tramer_tl or 0) > 0 else 0

    clean_hints = bool(
        re.search(r"boyas[iı]z|degisensiz|de[gğ]i[sş]ensiz|hatas[iı]z|orijinal boya|tramer\s*yok", norm)
    )
    if re.search(r"\bboyal[iı]\b|\bboyanan\b|lokal\s*boya|komple boya", norm) and not re.search(
        r"boyas[iı]z", norm
    ):
        has_boya = 1
    if re.search(r"de[gğ]i[sş]en", norm) and not re.search(r"de[gğ]i[sş]ensiz|degisensiz", norm):
        # Avoid matching the junk tab title alone (already handled); real "değişen" parts
        if "boya, degisen ve tramer" not in norm or has_boya or "parca" in norm or "kapı" in norm or "kapi" in norm:
            if norm != "boya, degisen ve tramer":
                has_degisen = 1
    if re.search(r"tramer", norm) and not re.search(r"tramer\s*yok|tramersiz", norm):
        if "boya, degisen ve tramer" not in norm:
            has_tramer = 1

    # Explicit clean statement wins when no positive damage tokens beyond junk
    if clean_hints and has_boya == 0 and has_degisen == 0:
        has_tramer = 1 if float(tramer_tl or 0) > 0 else 0

    if has_boya and has_degisen:
        status = "Boyalı+Değişen"
    elif has_degisen:
        status = "Değişenli"
    elif has_boya:
        status = "Boyalı"
    elif has_tramer:
        status = "Tramerli"
    elif clean_hints:
        status = "Temiz"
    else:
        status = "Belirsiz"

    return {
        "Boya_Durumu": status,
        "Has_Boya": int(has_boya),
        "Has_Degisen": int(has_degisen),
        "Has_Tramer": int(has_tramer),
    }


def _pick(raw: Mapping[str, Any], clean_key: str) -> Any:
    for alias in _RAW_ALIASES.get(clean_key, (clean_key,)):
        if alias in raw and raw[alias] is not None and str(raw[alias]).strip() != "":
            return raw[alias]
    return None


def normalize_raw_listing(raw: Mapping[str, Any], source: str = "import") -> Optional[dict[str, Any]]:
    """Map a dirty scrape dict → whitelist row. Returns None if no URL/Baslik."""
    if not isinstance(raw, Mapping):
        return None
    if raw.get("Hata"):
        return None

    url = _pick(raw, "ilan_url")
    baslik = _pick(raw, "Baslik")
    if not url and not baslik:
        return None
    url_s = str(url).strip() if url else None
    if url_s == "":
        url_s = None

    fiyat = clean_price(_pick(raw, "Fiyat"))
    km = clean_km(_pick(raw, "Kilometre"))
    yil_raw = _pick(raw, "Yil")
    yil: Optional[int] = None
    if yil_raw is not None:
        try:
            yil = int(float(re.sub(r"[^\d]", "", str(yil_raw)) or "nan"))
        except ValueError:
            yil = None
    if yil is None and isinstance(baslik, str):
        yil = parse_yil_from_baslik(baslik)

    marka = _pick(raw, "Marka")
    if marka:
        marka = str(marka).strip()
    elif isinstance(baslik, str):
        marka = parse_marka(baslik)
    else:
        marka = "Diğer"

    seri = _pick(raw, "Seri")
    if seri:
        seri = str(seri).strip()
    elif isinstance(baslik, str):
        seri = parse_seri(baslik, marka)
    else:
        seri = "Diğer"

    model = _pick(raw, "Model")
    if model:
        model = str(model).strip()
    elif isinstance(baslik, str):
        model = parse_model(baslik, seri, yil)
    else:
        model = "Belirtilmemiş"

    tramer_raw = _pick(raw, "Tramer_Tutari_Raw")
    tramer_tl = parse_tramer_tl(tramer_raw)
    # Prefer explicit numeric if scraper already sent Tramer_TL
    if "Tramer_TL" in raw and raw["Tramer_TL"] is not None:
        parsed = parse_tramer_tl(raw["Tramer_TL"])
        if parsed > 0 or tramer_tl == 0:
            tramer_tl = parsed

    boya_raw = _pick(raw, "Boya_Raw")
    boyanan = _pick(raw, "Boyanan_Parcalar")
    lokal = _pick(raw, "Lokal_Boya")
    # Prefer explicit flags from clean scrape batches
    if all(k in raw for k in ("Has_Boya", "Has_Degisen", "Has_Tramer")):
        has_boya = int(raw.get("Has_Boya") or 0)
        has_degisen = int(raw.get("Has_Degisen") or 0)
        has_tramer = int(raw.get("Has_Tramer") or 0) or (1 if tramer_tl > 0 else 0)
        if has_boya and has_degisen:
            boya_durumu = "Boyalı+Değişen"
        elif has_degisen:
            boya_durumu = "Değişenli"
        elif has_boya:
            boya_durumu = "Boyalı"
        elif has_tramer:
            boya_durumu = "Tramerli"
        else:
            boya_durumu = str(raw.get("Boya_Durumu") or "Belirsiz")
        flags = {
            "Boya_Durumu": boya_durumu,
            "Has_Boya": has_boya,
            "Has_Degisen": has_degisen,
            "Has_Tramer": has_tramer,
        }
    else:
        flags = parse_hasar_flags(boya_raw, boyanan, lokal, tramer_tl, tramer_raw)

    scraped = _pick(raw, "scraped_at")
    if scraped is None:
        scraped = datetime.now(timezone.utc).isoformat()
    else:
        scraped = str(scraped)

    src = _pick(raw, "source") or source

    def _str(v: Any) -> Optional[str]:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        t = str(v).strip()
        return t if t else None

    return {
        "ilan_url": url_s,
        "Baslik": _str(baslik),
        "Fiyat": fiyat,
        "Marka": marka,
        "Seri": seri,
        "Model": model,
        "Yil": yil,
        "Kilometre": km,
        "Yakit_Tipi": _str(_pick(raw, "Yakit_Tipi")),
        "Vites_Tipi": _str(_pick(raw, "Vites_Tipi")),
        "Kasa_Tipi": _str(_pick(raw, "Kasa_Tipi")),
        "Cekis": _str(_pick(raw, "Cekis")),
        "Renk": _str(_pick(raw, "Renk")),
        "Kimden": _str(_pick(raw, "Kimden")),
        "Garanti_Durumu": _str(_pick(raw, "Garanti_Durumu")),
        "Silindir_Sayisi": _str(_pick(raw, "Silindir_Sayisi")),
        "Koltuk_Sayisi": _str(_pick(raw, "Koltuk_Sayisi")),
        "Motor_Hacmi": _str(_pick(raw, "Motor_Hacmi")),
        "Motor_Gucu": _str(_pick(raw, "Motor_Gucu")),
        "Il": _str(_pick(raw, "Il")),
        "Ilce": _str(_pick(raw, "Ilce")),
        "Tramer_Tutari_Raw": _str(tramer_raw)[:120] if tramer_raw is not None else None,
        "Tramer_TL": float(tramer_tl),
        "Boya_Raw": _str(boya_raw)[:200] if boya_raw is not None else None,
        "Boyanan_Parcalar": _str(boyanan)[:200] if boyanan is not None else None,
        "Lokal_Boya": _str(lokal)[:200] if lokal is not None else None,
        "Boya_Durumu": flags["Boya_Durumu"],
        "Has_Boya": int(flags["Has_Boya"]),
        "Has_Degisen": int(flags["Has_Degisen"]),
        "Has_Tramer": int(flags["Has_Tramer"]),
        "scraped_at": scraped,
        "source": str(src)[:80],
    }


def get_engine(db_url: Optional[str] = None) -> Engine:
    url = db_url or os.getenv(
        "DB_URL",
        "postgresql+psycopg2://postgres:sifre123@localhost:5432/postgres",
    )
    return create_engine(url, pool_pre_ping=True)


def ensure_clean_table(engine: Optional[Engine] = None) -> Engine:
    """Create araclar_clean + unique(ilan_url). Dedupe legacy araclar.URL when possible."""
    eng = engine or get_engine()
    ddl = """
    CREATE TABLE IF NOT EXISTS araclar_clean (
        id BIGSERIAL PRIMARY KEY,
        ilan_url TEXT,
        "Baslik" TEXT,
        "Fiyat" DOUBLE PRECISION,
        "Marka" TEXT,
        "Seri" TEXT,
        "Model" TEXT,
        "Yil" INTEGER,
        "Kilometre" DOUBLE PRECISION,
        "Yakit_Tipi" TEXT,
        "Vites_Tipi" TEXT,
        "Kasa_Tipi" TEXT,
        "Cekis" TEXT,
        "Renk" TEXT,
        "Kimden" TEXT,
        "Garanti_Durumu" TEXT,
        "Silindir_Sayisi" TEXT,
        "Koltuk_Sayisi" TEXT,
        "Motor_Hacmi" TEXT,
        "Motor_Gucu" TEXT,
        "Il" TEXT,
        "Ilce" TEXT,
        "Tramer_Tutari_Raw" TEXT,
        "Tramer_TL" DOUBLE PRECISION DEFAULT 0,
        "Boya_Raw" TEXT,
        "Boyanan_Parcalar" TEXT,
        "Lokal_Boya" TEXT,
        "Boya_Durumu" TEXT,
        "Has_Boya" SMALLINT DEFAULT 0,
        "Has_Degisen" SMALLINT DEFAULT 0,
        "Has_Tramer" SMALLINT DEFAULT 0,
        scraped_at TIMESTAMPTZ,
        source TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    with eng.begin() as conn:
        conn.execute(text(ddl))
        # Partial unique: allow NULL urls but unique when present
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_araclar_clean_ilan_url
                ON araclar_clean (ilan_url)
                WHERE ilan_url IS NOT NULL
                """
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_araclar_clean_marka ON araclar_clean (\"Marka\")"
            )
        )

        # Legacy araclar: dedupe URLs then unique index (best-effort)
        try:
            has_araclar = conn.execute(
                text(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_name='araclar' LIMIT 1"
                )
            ).scalar()
            if has_araclar:
                conn.execute(
                    text(
                        """
                        DELETE FROM araclar a
                        USING araclar b
                        WHERE a.ctid < b.ctid
                          AND a."URL" IS NOT NULL
                          AND a."URL" = b."URL"
                        """
                    )
                )
                conn.execute(
                    text(
                        """
                        CREATE UNIQUE INDEX IF NOT EXISTS uq_araclar_url
                        ON araclar ("URL")
                        WHERE "URL" IS NOT NULL
                        """
                    )
                )
        except Exception as e:
            print(f"⚠️ Legacy araclar URL unique atlanamadı/uygulanamadı: {e}")

    return eng


def existing_clean_urls(engine: Engine) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT ilan_url FROM araclar_clean WHERE ilan_url IS NOT NULL")
        ).fetchall()
    return {r[0] for r in rows if r[0]}


def append_clean_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    engine: Optional[Engine] = None,
    source: str = "import",
    skip_existing_urls: bool = True,
) -> dict[str, int]:
    """
    Normalize + append whitelist rows into araclar_clean.
    Never uses if_exists='replace'. Never adds dynamic columns.
    """
    eng = ensure_clean_table(engine)
    normalized: list[dict[str, Any]] = []
    for raw in rows:
        row = normalize_raw_listing(raw, source=source)
        if row is None:
            continue
        normalized.append(row)

    stats = {"received": len(normalized), "inserted": 0, "skipped_dup": 0, "skipped_no_url": 0}
    if not normalized:
        return stats

    existing = existing_clean_urls(eng) if skip_existing_urls else set()
    to_insert: list[dict[str, Any]] = []
    for row in normalized:
        url = row.get("ilan_url")
        if not url:
            # Allow insert without URL but cannot dedupe — skip to keep uniqueness meaningful
            stats["skipped_no_url"] += 1
            continue
        if url in existing:
            stats["skipped_dup"] += 1
            continue
        existing.add(url)
        to_insert.append(row)

    if not to_insert:
        return stats

    df = pd.DataFrame(to_insert)
    # Strict column order / whitelist only
    for col in CLEAN_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[CLEAN_COLUMNS]

    df.to_sql(
        "araclar_clean",
        eng,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=200,
    )
    stats["inserted"] = len(df)
    return stats


def backfill_from_legacy_araclar(
    engine: Optional[Engine] = None,
    *,
    limit: Optional[int] = None,
    source: str = "legacy_araclar",
) -> dict[str, int]:
    """One-shot: map dirty araclar → araclar_clean (append, URL dedupe)."""
    eng = ensure_clean_table(engine)
    q = 'SELECT * FROM araclar WHERE "Baslik" IS NOT NULL'
    if limit:
        q += f" LIMIT {int(limit)}"
    df = pd.read_sql(q, eng)
    rows = df.to_dict(orient="records")
    return append_clean_rows(rows, engine=eng, source=source)


def load_clean_dataframe(engine: Optional[Engine] = None) -> pd.DataFrame:
    """Load araclar_clean; if empty, import from local jsonl or backfill from legacy then reload."""
    eng = ensure_clean_table(engine)
    with eng.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM araclar_clean")).scalar() or 0
    if n == 0:
        if os.path.exists("seed_data.jsonl"):
            print("araclar_clean boş — seed_data.jsonl'den import ediliyor...")
            try:
                stats = import_jsonl("seed_data.jsonl", engine=eng)
                print(f"  JSONL import: {stats}")
            except Exception as e:
                print(f"⚠️ JSONL import hatası (seed_data.jsonl): {e}")
        elif os.path.exists("araba_verileri.jsonl"):
            print("araclar_clean boş — araba_verileri.jsonl'den import ediliyor...")
            try:
                stats = import_jsonl("araba_verileri.jsonl", engine=eng)
                print(f"  JSONL import: {stats}")
            except Exception as e:
                print(f"⚠️ JSONL import hatası (araba_verileri.jsonl): {e}")
        elif os.path.exists("dev_veriseti.jsonl"):
            print("araclar_clean boş — dev_veriseti.jsonl'den import ediliyor...")
            try:
                stats = import_jsonl("dev_veriseti.jsonl", engine=eng)
                print(f"  JSONL import: {stats}")
            except Exception as e:
                print(f"⚠️ JSONL import hatası (dev_veriseti.jsonl): {e}")
        else:
            print("araclar_clean boş — legacy araclar'dan backfill...")
            try:
                stats = backfill_from_legacy_araclar(eng)
                print(f"  backfill: {stats}")
            except Exception as e:
                print(f"⚠️ Legacy backfill hatası (muhtemelen 'araclar' tablosu yok): {e}")
    return pd.read_sql("SELECT * FROM araclar_clean", eng)


def import_jsonl(
    path: str,
    *,
    engine: Optional[Engine] = None,
    source: str = "jsonl",
) -> dict[str, int]:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return append_clean_rows(rows, engine=engine, source=source)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="araclar_clean schema / import tools")
    p.add_argument("--ensure", action="store_true", help="Create table + URL indexes")
    p.add_argument("--backfill", action="store_true", help="Backfill from legacy araclar")
    p.add_argument("--jsonl", type=str, default=None, help="Import JSONL append-only")
    args = p.parse_args()

    eng = get_engine()
    if args.ensure or args.backfill or args.jsonl:
        ensure_clean_table(eng)
    if args.backfill:
        print(backfill_from_legacy_araclar(eng))
    if args.jsonl:
        print(import_jsonl(args.jsonl, engine=eng))
    if not any([args.ensure, args.backfill, args.jsonl]):
        ensure_clean_table(eng)
        print("araclar_clean hazır.")
