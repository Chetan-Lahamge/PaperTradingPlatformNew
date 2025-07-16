import gspread
import pandas as pd
from datetime import datetime
import streamlit as st  # To access st.secrets

class TradeManager:
    def __init__(self, sheet_name="Paper_Trades"):
        self.gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        self.sheet = self.gc.open(sheet_name)
        self.worksheet = self.sheet.worksheet("Trades")
        self._setup_sheet()

    def _setup_sheet(self):
        if not self.worksheet.row_values(1):
            headers = ["ID", "Underlying", "Strike Price", "Option Type",
                       "Entry Price", "Entry Time", "Exit Price", "Exit Time",
                       "Status", "PnL", "Company Name", "Lot Size", "Investment"]
            self.worksheet.append_row(headers)

    def _get_next_id(self):
        records = self.worksheet.get_all_records()
        if not records:
            return 1
        else:
            return records[-1]['ID'] + 1

    def _get_default_lot_size(self, underlying):
        lot_sizes = {
            'NIFTY': 75,
            'BANKNIFTY': 35,
            'FINNIFTY': 65
        }
        return lot_sizes.get(underlying.upper(), 1)

    def add_trade(self, underlying, strike_price, option_type, entry_price, lot_size, company_name):
        new_id = self._get_next_id()
        entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if underlying != "OTHER":
            company_name = ""
            lot_size = self._get_default_lot_size(underlying)
        investment = entry_price * lot_size
        row = [new_id, underlying, strike_price, option_type,
               entry_price, entry_time, "", "", "OPEN", "", company_name, lot_size, investment]
        self.worksheet.append_row(row)

    def exit_trade(self, trade_id, exit_price):
        records = self.worksheet.get_all_records()
        for idx, record in enumerate(records):
            if record['ID'] == trade_id and record['Status'] == "OPEN":
                exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry_price = float(record['Entry Price'])
                lot_size = int(record.get('Lot Size', 1))
                pnl = (exit_price - entry_price) * lot_size
                self.worksheet.update_cell(idx + 2, 7, exit_price)  # Exit Price
                self.worksheet.update_cell(idx + 2, 8, exit_time)   # Exit Time
                self.worksheet.update_cell(idx + 2, 9, "CLOSED")    # Status
                self.worksheet.update_cell(idx + 2, 10, pnl)        # PnL
                break

    def get_open_trades(self):
        df = pd.DataFrame(self.worksheet.get_all_records())
        return df[df['Status'] == 'OPEN'] if not df.empty else pd.DataFrame()

    def get_closed_trades(self):
        df = pd.DataFrame(self.worksheet.get_all_records())
        return df[df['Status'] == 'CLOSED'] if not df.empty else pd.DataFrame()

    def get_summary(self):
        df = self.get_closed_trades()
        if df.empty:
            return {'total_pnl': 0, 'win_rate': 0, 'avg_pnl': 0, 'total_trades': 0}
        total_pnl = df['PnL'].sum()
        win_rate = (len(df[df['PnL'] > 0]) / len(df)) * 100
        avg_pnl = df['PnL'].mean()
        total_trades = len(df)
        return {'total_pnl': total_pnl, 'win_rate': win_rate, 'avg_pnl': avg_pnl, 'total_trades': total_trades}

    def get_cumulative_pnl_chart(self):
        df = self.get_closed_trades()
        if df.empty:
            return pd.DataFrame()
        df = df.sort_values('Exit Time')
        df['cumulative_pnl'] = df['PnL'].cumsum()
        return df[['Exit Time', 'cumulative_pnl']]