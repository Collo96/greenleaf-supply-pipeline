# 🌿 Greenleaf Supply — Data Engineering Pipeline
**Monthly Excel → ETL Pipeline → Cloud Database → Live Dashboard**

Full year 2025 business intelligence system processing Sales, Inventory, Customer Orders and Supplier data from monthly Excel files.

---

## Project Structure
```
greenleaf-pipeline/
├── 00_generate_excel_data.py  # Generate sample Excel files (or use your real ones)
├── 01_extract.py              # Read all 12 monthly Excel files
├── 02_transform.py            # Clean, enrich and validate data
├── 03_load.py                 # Load into PostgreSQL (Neon.tech)
├── 04_dashboard.py            # Streamlit analytics dashboard
├── requirements.txt
├── .github/workflows/etl.yml  # Auto-run pipeline monthly
└── data/
    └── raw/                   # Drop your Excel files here
```

---

## Using Your Real Excel Files

Name your files exactly:
```
data/raw/2025_01_january.xlsx
data/raw/2025_02_february.xlsx
...
data/raw/2025_12_december.xlsx
```

Each file needs these sheet names:
- `Sales_Transactions`
- `Inventory`
- `Customer_Orders`
- `Supplier_Orders`

---

## Quick Start

```bash
pip install -r requirements.txt

# Use sample data (or skip if you have real Excel files)
python 00_generate_excel_data.py

# Run the pipeline
python 01_extract.py
python 02_transform.py
python 03_load.py

# Launch dashboard
streamlit run 04_dashboard.py
```

---

## Cloud Deployment

1. Push to GitHub
2. Get free PostgreSQL at [neon.tech](https://neon.tech)
3. Set `DATABASE_URL` environment variable
4. Deploy dashboard at [share.streamlit.io](https://share.streamlit.io)

---

## Dashboard Features

| Tab | What it shows |
|-----|--------------|
| Sales | Monthly revenue, profit margins, top products, payment methods |
| Inventory | Stock levels, reorder alerts, stock value by category |
| Orders | Delivery rates, county performance, order status |
| Suppliers | Spend by supplier, category breakdown, monthly trends |
