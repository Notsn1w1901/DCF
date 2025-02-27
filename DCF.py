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
    return total_value if total_value > 0 else None  # Ensure a valid output

# Streamlit UI
st.title("DCF Valuation Dashboard")

# Inputs
st.sidebar.header("Financial Inputs")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL or BBRI.JK)", value="AAPL").upper()

# Determine currency based on ticker suffix
is_indonesian_stock = ticker.endswith(".JK")
currency_symbol = "Rp." if is_indonesian_stock else "$"

# Fetch exchange rate (for IDR conversion)
try:
    exchange_rate = yf.Ticker("USDIDR=X").history(period="1d")["Close"].iloc[-1] if is_indonesian_stock else 1
except:
    exchange_rate = None

# Fetch data from Yahoo Finance
try:
    data = yf.Ticker(ticker)
    cash_flow_data = data.cashflow

    # Extracting Free Cash Flow (FCF) safely
    if not cash_flow_data.empty:
        available_rows = cash_flow_data.index.astype(str).tolist()
        fcf_row = next((row for row in available_rows if "Operating" in row or "Cash" in row), None)

        if fcf_row:
            initial_cash_flow = cash_flow_data.loc[fcf_row].values[0]
        else:
            initial_cash_flow = 100.0  # Default fallback
    else:
        initial_cash_flow = 100.0  # Default if data is missing

    # Get stock price & market cap safely
    stock_history = data.history(period="1d")
    stock_price = stock_history["Close"].iloc[-1] if "Close" in stock_history and not stock_history.empty else None
    market_cap = data.info.get("marketCap", None)

except Exception as e:
    st.error(f"Error fetching data for {ticker}: {e}")
    initial_cash_flow = 100.0
    stock_price, market_cap = None, None

# User Inputs for Growth Rates & Discounting
growth_rate = st.sidebar.number_input("Annual Growth Rate (%)", value=5.0, step=0.5) / 100
discount_rate = st.sidebar.number_input("Discount Rate (%)", value=10.0, step=0.5) / 100
terminal_growth = st.sidebar.number_input("Terminal Growth Rate (%)", value=2.0, step=0.5) / 100
years = st.sidebar.slider("Projection Years", min_value=3, max_value=10, value=5)

# Generate Future Cash Flows
cash_flows = [initial_cash_flow * (1 + growth_rate) ** i for i in range(1, years + 1)]
total_value = dcf_valuation(cash_flows, discount_rate, terminal_growth, years)

# Display Valuation Results
st.subheader("Valuation Results")
if total_value:
    formatted_value = f"{currency_symbol} {total_value / 1_000_000_000:,.2f} billion" if is_indonesian_stock else f"{currency_symbol} {total_value:,.2f} million"
    st.write(f"**Intrinsic Value (Total Enterprise Value):** {formatted_value}")

    if market_cap is not None and stock_price is not None:
        formatted_market_cap = f"{currency_symbol} {market_cap / 1_000_000_000:,.2f} billion" if is_indonesian_stock else f"{currency_symbol} {market_cap / 1_000_000:,.2f} million"
        formatted_stock_price = f"{currency_symbol} {stock_price:,.2f}"

        st.write(f"**Market Cap:** {formatted_market_cap}")
        st.write(f"**Current Stock Price:** {formatted_stock_price}")

        # Fair value per share
        if market_cap > 0 and stock_price > 0:
            fair_value_per_share = total_value / (market_cap / stock_price)
            formatted_fair_value = f"{currency_symbol} {fair_value_per_share:,.2f}"
            st.write(f"**Fair Value per Share (DCF Estimate):** {formatted_fair_value}")

        # Convert to USD if necessary
        if is_indonesian_stock and exchange_rate:
            total_value_usd = total_value / exchange_rate
            st.write(f"**Intrinsic Value in USD:** $ {total_value_usd:,.2f}")

# Data Visualization
st.subheader("Projected Cash Flows")
df = pd.DataFrame({"Year": list(range(1, years + 1)), "Cash Flow": cash_flows})
st.line_chart(df.set_index("Year"))

st.write(f"**Formula Used:** DCF = Sum(PV of future cash flows) + PV of terminal value")
