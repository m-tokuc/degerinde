"""
Helper for the external scrape IDE: append already-parsed dicts into araclar_clean.

Usage from another machine/process sharing the same Postgres:

  from schema_clean import append_clean_rows, ensure_clean_table, get_engine
  ensure_clean_table(get_engine())
  stats = append_clean_rows(list_of_raw_dicts, source="tier1_scrape")
  print(stats)

Then hit POST /api/admin/reload_cache on the API and retrain:
  python train_model.py
"""
from __future__ import annotations

import argparse
import json
import sys

from schema_clean import append_clean_rows, ensure_clean_table, get_engine, import_jsonl


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--jsonl", required=True)
    p.add_argument("--source", default="external_scrape")
    args = p.parse_args()
    eng = get_engine()
    ensure_clean_table(eng)
    stats = import_jsonl(args.jsonl, engine=eng, source=args.source)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0 if stats.get("inserted", 0) >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
