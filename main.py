import streamlit as st
from tracker.trade_manager_google_sheets import TradeManager

st.set_page_config(page_title="Paper Trading Dashboard", layout="wide")
st.title("📈 Paper Trading Dashboard")

# --------------------- User Login Section ---------------------
username = st.text_input("Enter Your Username", key="username_input")

if not username:
    st.warning("Please enter your username to use the app.")
    st.stop()

tm = TradeManager(sheet_name="Paper_Trades", user=username)

# --------------------- Trade Entry Section with Auto-Clear ---------------------
st.subheader("New Trade Entry")

with st.form("trade_entry_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        underlying = st.selectbox("Underlying", ["NIFTY", "BANKNIFTY", "FINNIFTY", "OTHER"], key="underlying_select")
    with col2:
        strike_price = st.number_input("Strike Price", min_value=0, key="strike_price_input")
    with col3:
        option_type = st.radio("Option Type", ["CE", "PE"], horizontal=True, key="option_type_radio")
    with col4:
        entry_price = st.number_input("Entry Price", min_value=0.0, format="%.2f", key="entry_price_input")

    manual_lot_size = 1
    company_name = ""
    if underlying == "OTHER":
        company_name = st.text_input("Enter Company Name", key="company_name_input")
        manual_lot_size = st.number_input("Enter Lot Size for OTHER", min_value=1, step=1, key="manual_lot_size_input")

    number_of_lots = st.number_input("Number of Lots", min_value=1, step=1, value=1, key="number_of_lots_input")

    submitted = st.form_submit_button("📥 Add Trade")
    if submitted:
        if strike_price == 0 or entry_price == 0.0:
            st.error("❗ Please enter a valid Strike Price and Entry Price (both must be greater than 0)")
        elif underlying == "OTHER" and not company_name:
            st.error("❗ Please enter a Company Name for OTHER underlying")
        else:
            tm.add_trade(underlying, strike_price, option_type, entry_price, manual_lot_size, company_name, number_of_lots)
            st.success("✅ Trade Added Successfully!")

# --------------------- Open Trades Section ---------------------
st.subheader("📝 Open Trades")
open_trades = tm.get_open_trades()

if open_trades.empty:
    st.info("No open trades")
else:
    open_trades = open_trades.set_index('ID')
    for id, row in open_trades.iterrows():
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
        col1.write(id)
        col2.write(row['Underlying'])
        col3.write(row['Strike Price'])
        col4.write(row['Option Type'])
        col5.write(f"₹{row['Entry Price']}")
        col6.write(f"Lot Size: {row['Lot Size']}")
        col7.write(f"No. of Lots: {row['Number of Lots']}")
        col8.write(f"Investment: ₹{row['Investment']}")

        with st.form(key=f"exit_form_{id}"):
            exit_price_input = st.number_input("Exit Price", min_value=0.0, format="%.2f", key=f"exit_price_input_{id}")
            exit_button = st.form_submit_button("Exit")
            if exit_button:
                tm.exit_trade(id, exit_price_input)
                st.success(f"Trade {id} exited successfully!")
                st.rerun()

# --------------------- Closed Trades Section ---------------------
st.subheader("📄 Closed Trades")
closed_trades = tm.get_closed_trades()

if not closed_trades.empty:
    st.dataframe(closed_trades[['Underlying', 'Strike Price', 'Option Type', 'Entry Price',
                                 'Exit Price', 'PnL', 'Entry Time', 'Exit Time',
                                 'Company Name', 'Lot Size', 'Number of Lots', 'Investment']])

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
