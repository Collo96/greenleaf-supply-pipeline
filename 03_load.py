"""
03_load.py
==========
Phase 3 - LOAD
Loads all 4 clean datasets into PostgreSQL (Neon.tech).

Set DATABASE_URL environment variable before running:
    $env:DATABASE_URL="postgresql://..."
    python 03_load.py
"""

import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)

PROCESSED_DIR = "data/processed"

TABLES = [
    ("sales_clean.parquet",     "gl_sales"),
    ("inventory_clean.parquet", "gl_inventory"),
    ("orders_clean.parquet",    "gl_orders"),
    ("suppliers_clean.parquet", "gl_suppliers"),
]


def get_engine():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        db_url = "sqlite:///data/greenleaf.db"
        log.warning("DATABASE_URL not set - using local SQLite")
    engine = create_engine(
        db_url.replace("postgresql://", "postgresql+psycopg://"),
        echo=False
    )
    host = db_url.split("@")[-1] if "@" in db_url else db_url
    log.info(f"Connected to: {host}")
    return engine


def clear_tables(engine):
    is_sqlite = "sqlite" in str(engine.url)
    with engine.connect() as conn:
        for _, table in TABLES:
            if is_sqlite:
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
            else:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        conn.commit()
    log.info("Cleared existing tables")


def load_table(df: pd.DataFrame, table_name: str, engine):
    # Convert all object columns to string to avoid type errors
    for col in df.select_dtypes(include=["object", "category"]).columns:
        df[col] = df[col].astype(str).replace("nan", None)

    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500,
        method="multi",
    )
    log.info(f"Loaded {len(df):,} rows into {table_name}")


def verify(engine):
    with engine.connect() as conn:
        for _, table in TABLES:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            log.info(f"  {table}: {count:,} rows")


def run():
    engine = get_engine()
    clear_tables(engine)

    for parquet_file, table_name in TABLES:
        path = os.path.join(PROCESSED_DIR, parquet_file)
        log.info(f"Loading {parquet_file} -> {table_name}")
        df = pd.read_parquet(path)
        load_table(df, table_name, engine)

    log.info("Verifying row counts...")
    verify(engine)
    log.info("Load phase COMPLETE")


if __name__ == "__main__":
    run()
