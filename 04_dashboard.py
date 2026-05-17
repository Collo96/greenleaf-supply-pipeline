"""
04_dashboard.py
===============
Greenleaf Supply Company - Business Intelligence Dashboard
Full year 2025 analytics across Sales, Inventory, Orders and Suppliers.

Run locally:
    streamlit run 04_dashboard.py

Deploy on Streamlit Cloud:
    Add DATABASE_URL to secrets.toml
"""

import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Greenleaf Supply Analytics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom styling ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-container { background: #f0f7f0; border-radius: 10px; padding: 12px; }
.stMetric label { font-size: 13px !important; }
</style>
""", unsafe_allow_html=True)

st.title("🌿 Greenleaf Supply Company")
st.caption("Business Intelligence Dashboard — January to December 2025")


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_all():
    db_url = (
        st.secrets.get("DATABASE_URL", None)
        if hasattr(st, "secrets") else None
    ) or os.environ.get("DATABASE_URL")

    if db_url:
        engine = create_engine(
            db_url.replace("postgresql://", "postgresql+psycopg://")
        )
        sales     = pd.read_sql("SELECT * FROM gl_sales",     engine)
        inventory = pd.read_sql("SELECT * FROM gl_inventory", engine)
        orders    = pd.read_sql("SELECT * FROM gl_orders",    engine)
        suppliers = pd.read_sql("SELECT * FROM gl_suppliers", engine)
    else:
        # Fallback: load from local SQLite
        sqlite = "sqlite:///data/greenleaf.db"
        engine = create_engine(sqlite)
        try:
            sales     = pd.read_sql("SELECT * FROM gl_sales",     engine)
            inventory = pd.read_sql("SELECT * FROM gl_inventory", engine)
            orders    = pd.read_sql("SELECT * FROM gl_orders",    engine)
            suppliers = pd.read_sql("SELECT * FROM gl_suppliers", engine)
        except Exception:
            st.error("No database found. Run the pipeline first:\n"
                     "python 00_generate_excel_data.py\n"
                     "python 01_extract.py\n"
                     "python 02_transform.py\n"
                     "python 03_load.py")
            st.stop()

    # Fix types
    for df in [sales, inventory, orders, suppliers]:
        for col in df.select_dtypes(include="object").columns:
            try:
                df[col] = df[col].replace("None", pd.NA)
            except Exception:
                pass

    sales["revenue_kes"]      = pd.to_numeric(sales["revenue_kes"],      errors="coerce")
    sales["profit_kes"]       = pd.to_numeric(sales["profit_kes"],        errors="coerce")
    sales["cost_kes"]         = pd.to_numeric(sales["cost_kes"],          errors="coerce")
    sales["quantity"]         = pd.to_numeric(sales["quantity"],          errors="coerce")
    sales["date"]             = pd.to_datetime(sales["date"],             errors="coerce")
    orders["order_total_kes"] = pd.to_numeric(orders["order_total_kes"],  errors="coerce")
    orders["is_delivered"]    = pd.to_numeric(orders["is_delivered"],     errors="coerce")
    orders["delivery_days"]   = pd.to_numeric(orders["delivery_days"],    errors="coerce")
    suppliers["amount_kes"]   = pd.to_numeric(suppliers["amount_kes"],    errors="coerce")
    inventory["stock_value_kes"]  = pd.to_numeric(inventory["stock_value_kes"], errors="coerce")
    inventory["closing_stock"]    = pd.to_numeric(inventory["closing_stock"],   errors="coerce")
    inventory["reorder_level"]    = pd.to_numeric(inventory["reorder_level"],   errors="coerce")

    return sales, inventory, orders, suppliers


sales, inventory, orders, suppliers = load_all()

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.header("Filters")
st.sidebar.image("https://via.placeholder.com/200x60/2d6a2d/ffffff?text=Greenleaf+Supply",
                 use_column_width=True)

all_months = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]
sel_months = st.sidebar.multiselect("Month", all_months, default=[])
sel_cat    = st.sidebar.multiselect("Category", sorted(sales["category"].dropna().unique()), default=[])

s = sales.copy()
if sel_months: s = s[s["month_name"].isin(sel_months)]
if sel_cat:    s = s[s["category"].isin(sel_cat)]

o = orders.copy()
if sel_months: o = o[o["month_name"].isin(sel_months)]

# ── Tab navigation ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Sales", "Inventory", "Orders", "Suppliers"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: SALES
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Sales Performance 2025")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Revenue",  f"KES {s['revenue_kes'].sum():,.0f}")
    k2.metric("Total Profit",   f"KES {s['profit_kes'].sum():,.0f}")
    k3.metric("Transactions",   f"{len(s):,}")
    k4.metric("Avg Margin",     f"{s['profit_kes'].sum()/s['revenue_kes'].sum()*100:.1f}%")
    k5.metric("Units Sold",     f"{s['quantity'].sum():,.0f}")

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        monthly = s.groupby("month_name")["revenue_kes"].sum().reindex(all_months).dropna()
        fig = px.bar(
            x=monthly.index, y=monthly.values,
            title="Monthly Revenue (KES)",
            labels={"x": "Month", "y": "Revenue (KES)"},
            color=monthly.values,
            color_continuous_scale="Greens",
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False, height=320)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        cat_rev = s.groupby("category")["revenue_kes"].sum().reset_index()
        fig2 = px.pie(
            cat_rev, names="category", values="revenue_kes",
            title="Revenue by Product Category",
            color_discrete_sequence=px.colors.sequential.Greens_r,
        )
        fig2.update_layout(height=320)
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        monthly_profit = s.groupby("month_name")[["revenue_kes","profit_kes"]].sum().reindex(all_months).dropna()
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Revenue", x=monthly_profit.index, y=monthly_profit["revenue_kes"], marker_color="#2d6a2d"))
        fig3.add_trace(go.Bar(name="Profit",  x=monthly_profit.index, y=monthly_profit["profit_kes"],  marker_color="#74c476"))
        fig3.update_layout(barmode="group", title="Revenue vs Profit by Month", height=320)
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        top_products = s.groupby("product_name")["revenue_kes"].sum().nlargest(8).reset_index()
        fig4 = px.bar(
            top_products, x="revenue_kes", y="product_name", orientation="h",
            title="Top 8 Products by Revenue",
            color="revenue_kes", color_continuous_scale="Greens",
        )
        fig4.update_layout(height=320, coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig4, use_container_width=True)

    # Payment method breakdown
    pay = s["payment_method"].value_counts().reset_index()
    pay.columns = ["method", "count"]
    fig5 = px.bar(pay, x="method", y="count", title="Transactions by Payment Method",
                  color="count", color_continuous_scale="Greens")
    fig5.update_layout(height=260, coloraxis_showscale=False)
    st.plotly_chart(fig5, use_container_width=True)

    # Download
    csv = s.to_csv(index=False).encode("utf-8")
    st.download_button("Download Sales Data CSV", csv, "greenleaf_sales_2025.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: INVENTORY
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Inventory Management 2025")

    inv = inventory.copy()
    if sel_months:
        inv = inv[inv["month_name"].isin(sel_months)]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Stock Value", f"KES {inv['stock_value_kes'].sum():,.0f}")
    k2.metric("Products Tracked",  inv["product_id"].nunique())
    k3.metric("Reorder Alerts",    (inv["needs_reorder"] == "Yes").sum())
    k4.metric("High Risk Items",   (inv["stockout_risk"] == "High").sum())

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        reorder = inv[inv["needs_reorder"] == "Yes"].groupby("product_name")["closing_stock"].mean().nsmallest(10).reset_index()
        fig = px.bar(
            reorder, x="closing_stock", y="product_name", orientation="h",
            title="Products Needing Reorder (Lowest Stock)",
            color="closing_stock", color_continuous_scale="Reds_r",
        )
        fig.update_layout(height=340, coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        cat_val = inv.groupby("category")["stock_value_kes"].sum().reset_index()
        fig2 = px.pie(
            cat_val, names="category", values="stock_value_kes",
            title="Stock Value by Category",
            color_discrete_sequence=px.colors.sequential.Greens_r,
        )
        fig2.update_layout(height=340)
        st.plotly_chart(fig2, use_container_width=True)

    # Monthly stock value trend
    monthly_stock = inv.groupby("month_name")["stock_value_kes"].sum().reindex(all_months).dropna()
    fig3 = px.line(
        x=monthly_stock.index, y=monthly_stock.values,
        title="Monthly Stock Value Trend (KES)",
        labels={"x": "Month", "y": "Stock Value (KES)"},
        markers=True,
    )
    fig3.update_traces(line_color="#2d6a2d", line_width=2.5)
    fig3.update_layout(height=280)
    st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: ORDERS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Customer Orders 2025")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Orders",    f"{len(o):,}")
    k2.metric("Total Value",     f"KES {o['order_total_kes'].sum():,.0f}")
    k3.metric("Delivery Rate",   f"{o['is_delivered'].mean()*100:.1f}%")
    k4.metric("Avg Delivery",    f"{o['delivery_days'].mean():.1f} days")

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        monthly_orders = o.groupby("month_name")["order_total_kes"].sum().reindex(all_months).dropna()
        fig = px.bar(
            x=monthly_orders.index, y=monthly_orders.values,
            title="Monthly Order Value (KES)",
            color=monthly_orders.values, color_continuous_scale="Blues",
        )
        fig.update_layout(height=320, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        county_orders = o.groupby("county")["order_total_kes"].sum().nlargest(8).reset_index()
        fig2 = px.bar(
            county_orders, x="order_total_kes", y="county", orientation="h",
            title="Top Counties by Order Value",
            color="order_total_kes", color_continuous_scale="Blues",
        )
        fig2.update_layout(height=320, coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    status_counts = o["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig3 = px.pie(status_counts, names="status", values="count",
                  title="Order Status Breakdown",
                  color_discrete_map={"Delivered":"#2d6a2d","Pending":"#f9a825","Cancelled":"#c62828"})
    fig3.update_layout(height=280)
    st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: SUPPLIERS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Supplier Spend 2025")

    sup = suppliers.copy()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Spend",    f"KES {sup['amount_kes'].sum():,.0f}")
    k2.metric("Suppliers",      sup["supplier_id"].nunique())
    k3.metric("Purchase Orders", len(sup))
    k4.metric("Paid Orders",    f"{sup['is_paid'].mean()*100:.1f}%")

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        sup_spend = sup.groupby("supplier_name")["amount_kes"].sum().reset_index().sort_values("amount_kes", ascending=False)
        fig = px.bar(
            sup_spend, x="amount_kes", y="supplier_name", orientation="h",
            title="Spend by Supplier (KES)",
            color="amount_kes", color_continuous_scale="Greens",
        )
        fig.update_layout(height=320, coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        cat_spend = sup.groupby("category")["amount_kes"].sum().reset_index()
        fig2 = px.pie(
            cat_spend, names="category", values="amount_kes",
            title="Spend by Category",
            color_discrete_sequence=px.colors.sequential.Greens_r,
        )
        fig2.update_layout(height=320)
        st.plotly_chart(fig2, use_container_width=True)

    monthly_sup = sup.groupby("month_name")["amount_kes"].sum().reindex(all_months).dropna()
    fig3 = px.line(
        x=monthly_sup.index, y=monthly_sup.values,
        title="Monthly Supplier Spend (KES)",
        markers=True,
        labels={"x": "Month", "y": "Amount (KES)"},
    )
    fig3.update_traces(line_color="#2d6a2d", line_width=2.5)
    fig3.update_layout(height=280)
    st.plotly_chart(fig3, use_container_width=True)
