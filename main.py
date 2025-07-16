import streamlit as st
from tracker.trade_manager_google_sheets import TradeManager
from datetime import datetime, timedelta
import pandas as pd

tm = TradeManager(sheet_name="Paper_Trades")

st.set_page_config(page_title="Paper Trading Dashboard", layout="wide")
st.title("📈 AI Paper Trading Dashboard")

# --------------------- Trade Entry Section ---------------------
st.subheader("New Trade Entry")
col1, col2, col3, col4 = st.columns(4)
with col1:
    underlying = st.selectbox("Underlying", ["NIFTY", "BANKNIFTY", "FINNIFTY", "OTHER"])
with col2:
    strike_price = st.number_input("Strike Price", min_value=0)
with col3:
    option_type = st.radio("Option Type", ["CE", "PE"], horizontal=True)
with col4:
    entry_price = st.number_input("Entry Price", min_value=0.0, format="%.2f")

if st.button("📥 Add Trade"):
    if strike_price == 0 or entry_price == 0.0:
        st.error("❗ Please enter a valid Strike Price and Entry Price (both must be greater than 0)")
    else:
        tm.add_trade(underlying, strike_price, option_type, entry_price)
        st.success("✅ Trade Added Successfully!")

# --------------------- Open Trades Section ---------------------
st.subheader("📝 Open Trades")
open_trades = tm.get_open_trades()

if open_trades.empty:
    st.info("No open trades")
else:
    open_trades = open_trades.set_index('ID')
    for id, row in open_trades.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.write(id)
        col2.write(row['Underlying'])
        col3.write(row['Strike Price'])
        col4.write(row['Option Type'])
        col5.write(f"₹{row['Entry Price']}")

        with col6.form(key=f"exit_form_{id}"):
            exit_price_input = st.number_input("Exit Price", min_value=0.0, format="%.2f", key=f"exit_price_input_{id}")
            exit_button = st.form_submit_button("Exit")
            if exit_button:
                tm.exit_trade(id, exit_price_input)
                st.success(f"Trade {id} exited successfully!")
                st.experimental_rerun()

# --------------------- Closed Trades Section ---------------------
st.subheader("📄 Closed Trades")
closed_trades = tm.get_closed_trades()

if not closed_trades.empty:
    st.dataframe(closed_trades[['Underlying', 'Strike Price', 'Option Type', 'Entry Price', 'Exit Price', 'PnL', 'Entry Time', 'Exit Time']])

# --------------------- Performance Summary ---------------------
st.subheader("📊 Performance Summary")

summary = tm.get_summary()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total P&L", f"₹{summary['total_pnl']:.2f}")
col2.metric("Win Rate %", f"{summary['win_rate']:.2f}%")
col3.metric("Average P&L/Trade", f"₹{summary['avg_pnl']:.2f}")
col4.metric("Total Trades", f"{summary['total_trades']}")

# --------------------- Cumulative P&L Chart ---------------------
st.subheader("📈 Cumulative P&L Chart")
cum_pnl_df = tm.get_cumulative_pnl_chart()
if not cum_pnl_df.empty:
    st.line_chart(cum_pnl_df.set_index('Exit Time')['cumulative_pnl'])
else:
    st.info("No closed trades to show P&L chart.")