import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Amazon Hardware POS", page_icon="🔧", layout="wide")

STOCK_FILE = "stock.csv"
SALES_FILE = "sales.csv"

def load_stock():
    if os.path.exists(STOCK_FILE):
        return pd.read_csv(STOCK_FILE)
    else:
        return pd.DataFrame(columns=["Product", "Category", "Qty_Left", "BP", "SP", "Date_Added"])

def load_sales():
    if os.path.exists(SALES_FILE):
        return pd.read_csv(SALES_FILE)
    else:
        return pd.DataFrame(columns=["Date", "Product", "Qty_Sold", "BP", "SP", "Profit", "Total_Sale"])

stock_df = load_stock()
sales_df = load_sales()

st.title("🔧 AMAZON HARDWARE - Stock & Profit System")
st.caption("Mombasa | Phone POS - Bargain Allowed")

menu = st.sidebar.selectbox("MENU", ["Dashboard", "Add New Stock (IN)", "Sell Product (OUT)", "View Stock", "Sales History & Profit"])

if menu == "Dashboard":
    st.subheader("📊 Today Business")
    total_stock_value = (stock_df["Qty_Left"] * stock_df["BP"]).sum() if not stock_df.empty else 0
    total_profit = sales_df["Profit"].sum() if not sales_df.empty else 0
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_profit = sales_df[sales_df["Date"].astype(str).str.contains(today_str)]["Profit"].sum() if not sales_df.empty else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Stock Value (BP)", f"Ksh {total_stock_value:,.0f}")
    col2.metric("Total Profit", f"Ksh {total_profit:,.0f}")
    col3.metric("Today Profit", f"Ksh {today_profit:,.0f}")
    st.divider()
    st.write("⚠️ Low Stock Alert (Less than 10)")
    if not stock_df.empty:
        low = stock_df[stock_df["Qty_Left"] < 10]
        st.dataframe(low, use_container_width=True)

elif menu == "Add New Stock (IN)":
    st.subheader("➕ Record Stock Entering Shop")
    with st.form("add_stock"):
        product = st.text_input("Product Name e.g Cement, Nails 2inch")
        category = st.selectbox("Category", ["Cement", "Nails", "Paint", "Pipes", "Timber", "Tools", "Electrical", "Other"])
        qty = st.number_input("Quantity Entered", min_value=1, step=1)
        bp = st.number_input("Buying Price (BP)", min_value=1.0)
        sp = st.number_input("Normal Selling Price (SP)", min_value=1.0)
        date_added = st.date_input("Date Entered", datetime.now())
        submitted = st.form_submit_button("SAVE TO STOCK")
        if submitted:
            if product in stock_df["Product"].values:
                idx = stock_df[stock_df["Product"] == product].index[0]
                stock_df.loc[idx, "Qty_Left"] += qty
                stock_df.loc[idx, "BP"] = bp
                stock_df.loc[idx, "SP"] = sp
            else:
                new_row = pd.DataFrame([[product, category, qty, bp, sp, date_added]], columns=stock_df.columns)
                stock_df = pd.concat([stock_df, new_row], ignore_index=True)
            stock_df.to_csv(STOCK_FILE, index=False)
            st.success(f"✅ {product} - {qty} added!")
            st.balloons()

elif menu == "Sell Product (OUT)":
    st.subheader("💰 Sell - ADJUST PRICE IF BARGAIN")
    if stock_df.empty:
        st.warning("No stock to sell. Add stock first.")
    else:
        product_list = stock_df["Product"].tolist()
        selected_product = st.selectbox("Select Product", product_list)
        row = stock_df[stock_df["Product"] == selected_product].iloc[0]
        st.info(f"In Stock: {row['Qty_Left']} | BP: Ksh {row['BP']} | Normal SP: Ksh {row['SP']}")

        with st.form("sell"):
            qty_sold = st.number_input("Quantity Customer Buying", min_value=1, max_value=int(row['Qty_Left']), step=1)
            actual_sp = st.number_input("ACTUAL Selling Price (change if customer bargained)", value=float(row['SP']), min_value=1.0)
            sale_date = st.date_input("Sale Date", datetime.now())
            sell_btn = st.form_submit_button("SELL NOW & CALCULATE PROFIT")

            if sell_btn:
                profit_per_item = actual_sp - row["BP"]
                total_profit = profit_per_item * qty_sold
                total_sale = actual_sp * qty_sold

                idx = stock_df[stock_df["Product"] == selected_product].index[0]
                stock_df.loc[idx, "Qty_Left"] -= qty_sold
                stock_df.to_csv(STOCK_FILE, index=False)

                new_sale = pd.DataFrame([[str(sale_date), selected_product, qty_sold, row["BP"], actual_sp, total_profit, total_sale]], columns=sales_df.columns)
                sales_df = pd.concat([sales_df, new_sale], ignore_index=True)
                sales_df.to_csv(SALES_FILE, index=False)

                if total_profit < 0:
                    st.warning(f"⚠️ LOSS! You sold at loss: Ksh {total_profit:,.0f}")
                else:
                    st.success(f"✅ SOLD! Profit: Ksh {total_profit:,.0f} | Total Sale: Ksh {total_sale:,.0f}")
                st.info(f"Stock Left: {stock_df.loc[idx, 'Qty_Left']}")

elif menu == "View Stock":
    st.subheader("📦 Current Stock")
    st.dataframe(stock_df, use_container_width=True) if not stock_df.empty else st.info("No stock")

elif menu == "Sales History & Profit":
    st.subheader("🧾 Sales History - Accurate with Date & Bargain Price")
    if sales_df.empty:
        st.info("No sales yet.")
    else:
        st.dataframe(sales_df.sort_values("Date", ascending=False), use_container_width=True)
        st.metric("TOTAL PROFIT MADE", f"Ksh {sales_df['Profit'].sum():,.0f}")
