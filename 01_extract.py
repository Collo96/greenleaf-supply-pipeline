"""
01_extract.py
=============
Phase 1 - EXTRACT
Reads all monthly Excel files from data/raw/ and combines
them into unified staging Parquet files per data type.

Handles YOUR real Excel files automatically - just drop them
in data/raw/ named as: 2025_01_january.xlsx etc.

Run:
    python 01_extract.py
"""

import os
import glob
import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/extract.log", mode="a"),
    ],
)
log = logging.getLogger(__name__)

RAW_DIR     = "data/raw"
STAGING_DIR = "data/staging"

SHEET_CONFIG = {
    "Sales_Transactions": {
        "out_file": "staging_sales.parquet",
        "required_cols": ["transaction_id", "date", "customer_id", "product_id",
                          "quantity", "revenue_kes", "cost_kes"],
    },
    "Inventory": {
        "out_file": "staging_inventory.parquet",
        "required_cols": ["product_id", "opening_stock", "closing_stock",
                          "stock_value_kes"],
    },
    "Customer_Orders": {
        "out_file": "staging_orders.parquet",
        "required_cols": ["order_id", "order_date", "customer_id",
                          "order_total_kes", "status"],
    },
    "Supplier_Orders": {
        "out_file": "staging_suppliers.parquet",
        "required_cols": ["po_id", "order_date", "supplier_id", "amount_kes"],
    },
}


def find_excel_files() -> list:
    """Find all monthly Excel files in data/raw/."""
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.xlsx")))
    if not files:
        raise FileNotFoundError(
            f"No Excel files found in {RAW_DIR}/\n"
            "Run python 00_generate_excel_data.py first, or drop your real files there."
        )
    log.info(f"Found {len(files)} Excel files:")
    for f in files:
        log.info(f"  {os.path.basename(f)}")
    return files


def extract_sheet(files: list, sheet_name: str) -> pd.DataFrame:
    """Read one sheet from all monthly files and combine into one DataFrame."""
    frames = []
    for filepath in files:
        filename = os.path.basename(filepath)
        try:
            df = pd.read_excel(filepath, sheet_name=sheet_name, dtype=str)
            # Add source file tracking
            df["source_file"] = filename
            df["source_month"] = filename[:7]  # e.g. "2025_01"
            frames.append(df)
            log.info(f"  Read {sheet_name} from {filename}: {len(df)} rows")
        except Exception as e:
            log.warning(f"  Could not read {sheet_name} from {filename}: {e}")

    if not frames:
        raise ValueError(f"No data found for sheet: {sheet_name}")

    combined = pd.concat(frames, ignore_index=True)
    log.info(f"Combined {sheet_name}: {len(combined):,} total rows")
    return combined


def validate_columns(df: pd.DataFrame, required: list, sheet: str) -> bool:
    missing = [c for c in required if c not in df.columns]
    if missing:
        log.error(f"Sheet '{sheet}' missing columns: {missing}")
        return False
    return True


def run():
    os.makedirs(STAGING_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    files = find_excel_files()

    for sheet_name, config in SHEET_CONFIG.items():
        log.info(f"\nExtracting sheet: {sheet_name}")
        df = extract_sheet(files, sheet_name)

        if validate_columns(df, config["required_cols"], sheet_name):
            out_path = os.path.join(STAGING_DIR, config["out_file"])
            df.to_parquet(out_path, index=False)
            log.info(f"Saved -> {out_path} ({len(df):,} rows)")

    log.info("\nExtract phase COMPLETE")


if __name__ == "__main__":
    run()
