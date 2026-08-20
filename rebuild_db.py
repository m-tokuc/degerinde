import sys
import logging
from sqlalchemy import text
from app_db import engine
from schema_clean import ensure_clean_table, import_jsonl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rebuild_clean_db():
    logger.info("1. Dropping existing araclar_clean...")
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS araclar_clean CASCADE;"))
    
    logger.info("2. Re-creating araclar_clean with new 13-part schema...")
    ensure_clean_table(engine)
    
    logger.info("3. Starting NLP Backfill from araba_verileri.jsonl. This may take a few minutes...")
    # This will read all 140k rows and run them through our NLP regex
    stats = import_jsonl("araba_verileri.jsonl", engine=engine)
    
    logger.info("✅ BACKFILL COMPLETE!")
    logger.info(f"Stats: {stats}")

if __name__ == '__main__':
    rebuild_clean_db()
