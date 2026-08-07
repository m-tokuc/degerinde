"""
Safe data import → araclar_clean (append-only, URL dedupe, whitelist columns).

NEVER uses if_exists='replace'. Never writes dirty/dynamic scrape columns.

Usage:
  python import_data.py
  python import_data.py --jsonl batch1_vw_ford_opel.jsonl
  python import_data.py --backfill-legacy
"""
from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from schema_clean import (  # noqa: E402
    backfill_from_legacy_araclar,
    ensure_clean_table,
    get_engine,
    import_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Değerinde safe import (append-only)")
    parser.add_argument(
        "--jsonl",
        default=os.getenv("IMPORT_JSONL", "dev_veriseti.jsonl"),
        help="JSONL path to import (default: dev_veriseti.jsonl)",
    )
    parser.add_argument(
        "--backfill-legacy",
        action="store_true",
        help="Map existing dirty araclar rows into araclar_clean",
    )
    parser.add_argument(
        "--ensure-only",
        action="store_true",
        help="Only create araclar_clean + unique URL indexes",
    )
    args = parser.parse_args()

    engine = get_engine()
    ensure_clean_table(engine)
    print("✅ araclar_clean schema + URL unique index ready (append-only).")

    if args.ensure_only:
        return 0

    if args.backfill_legacy:
        stats = backfill_from_legacy_araclar(engine, source="legacy_araclar")
        print(
            f"Legacy backfill → inserted={stats['inserted']} "
            f"dup_skip={stats['skipped_dup']} no_url={stats['skipped_no_url']} "
            f"received={stats['received']}"
        )

    if args.jsonl and os.path.exists(args.jsonl) and not args.backfill_legacy:
        stats = import_jsonl(args.jsonl, engine=engine, source=os.path.basename(args.jsonl))
        print(
            f"JSONL import ({args.jsonl}) → inserted={stats['inserted']} "
            f"dup_skip={stats['skipped_dup']} no_url={stats['skipped_no_url']} "
            f"received={stats['received']}"
        )
    elif args.jsonl and not args.backfill_legacy and not os.path.exists(args.jsonl):
        print(f"⚠️ JSONL bulunamadı: {args.jsonl}", file=sys.stderr)
        if not args.backfill_legacy:
            print("İpucu: python import_data.py --backfill-legacy")
            return 1

    with engine.connect() as conn:
        from sqlalchemy import text

        total = conn.execute(text("SELECT COUNT(*) FROM araclar_clean")).scalar()
        brands = conn.execute(
            text(
                'SELECT "Marka", COUNT(*) c FROM araclar_clean '
                'GROUP BY 1 ORDER BY c DESC LIMIT 12'
            )
        ).fetchall()
    print(f"araclar_clean toplam satır: {total}")
    for marka, c in brands:
        print(f"  {marka}: {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
