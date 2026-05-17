import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import psycopg
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Greenleaf Supply Analytics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌿 Greenleaf Supply Company")
st.caption("Business Intelligence Dashboard — January to December 2025")


@st.cache_data(ttl=600)
def load_all():
    db_url = None
    try:
        db_url = st.secrets["DATABASE_URL"]
    except Exception:
        db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        st.error("No DATABASE_URL found. Add it to Streamlit secrets.")
        st.stop()

    def read(query):
        with psycopg.connect(db_url) as conn:
            return pd.read_sql(query, conn)

    sales     = read("SELECT * FROM gl_sales")
    inventory = read("SELECT * FROM gl_inventory")
    orders    = read("SELECT * FROM gl_orders")
    suppliers = read("SELECT * FROM gl_suppliers")

    for col in ["revenue_kes", "profit_kes", "cost_kes", "quantity"]:
        if col in sales.columns:
            sales[col] = pd.to_numeric(sales[col], errors="coerce")

    for col in ["order_total_kes", "is_delivered", "delivery_days"]:
        if col in orders.columns:
            orders[col] = pd.to_numeric(orders[col], errors="coerce")

    for col in ["amount_kes", "is_paid"]:
        if col in suppliers.columns:
            suppliers[col] = pd.to_numeric(suppliers[col], errors="coerce")

    for col in ["stock_value_kes", "closing_stock", "reorder_level"]:
        if col in inventory.columns:
            inventory[col] = pd.to_numeric(inventory[col], errors="coerce")

    return sales, inventory, orders, suppliers


sales, inventory, orders, suppliers = load_all()

ALL_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

st.sidebar.header("Filters")
sel_months = st.sidebar.multiselect("Month", ALL_MONTHS)
sel_cat    = st.sidebar.multiselect("Category", sorted(sales["category"].dropna().unique()))

s = sales.copy()
if sel_months: s = s[s["month_name"].isin(sel_months)]
if sel_cat:    s = s[s["category"].isin(sel_cat)]

o = orders.copy()
if sel_months: o = o[o["month_name"].isin(sel_months)]

tab1, tab2, tab3, tab4 = st.tabs(["Sales", "Inventory", "Orders", "Suppliers"])

with tab1:
    st.subheader("Sales Performance 2025")
    k1, k2, k3, k4, k5 = st.columns(5)
    total_rev  = s["revenue_kes"].sum()
    total_prof = s["profit_kes"].sum()
    k1.metric("Total Revenue", f"KES {total_rev:,.0f}")
    k2.metric("Total Profit",  f"KES {total_prof:,.0f}")
    k3.metric("Transactions",  f"{len(s):,}")
    k4.metric("Avg Margin",    f"{total_prof / max(total_rev, 1) * 100:.1f}%")
    k5.metric("Units Sold",    f"{s['quantity'].sum():,.0f}")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        m = s.groupby("month_name")["revenue_kes"].sum().reindex(ALL_MONTHS).dropna()
        fig = px.bar(x=m.index, y=m.values, title="Monthly Revenue (KES)",
                     color=m.values, color_continuous_scale="Greens",
                     labels={"x": "Month", "y": "Revenue"})
        fig.update_layout(coloraxis_showscale=False, height=320)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        cat = s.groupby("category")["revenue_kes"].sum().reset_index()
        fig2 = px.pie(cat, names="category", values="revenue_kes",
                      title="Revenue by Category",
                      color_discrete_sequence=px.colors.sequential.Greens_r)
        fig2.update_layout(height=320)
        st.plotly_chart(fig2, use_container_width=True)
    c3, c4 = st.columns(2)
    with c3:
        mp = s.groupby("month_name")[["revenue_kes", "profit_kes"]].sum().reindex(ALL_MONTHS).dropna()
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Revenue", x=mp.index, y=mp["revenue_kes"], marker_color="#2d6a2d"))
        fig3.add_trace(go.Bar(name="Profit",  x=mp.index, y=mp["profit_kes"],  marker_color="#74c476"))
        fig3.update_layout(barmode="group", title="Revenue vs Profit by Month", height=320)
        st.plotly_chart(fig3, use_container_width=True)
    with c4:
        tp = s.groupby("product_name")["revenue_kes"].sum().nlargest(8).reset_index()
        fig4 = px.bar(tp, x="revenue_kes", y="product_name", orientation="h",
                      title="Top 8 Products by Revenue",
                      color="revenue_kes", color_continuous_scale="Greens")
        fig4.update_layout(coloraxis_showscale=False, height=320, yaxis_title="")
        st.plotly_chart(fig4, use_container_width=True)
    pay = s["payment_method"].value_counts().reset_index()
    pay.columns = ["method", "count"]
    fig5 = px.bar(pay, x="method", y="count", title="Transactions by Payment Method",
                  color="count", color_continuous_scale="Greens")
    fig5.update_layout(coloraxis_showscale=False, height=260)
    st.plotly_chart(fig5, use_container_width=True)
    csv = s.to_csv(index=False).encode("utf-8")
    st.download_button("Download Sales CSV", csv, "greenleaf_sales_2025.csv", "text/csv")

with tab2:
    st.subheader("Inventory Management 2025")
    inv = inventory.copy()
    if sel_months:
        inv = inv[inv["month_name"].isin(sel_months)]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Stock Value",     f"KES {inv['stock_value_kes'].sum():,.0f}")
    k2.metric("Products",        inv["product_id"].nunique())
    k3.metric("Reorder Alerts",  int((inv["needs_reorder"] == "Yes").sum()))
    k4.metric("High Risk Items", int((inv["stockout_risk"] == "High").sum()))
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        r = (inv[inv["needs_reorder"] == "Yes"]
             .groupby("product_name")["closing_stock"].mean()
             .nsmallest(10).reset_index())
        fig = px.bar(r, x="closing_stock", y="product_name", orientation="h",
                     title="Products Needing Reorder",
                     color="closing_stock", color_continuous_scale="Reds_r")
        fig.update_layout(coloraxis_showscale=False, height=340, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        cv = inv.groupby("category")["stock_value_kes"].sum().reset_index()
        fig2 = px.pie(cv, names="category", values="stock_value_kes",
                      title="Stock Value by Category",
                      color_discrete_sequence=px.colors.sequential.Greens_r)
        fig2.update_layout(height=340)
        st.plotly_chart(fig2, use_container_width=True)
    ms = inv.groupby("month_name")["stock_value_kes"].sum().reindex(ALL_MONTHS).dropna()
    fig3 = px.line(x=ms.index, y=ms.values, title="Monthly Stock Value Trend",
                   markers=True, labels={"x": "Month", "y": "Stock Value (KES)"})
    fig3.update_traces(line_color="#2d6a2d", line_width=2.5)
    fig3.update_layout(height=280)
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.subheader("Customer Orders 2025")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Orders",  f"{len(o):,}")
    k2.metric("Total Value",   f"KES {o['order_total_kes'].sum():,.0f}")
    k3.metric("Delivery Rate", f"{o['is_delivered'].mean() * 100:.1f}%")
    k4.metric("Avg Delivery",  f"{o['delivery_days'].mean():.1f} days")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        mo = o.groupby("month_name")["order_total_kes"].sum().reindex(ALL_MONTHS).dropna()
        fig = px.bar(x=mo.index, y=mo.values, title="Monthly Order Value (KES)",
                     color=mo.values, color_continuous_scale="Blues")
        fig.update_layout(coloraxis_showscale=False, height=320)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        co = o.groupby("county")["order_total_kes"].sum().nlargest(8).reset_index()
        fig2 = px.bar(co, x="order_total_kes", y="county", orientation="h",
                      title="Top Counties by Order Value",
                      color="order_total_kes", color_continuous_scale="Blues")
        fig2.update_layout(coloraxis_showscale=False, height=320, yaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)
    sc = o["status"].value_counts().reset_index()
    sc.columns = ["status", "count"]
    fig3 = px.pie(sc, names="status", values="count", title="Order Status Breakdown",
                  color_discrete_map={"Delivered": "#2d6a2d", "Pending": "#f9a825", "Cancelled": "#c62828"})
    fig3.update_layout(height=280)
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    st.subheader("Supplier Spend 2025")
    sup = suppliers.copy()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Spend",     f"KES {sup['amount_kes'].sum():,.0f}")
    k2.metric("Suppliers",       sup["supplier_id"].nunique())
    k3.metric("Purchase Orders", len(sup))
    k4.metric("Paid Orders",     f"{sup['is_paid'].mean() * 100:.1f}%")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        ss = (sup.groupby("supplier_name")["amount_kes"].sum()
              .reset_index().sort_values("amount_kes", ascending=False))
        fig = px.bar(ss, x="amount_kes", y="supplier_name", orientation="h",
                     title="Spend by Supplier (KES)",
                     color="amount_kes", color_continuous_scale="Greens")
        fig.update_layout(coloraxis_showscale=False, height=320, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        cs = sup.groupby("category")["amount_kes"].sum().reset_index()
        fig2 = px.pie(cs, names="category", values="amount_kes",
                      title="Spend by Category",
                      color_discrete_sequence=px.colors.sequential.Greens_r)
        fig2.update_layout(height=320)
        st.plotly_chart(fig2, use_container_width=True)
    ms2 = sup.groupby("month_name")["amount_kes"].sum().reindex(ALL_MONTHS).dropna()
    fig3 = px.line(x=ms2.index, y=ms2.values, title="Monthly Supplier Spend (KES)",
                   markers=True, labels={"x": "Month", "y": "Amount (KES)"})
    fig3.update_traces(line_color="#2d6a2d", line_width=2.5)
    fig3.update_layout(height=280)
    st.plotly_chart(fig3, use_container_width=True)