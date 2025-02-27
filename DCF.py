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
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL or BBRI.JK)", value="AAPL").upper()

# Determine currency based on ticker suffix
is_indonesian_stock = ticker.endswith(".JK")
currency_symbol = "Rp." if is_indonesian_stock else "$"

# Fetch exchange rate (optional feature)
try:
    if is_indonesian_stock:
        exchange_rate = yf.Ticker("USDIDR=X").history(period="1d")["Close"].iloc[-1]
    else:
        exchange_rate = 1  # USD-based stocks, no conversion needed
except:
    exchange_rate = None

# Fetch data from Yahoo Finance
try:
    data = yf.Ticker(ticker)
    cash_flow_data = data.cashflow

    # Ensure cash flow data is not empty before extracting FCF
    if not cash_flow_data.empty and "Total Cash From Operating Activities" in cash_flow_data.index:
        initial_cash_flow = cash_flow_data.loc["Total Cash From Operating Activities"].values[0]
    else:
        initial_cash_flow = 100.0  # Default if data isn't available

    # Get stock price & market cap
    stock_price = data.history(period="1d")["Close"].iloc[-1] if "Close" in data.history(period="1d") else None
    market_cap = data.info.get("marketCap", None)

except Exception as e:
    st.error(f"Error fetching data for {ticker}: {e}")
    initial_cash_flow = 100.0
    stock_price, market_cap = None, None

growth_rate = st.sidebar.number_input("Annual Growth Rate (%)", value=5.0, step=0.5) / 100
discount_rate = st.sidebar.number_input("Discount Rate (%)", value=10.0, step=0.5) / 100
terminal_growth = st.sidebar.number_input("Terminal Growth Rate (%)", value=2.0, step=0.5) / 100
years = st.sidebar.slider("Projection Years", min_value=3, max_value=10, value=5)

# Generate future cash flows
cash_flows = [initial_cash_flow * (1 + growth_rate) ** i for i in range(1, years + 1)]
total_value = dcf_valuation(cash_flows, discount_rate, terminal_growth, years)

st.subheader("Valuation Results")
if total_value:
    # Convert to billions for better readability
    if is_indonesian_stock:
        formatted_value = f"{currency_symbol} {total_value / 1_000_000_000:,.2f} billion"
    else:
        formatted_value = f"{currency_symbol} {total_value:,.2f} million"

    st.write(f"**Intrinsic Value (Total Enterprise Value):** {formatted_value}")

    if market_cap is not None and stock_price is not None:
        # Convert market cap to billions for IDR stocks
        if is_indonesian_stock:
            formatted_market_cap = f"{currency_symbol} {market_cap / 1_000_000_000:,.2f} billion"
        else:
            formatted_market_cap = f"{currency_symbol} {market_cap / 1_000_000:,.2f} million"

        formatted_stock_price = f"{currency_symbol} {stock_price:,.2f}"

        st.write(f"**Market Cap:** {formatted_market_cap}")
        st.write(f"**Current Stock Price:** {formatted_stock_price}")

        # Fair value per share (only calculate if values are valid)
        if market_cap > 0 and stock_price > 0:
            fair_value_per_share = total_value / (market_cap / stock_price)
            formatted_fair_value = f"{currency_symbol} {fair_value_per_share:,.2f}"
            st.write(f"**Fair Value per Share (DCF Estimate):** {formatted_fair_value}")

        # Optional: Convert to USD for better comparison
        if is_indonesian_stock and exchange_rate:
            total_value_usd = total_value / exchange_rate
            st.write(f"**Intrinsic Value in USD:** $ {total_value_usd:,.2f} million")

# Data Visualization
st.subheader("Projected Cash Flows")
df = pd.DataFrame({"Year": list(range(1, years + 1)), "Cash Flow": cash_flows})
st.line_chart(df.set_index("Year"))

st.write(f"**Formula Used:** DCF = Sum(PV of future cash flows) + PV of terminal value")
