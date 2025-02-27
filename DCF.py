import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf

def dcf_valuation(cash_flows, discount_rate, terminal_growth, years=5):
    discount_factors = [(1 / (1 + discount_rate)) ** i for i in range(1, years + 1)]
    present_values = [cf * df for cf, df in zip(cash_flows, discount_factors)]
    terminal_value = (cash_flows[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
    terminal_value_pv = terminal_value * discount_factors[-1]
    
    total_value = sum(present_values) + terminal_value_pv
    return total_value

# Streamlit UI
st.title("DCF Valuation Dashboard")

# Inputs
st.sidebar.header("Financial Inputs")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL)", value="AAPL")

# Fetch data from Yahoo Finance
data = yf.Ticker(ticker)
cash_flow_data = data.cashflow
initial_cash_flow = cash_flow_data.iloc[0, 0] if not cash_flow_data.empty else 100.0

growth_rate = st.sidebar.number_input("Annual Growth Rate (%)", value=5.0, step=0.5) / 100
discount_rate = st.sidebar.number_input("Discount Rate (%)", value=10.0, step=0.5) / 100
terminal_growth = st.sidebar.number_input("Terminal Growth Rate (%)", value=2.0, step=0.5) / 100
years = st.sidebar.slider("Projection Years", min_value=3, max_value=10, value=5)

# Generate future cash flows
cash_flows = [initial_cash_flow * (1 + growth_rate) ** i for i in range(1, years + 1)]
total_value = dcf_valuation(cash_flows, discount_rate, terminal_growth, years)

st.subheader("Valuation Results")
st.write(f"**Intrinsic Value (Total Enterprise Value):** ${total_value:.2f} million")

# Data Visualization
st.subheader("Projected Cash Flows")
df = pd.DataFrame({"Year": list(range(1, years + 1)), "Cash Flow": cash_flows})
st.line_chart(df.set_index("Year"))

st.write("**Formula Used:** DCF = Sum(PV of future cash flows) + PV of terminal value")
