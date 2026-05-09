import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.express as px

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="Financial Health Dashboard",
    page_icon="📊",
    layout="wide"
)

# =====================
# LOAD DATA
# =====================
@st.cache_data
def load_data(ticker):
    company = yf.Ticker(ticker)
    income_stmt = company.financials.T
    balance_sheet = company.balance_sheet.T
    cash_flow = company.cashflow.T

    for df in [income_stmt, balance_sheet, cash_flow]:
        df.index = df.index.year
        df.dropna(how='all', inplace=True)

    ratios = pd.DataFrame()
    ratios['Net Profit Margin (%)'] = income_stmt['Net Income'] / income_stmt['Total Revenue'] * 100
    ratios['Gross Profit Margin (%)'] = income_stmt['Gross Profit'] / income_stmt['Total Revenue'] * 100
    ratios['EBITDA Margin (%)'] = income_stmt['EBITDA'] / income_stmt['Total Revenue'] * 100
    ratios['Operating Margin (%)'] = income_stmt['Operating Income'] / income_stmt['Total Revenue'] * 100
    ratios['Current Ratio'] = balance_sheet['Current Assets'] / balance_sheet['Current Liabilities']
    ratios['Working Capital (B)'] = balance_sheet['Working Capital'] / 1e9
    ratios['Asset Turnover'] = income_stmt['Total Revenue'] / balance_sheet['Total Assets']
    ratios['ROA (%)'] = income_stmt['Net Income'] / balance_sheet['Total Assets'] * 100
    ratios['Debt to Equity'] = balance_sheet['Total Debt'] / balance_sheet['Stockholders Equity']
    ratios['Net Debt (B)'] = balance_sheet['Net Debt'] / 1e9

    return ratios.round(2).sort_index()

# =====================
# HEADER
# =====================
st.title("📊 Financial Health Dashboard")
st.markdown("Analyzing real financial performance using live market data")

ticker = st.selectbox("Select Company", ["MSFT", "AMZN", "AAPL", "GOOGL"])
ratios = load_data(ticker)
latest = ratios.iloc[-1]

st.markdown(f"### Showing data for: `{ticker}` | Latest Year: `{ratios.index[-1]}`")
st.divider()

# =====================
# KPI CARDS
# =====================
st.subheader("📌 Key Metrics — Latest Year")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Net Profit Margin", f"{latest['Net Profit Margin (%)']:.2f}%")
col2.metric("Gross Profit Margin", f"{latest['Gross Profit Margin (%)']:.2f}%")
col3.metric("Current Ratio", f"{latest['Current Ratio']:.2f}")
col4.metric("Debt to Equity", f"{latest['Debt to Equity']:.2f}")

col5, col6, col7, col8 = st.columns(4)
col5.metric("ROA", f"{latest['ROA (%)']:.2f}%")
col6.metric("EBITDA Margin", f"{latest['EBITDA Margin (%)']:.2f}%")
col7.metric("Asset Turnover", f"{latest['Asset Turnover']:.2f}")
col8.metric("Working Capital (B)", f"${latest['Working Capital (B)']:.2f}B")

st.divider()

# =====================
# TREND CHARTS
# =====================
st.subheader("📈 5-Year Trends")

col_a, col_b = st.columns(2)

with col_a:
    fig1 = px.line(ratios, y=['Net Profit Margin (%)', 'Gross Profit Margin (%)', 'EBITDA Margin (%)'],
                   title="Profitability Margins Over Time", markers=True)
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    fig2 = px.line(ratios, y=['Current Ratio', 'Asset Turnover'],
                   title="Liquidity & Efficiency Over Time", markers=True)
    st.plotly_chart(fig2, use_container_width=True)

col_c, col_d = st.columns(2)

with col_c:
    fig3 = px.bar(ratios, y='Net Debt (B)', title="Net Debt Over Time (in Billions)",
                  color='Net Debt (B)', color_continuous_scale='reds')
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    fig4 = px.line(ratios, y=['ROA (%)'], title="Return on Assets Over Time", markers=True)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# =====================
# HEALTH SCORECARD
# =====================
st.subheader("🏥 Financial Health Scorecard")
st.markdown("Benchmarks based on industry standards for large-cap tech companies")

def score(metric, value):
    benchmarks = {
        'Net Profit Margin (%)':   {'green': 20,  'yellow': 10},
        'Gross Profit Margin (%)': {'green': 50,  'yellow': 30},
        'EBITDA Margin (%)':       {'green': 25,  'yellow': 15},
        'Operating Margin (%)':    {'green': 25,  'yellow': 15},
        'Current Ratio':           {'green': 1.5, 'yellow': 1.0},
        'ROA (%)':                 {'green': 10,  'yellow': 5},
        'Debt to Equity':          {'green': 0.5, 'yellow': 1.0},
        'Asset Turnover':          {'green': 0.5, 'yellow': 0.3},
        'Working Capital (B)':     {'green': 10,  'yellow': 0},
    }
    if metric not in benchmarks:
        return "⚪ N/A"
    b = benchmarks[metric]
    if metric == 'Debt to Equity':
        if value <= b['green']:   return "🟢 Strong"
        elif value <= b['yellow']: return "🟡 Moderate"
        else: return "🔴 Weak"
    else:
        if value >= b['green']:   return "🟢 Strong"
        elif value >= b['yellow']: return "🟡 Moderate"
        else: return "🔴 Weak"

scorecard_data = {
    'Metric': [],
    'Latest Value': [],
    'Health': []
}

for col in ['Net Profit Margin (%)', 'Gross Profit Margin (%)', 'EBITDA Margin (%)',
            'Operating Margin (%)', 'Current Ratio', 'ROA (%)',
            'Debt to Equity', 'Asset Turnover', 'Working Capital (B)']:
    scorecard_data['Metric'].append(col)
    scorecard_data['Latest Value'].append(latest[col])
    scorecard_data['Health'].append(score(col, latest[col]))

scorecard_df = pd.DataFrame(scorecard_data)
st.dataframe(scorecard_df, use_container_width=True, hide_index=True)

green_count = scorecard_df['Health'].str.contains('Strong').sum()
yellow_count = scorecard_df['Health'].str.contains('Moderate').sum()
red_count = scorecard_df['Health'].str.contains('Weak').sum()
total = len(scorecard_df)

overall_score = round((green_count * 100 + yellow_count * 50) / total, 1)

st.markdown("### 🎯 Overall Financial Health Score")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Overall Score", f"{overall_score}/100")
col2.metric("🟢 Strong", f"{green_count} metrics")
col3.metric("🟡 Moderate", f"{yellow_count} metrics")
col4.metric("🔴 Weak", f"{red_count} metrics")

if overall_score >= 75:
    st.success(f"{ticker} shows strong overall financial health.")
elif overall_score >= 50:
    st.warning(f"{ticker} shows moderate financial health with some areas of concern.")
else:
    st.error(f"{ticker} shows weak financial health. Further analysis recommended.")

st.divider()

# =====================
# RAW DATA TABLE
# =====================
st.subheader("📋 Full Ratio Table (All Years)")
st.dataframe(ratios, use_container_width=True)