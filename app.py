import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Amazon Hardware POS", page_icon="🔧", layout="wide")

# Files to save data
STOCK_FILE = "stock.csv"
SALES_FILE = "sales.csv"

# Load or create stock
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
st.caption("Mombasa | Phone POS System")

menu = st.sidebar.selectbox("MENU", ["Dashboard", "Add New Stock (IN)", "Sell Product (OUT)", "View Stock", "Sales History & Profit"])

if menu == "Dashboard":
    st.subheader("📊 Today Business")
    total_stock_value = (stock_df["Qty_Left"] * stock_df["BP"]).sum() if not stock_df.empty else 0
    total_profit = sales_df["Profit"].sum() if not sales_df.empty else 0

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_profit = sales_df[sales_df["Date"].astype(str).str.contains(today_str)]["Profit"].sum() if not sales_df.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Stock Value (BP)", f"Ksh {total_stock_value:,.0f}")
    col2.metric("Total Profit (All Time)", f"Ksh {total_profit:,.0f}")
    col3.metric("Today's Profit", f"Ksh {today_profit:,.0f}")

    st.divider()
    st.write("⚠️ Low Stock Alert (Less than 10)")
    if not stock_df.empty:
        low = stock_df[stock_df["Qty_Left"] < 10]
        st.dataframe(low, use_container_width=True)
    else:
        st.info("No stock yet. Go to Add New Stock.")

elif menu == "Add New Stock (IN)":
    st.subheader("➕ Record Stock Entering Shop")
    with st.form("add_stock"):
        product = st.text_input("Product Name e.g Cement, Nails 2inch, Paint White")
        category = st.selectbox("Category", ["Cement", "Nails", "Paint", "Pipes", "Timber", "Tools", "Electrical", "Other"])
        qty = st.number_input("Quantity Entered", min_value=1, step=1)
        bp = st.number_input("Buying Price (BP) per item", min_value=1.0)
        sp = st.number_input("Selling Price (SP) per item", min_value=1.0)
        date_added = st.date_input("Date Entered", datetime.now())
        submitted = st.form_submit_button("SAVE TO STOCK")

        if submitted:
            if product == "":
                st.error("Enter product name")
            else:
                # If product exists, update qty
                if product in stock_df["Product"].values:
                    idx = stock_df[stock_df["Product"] == product].index[0]
                    stock_df.loc[idx, "Qty_Left"] += qty
                    stock_df.loc[idx, "BP"] = bp
                    stock_df.loc[idx, "SP"] = sp
                else:
                    new_row = pd.DataFrame([[product, category, qty, bp, sp, date_added]], columns=stock_df.columns)
                    stock_df = pd.concat([stock_df, new_row], ignore_index=True)
                stock_df.to_csv(STOCK_FILE, index=False)
                st.success(f"✅ {product} - {qty} added! Stock saved.")
                st.balloons()

elif menu == "Sell Product (OUT)":
    st.subheader("💰 Make a Sale - It will deduct automatically")
    if stock_df.empty:
        st.warning("No stock to sell. Add stock first.")
    else:
        with st.form("sell"):
            product_list = stock_df["Product"].tolist()
            selected_product = st.selectbox("Select Product Customer is Buying", product_list)
            qty_sold = st.number_input("Quantity Customer Buying", min_value=1, step=1)
            sale_date = st.date_input("Sale Date", datetime.now())
            sell_btn = st.form_submit_button("SELL NOW & CALCULATE PROFIT")

            if sell_btn:
                row = stock_df[stock_df["Product"] == selected_product].iloc[0]
                if qty_sold > row["Qty_Left"]:
                    st.error(f"❌ Not enough stock! Only {row['Qty_Left']} left.")
                else:
                    profit_per_item = row["SP"] - row["BP"]
                    total_profit = profit_per_item * qty_sold
                    total_sale = row["SP"] * qty_sold

                    # Deduct from stock
                    idx = stock_df[stock_df["Product"] == selected_product].index[0]
                    stock_df.loc[idx, "Qty_Left"] -= qty_sold
                    stock_df.to_csv(STOCK_FILE, index=False)

                    # Add to sales
                    new_sale = pd.DataFrame([[str(sale_date), selected_product, qty_sold, row["BP"], row["SP"], total_profit, total_sale]], columns=sales_df.columns)
                    sales_df = pd.concat([sales_df, new_sale], ignore_index=True)
                    sales_df.to_csv(SALES_FILE, index=False)

                    st.success(f"✅ SOLD! Profit: Ksh {total_profit:,.0f} | Sale: Ksh {total_sale:,.0f}")
                    st.info(f"Stock Left for {selected_product}: {stock_df.loc[idx, 'Qty_Left']}")

elif menu == "View Stock":
    st.subheader("📦 Current Stock Table")
    if stock_df.empty:
        st.info("No stock recorded yet.")
    else:
        st.dataframe(stock_df, use_container_width=True)
        csv = stock_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Stock as Excel CSV", csv, "amazon_stock.csv", "text/csv")

elif menu == "Sales History & Profit":
    st.subheader("🧾 Sales History with Profit & Date")
    if sales_df.empty:
        st.info("No sales yet.")
    else:
        st.dataframe(sales_df.sort_values("Date", ascending=False), use_container_width=True)
        total_p = sales_df["Profit"].sum()
        st.metric("TOTAL PROFIT MADE", f"Ksh {total_p:,.0f}")
        csv2 = sales_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Sales Report", csv2, "amazon_sales.csv", "text/csv")