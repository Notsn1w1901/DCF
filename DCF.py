import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf

def dcf_valuation(cash_flows, discount_rate, terminal_growth, years=5):
    if discount_rate <= terminal_growth:
        st.error("Discount rate must be greater than the terminal growth rate to avoid division errors.")
        return None

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
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL)", value="AAPL").upper()

# Fetch data from Yahoo Finance
try:
    data = yf.Ticker(ticker)
    cash_flow_data = data.cashflow

    # Ensure cash flow data is not empty before extracting FCF
    if not cash_flow_data.empty:
        available_rows = cash_flow_data.index.astype(str).tolist()  # Convert index to string for safety
        fcf_row = next((row for row in available_rows if "Operating" in row or "Cash" in row), None)
        
        if fcf_row:
            initial_cash_flow = cash_flow_data.loc[fcf_row].values[0]  # Take the latest available value
        else:
            initial_cash_flow = 100.0  # Fallback default

    else:
        initial_cash_flow = 100.0  # Default if data isn't available

    # Get stock price & market cap
    stock_price = data.history(period="1d")["Close"].iloc[-1] if "Close" in data.history(period="1d") else None
    market_cap = data.info.get("marketCap", "N/A")

except Exception as e:
    st.error(f"Error fetching data for {ticker}: {e}")
    initial_cash_flow = 100.0
    stock_price, market_cap = None, "N/A"

growth_rate = st.sidebar.number_input("Annual Growth Rate (%)", value=5.0, step=0.5) / 100
discount_rate = st.sidebar.number_input("Discount Rate (%)", value=10.0, step=0.5) / 100
terminal_growth = st.sidebar.number_input("Terminal Growth Rate (%)", value=2.0, step=0.5) / 100
years = st.sidebar.slider("Projection Years", min_value=3, max_value=10, value=5)

# Generate future cash flows
cash_flows = [initial_cash_flow * (1 + growth_rate) ** i for i in range(1, years + 1)]
total_value = dcf_valuation(cash_flows, discount_rate, terminal_growth, years)

st.subheader("Valuation Results")
if total_value:
    st.write(f"**Intrinsic Value (Total Enterprise Value):** ${total_value:,.2f} million")

    if market_cap != "N/A" and stock_price is not None:
        st.write(f"**Market Cap:** ${market_cap:,.2f}")
        st.write(f"**Current Stock Price:** ${stock_price:,.2f}")

        fair_value_per_share = total_value / (market_cap / stock_price)
        st.write(f"**Fair Value per Share (DCF Estimate):** ${fair_value_per_share:,.2f}")

# Data Visualization
st.subheader("Projected Cash Flows")
df = pd.DataFrame({"Year": list(range(1, years + 1)), "Cash Flow": cash_flows})
st.line_chart(df.set_index("Year"))

st.write("**Formula Used:** DCF = Sum(PV of future cash flows) + PV of terminal value")
