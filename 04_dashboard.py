@'
import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import psycopg
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Greenleaf Supply Analytics", page_icon="🌿", layout="wide")
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
        st.error("No DATABASE_URL set.")
        st.stop()
    def read(q):
        with psycopg.connect(db_url) as conn:
            return pd.read_sql(q, conn)
    sales     = read("SELECT * FROM gl_sales")
    inventory = read("SELECT * FROM gl_inventory")
    orders    = read("SELECT * FROM gl_orders")
    suppliers = read("SELECT * FROM gl_suppliers")
    sales["revenue_kes"]     = pd.to_numeric(sales["revenue_kes"],     errors="coerce")
    sales["profit_kes"]      = pd.to_numeric(sales["profit_kes"],      errors="coerce")
    sales["quantity"]        = pd.to_numeric(sales["quantity"],        errors="coerce")
    orders["order_total_kes"]= pd.to_numeric(orders["order_total_kes"],errors="coerce")
    orders["is_delivered"]   = pd.to_numeric(orders["is_delivered"],   errors="coerce")
    orders["delivery_days"]  = pd.to_numeric(orders["delivery_days"],  errors="coerce")
    suppliers["amount_kes"]  = pd.to_numeric(suppliers["amount_kes"],  errors="coerce")
    suppliers["is_paid"]     = pd.to_numeric(suppliers["is_paid"],     errors="coerce")
    inventory["stock_value_kes"] = pd.to_numeric(inventory["stock_value_kes"], errors="coerce")
    inventory["closing_stock"]   = pd.to_numeric(inventory["closing_stock"],   errors="coerce")
    inventory["reorder_level"]   = pd.to_numeric(inventory["reorder_level"],   errors="coerce")
    return sales, inventory, orders, suppliers

sales, inventory, orders, suppliers = load_all()

all_months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
st.sidebar.header("Filters")
sel_months = st.sidebar.multiselect("Month", all_months)
sel_cat    = st.sidebar.multiselect("Category", sorted(sales["category"].dropna().unique()))
s = sales.copy()
if sel_months: s = s[s["month_name"].isin(sel_months)]
if sel_cat:    s = s[s["category"].isin(sel_cat)]
o = orders.copy()
if sel_months: o = o[o["month_name"].isin(sel_months)]

tab1,tab2,tab3,tab4 = st.tabs(["Sales","Inventory","Orders","Suppliers"])

with tab1:
    st.subheader("Sales Performance 2025")
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Total Revenue", f"KES {s['revenue_kes'].sum():,.0f}")
    k2.metric("Total Profit",  f"KES {s['profit_kes'].sum():,.0f}")
    k3.metric("Transactions",  f"{len(s):,}")
    k4.metric("Avg Margin",    f"{s['profit_kes'].sum()/max(s['revenue_kes'].sum(),1)*100:.1f}%")
    k5.metric("Units Sold",    f"{s['quantity'].sum():,.0f}")
    c1,c2 = st.columns(2)
    with c1:
        m = s.groupby("month_name")["revenue_kes"].sum().reindex(all_months).dropna()
        st.plotly_chart(px.bar(x=m.index,y=m.values,title="Monthly Revenue (KES)",color=m.values,color_continuous_scale="Greens").update_layout(coloraxis_showscale=False,height=320), use_container_width=True)
    with c2:
        st.plotly_chart(px.pie(s.groupby("category")["revenue_kes"].sum().reset_index(),names="category",values="revenue_kes",title="Revenue by Category",color_discrete_sequence=px.colors.sequential.Greens_r).update_layout(height=320), use_container_width=True)
    c3,c4 = st.columns(2)
    with c3:
        mp = s.groupby("month_name")[["revenue_kes","profit_kes"]].sum().reindex(all_months).dropna()
        fig=go.Figure()
        fig.add_trace(go.Bar(name="Revenue",x=mp.index,y=mp["revenue_kes"],marker_color="#2d6a2d"))
        fig.add_trace(go.Bar(name="Profit", x=mp.index,y=mp["profit_kes"], marker_color="#74c476"))
        fig.update_layout(barmode="group",title="Revenue vs Profit",height=320)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        tp = s.groupby("product_name")["revenue_kes"].sum().nlargest(8).reset_index()
        st.plotly_chart(px.bar(tp,x="revenue_kes",y="product_name",orientation="h",title="Top 8 Products",color="revenue_kes",color_continuous_scale="Greens").update_layout(coloraxis_showscale=False,height=320,yaxis_title=""), use_container_width=True)

with tab2:
    st.subheader("Inventory Management 2025")
    inv = inventory.copy()
    if sel_months: inv = inv[inv["month_name"].isin(sel_months)]
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Stock Value",    f"KES {inv['stock_value_kes'].sum():,.0f}")
    k2.metric("Products",       inv["product_id"].nunique())
    k3.metric("Reorder Alerts", (inv["needs_reorder"]=="Yes").sum())
    k4.metric("High Risk",      (inv["stockout_risk"]=="High").sum())
    c1,c2 = st.columns(2)
    with c1:
        r = inv[inv["needs_reorder"]=="Yes"].groupby("product_name")["closing_stock"].mean().nsmallest(10).reset_index()
        st.plotly_chart(px.bar(r,x="closing_stock",y="product_name",orientation="h",title="Reorder Needed",color="closing_stock",color_continuous_scale="Reds_r").update_layout(coloraxis_showscale=False,height=340,yaxis_title=""), use_container_width=True)
    with c2:
        st.plotly_chart(px.pie(inv.groupby("category")["stock_value_kes"].sum().reset_index(),names="category",values="stock_value_kes",title="Stock Value by Category",color_discrete_sequence=px.colors.sequential.Greens_r).update_layout(height=340), use_container_width=True)

with tab3:
    st.subheader("Customer Orders 2025")
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Total Orders",   f"{len(o):,}")
    k2.metric("Total Value",    f"KES {o['order_total_kes'].sum():,.0f}")
    k3.metric("Delivery Rate",  f"{o['is_delivered'].mean()*100:.1f}%")
    k4.metric("Avg Delivery",   f"{o['delivery_days'].mean():.1f} days")
    c1,c2 = st.columns(2)
    with c1:
        mo = o.groupby("month_name")["order_total_kes"].sum().reindex(all_months).dropna()
        st.plotly_chart(px.bar(x=mo.index,y=mo.values,title="Monthly Order Value",color=mo.values,color_continuous_scale="Blues").update_layout(coloraxis_showscale=False,height=320), use_container_width=True)
    with c2:
        co = o.groupby("county")["order_total_kes"].sum().nlargest(8).reset_index()
        st.plotly_chart(px.bar(co,x="order_total_kes",y="county",orientation="h",title="Top Counties",color="order_total_kes",color_continuous_scale="Blues").update_layout(coloraxis_showscale=False,height=320,yaxis_title=""), use_container_width=True)
    sc = o["status"].value_counts().reset_index()
    sc.columns=["status","count"]
    st.plotly_chart(px.pie(sc,names="status",values="count",title="Order Status",color_discrete_map={"Delivered":"#2d6a2d","Pending":"#f9a825","Cancelled":"#c62828"}).update_layout(height=280), use_container_width=True)

with tab4:
    st.subheader("Supplier Spend 2025")
    sup = suppliers.copy()
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Total Spend",     f"KES {sup['amount_kes'].sum():,.0f}")
    k2.metric("Suppliers",       sup["supplier_id"].nunique())
    k3.metric("Purchase Orders", len(sup))
    k4.metric("Paid Orders",     f"{sup['is_paid'].mean()*100:.1f}%")
    c1,c2 = st.columns(2)
    with c1:
        ss = sup.groupby("supplier_name")["amount_kes"].sum().reset_index().sort_values("amount_kes",ascending=False)
        st.plotly_chart(px.bar(ss,x="amount_kes",y="supplier_name",orientation="h",title="Spend by Supplier",color="amount_kes",color_continuous_scale="Greens").update_layout(coloraxis_showscale=False,height=320,yaxis_title=""), use_container_width=True)
    with c2:
        st.plotly_chart(px.pie(sup.groupby("category")["amount_kes"].sum().reset_index(),names="category",values="amount_kes",title="Spend by Category",color_discrete_sequence=px.colors.sequential.Greens_r).update_layout(height=320), use_container_width=True)
'@ | Set-Content "04_dashboard.py"
