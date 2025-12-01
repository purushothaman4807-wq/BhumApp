import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

# --- Configuration and Setup ---
st.set_page_config(layout="wide", page_title="RBI Policy Pulse Dashboard")
REPO_RATE_MOCK = 6.50 # Current mock Repo Rate

def generate_mock_data(start_date, end_date):
    """Generates mock time-series data for the unique metrics."""
    dates = pd.date_range(start=start_date, end=end_date, freq='M')
    n = len(dates)
    
    data = {
        'Date': dates,
        # 1. Inflation Expectations vs. Actual
        'Actual_CPI': np.clip(5 + np.sin(np.arange(n) / 5) + np.random.randn(n) * 0.5, 3.0, 8.0),
        'IESH_1Y_Ahead': np.clip(4.5 + np.cos(np.arange(n) / 5) + np.random.randn(n) * 0.4, 3.5, 7.5),
        # 3. Liquidity Forecasting
        'LAF_Net_Liquidity_Billion': 1000 * np.sin(np.arange(n) / 4) + 500 * np.random.randn(n) + 10000,
        # 4. Global Policy Divergence (India - US Fed Rate)
        'Global_Divergence_Index': REPO_RATE_MOCK - (5.5 + np.random.randn(n) * 0.3),
        'INR_USD': 80 + np.sin(np.arange(n) / 3) * 3 + np.random.randn(n) * 0.5
    }
    return pd.DataFrame(data)

# Load Mock Data
mock_df = generate_mock_data(date(2022, 1, 1), date.today())

# --- Dashboard Header ---
st.title("🏦 RBI Monetary Policy Pulse & Transmission Dashboard")
st.markdown("---")

# --- Tab Navigation for Unique Features ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Transmission Heatmap", "Inflation Expectations Gap", 
    "Liquidity Forecasting", "Global Policy Divergence", "Sectoral Credit Impulse"
])

# =========================================================================
# 1. Policy Transmission Heatmap Tab
# =========================================================================
with tab1:
    st.header("1. Policy Transmission Heatmap 📊")
    st.markdown("Analyzes how Repo Rate changes transmit across various market rates over different time lags.")

    # Mock data for Heatmap
    rates = ['Overnight MIBOR', '3-Month G-Sec Yield', '1-Year MCLR', 'Housing Loan Rate']
    lags = ['1 Month Lag', '3 Month Lag', '6 Month Lag']
    # Mock data: Higher values (darker color) mean stronger transmission
    transmission_data = np.array([
        [0.95, 0.85, 0.70],
        [0.75, 0.80, 0.85],
        [0.40, 0.65, 0.75],
        [0.30, 0.50, 0.60]
    ])
    
    heatmap_df = pd.DataFrame(transmission_data, index=rates, columns=lags)

    fig = px.imshow(
        heatmap_df,
        text_auto=".1f",
        aspect="auto",
        color_continuous_scale=px.colors.sequential.Viridis,
        title="Repo Rate Transmission Coefficient (0 to 1)"
    )
    fig.update_xaxes(side="top")
    st.plotly_chart(fig, use_container_width=True)

# =========================================================================
# 2. Inflation Expectations Gap Tab
# =========================================================================
with tab2:
    st.header("2. Inflation Expectations Gap Analysis 📈")
    st.markdown("Compares household expectations on inflation (IESH) against actual CPI. The **Gap** is a measure of public confidence and policy credibility.")

    # Create the Gap column
    mock_df['Expectations_Gap'] = mock_df['IESH_1Y_Ahead'] - mock_df['Actual_CPI']

    # Primary Line Chart: Actual vs. Expected
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=mock_df['Date'], y=mock_df['Actual_CPI'], mode='lines', name='Actual CPI (%)'))
    fig.add_trace(go.Scatter(x=mock_df['Date'], y=mock_df['IESH_1Y_Ahead'], mode='lines', name='IESH (Expected CPI) (%)'))
    
    # Bar Chart for the Gap
    fig_gap = px.bar(mock_df, x='Date', y='Expectations_Gap', 
                      title='Inflation Expectations Gap (IESH - Actual CPI)',
                      color='Expectations_Gap',
                      color_continuous_scale='RdBu')
    
    st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(fig_gap, use_container_width=True)

# =========================================================================
# 3. Liquidity Forecasting Tool Tab
# =========================================================================
with tab3:
    st.header("3. Systemic Liquidity Pulse & Forecast 🌊")
    st.markdown("Tracks the Net Liquidity Adjustment Facility (LAF) and projects short-term trends based on known drivers (e.g., GST/Tax outflows, government securities).")

    # Add a simple forecast (just extending the last trend with noise for mock)
    last_date = mock_df['Date'].iloc[-1]
    forecast_dates = pd.date_range(start=last_date + timedelta(days=1), periods=30, freq='D')
    last_liquidity = mock_df['LAF_Net_Liquidity_Billion'].iloc[-1]
    forecast_liquidity = last_liquidity + 50 * np.sin(np.arange(30) / 5) + np.random.randn(30) * 10
    
    forecast_df = pd.DataFrame({'Date': forecast_dates, 'LAF_Net_Liquidity_Billion': forecast_liquidity})
    forecast_df['Type'] = 'Forecast'
    mock_df['Type'] = 'Actual'
    
    combined_df = pd.concat([mock_df[['Date', 'LAF_Net_Liquidity_Billion', 'Type']], 
                              forecast_df])

    fig = px.line(combined_df, x='Date', y='LAF_Net_Liquidity_Billion', color='Type',
                  title='Net LAF Liquidity (₹ Billion) - Actual and 30-Day Forecast',
                  markers=False)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display drivers of change (mock data for today's liquidity)
    st.subheader("Liquidity Drivers for Next 7 Days (Mock)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Government Cash Balance", "+₹500 Bn", "Tax Inflows")
    col2.metric("Forex Intervention", "-₹150 Bn", "USD Sales")
    col3.metric("Festival Currency Demand", "-₹200 Bn", "Seasonal")

# =========================================================================
# 4. Global Policy Divergence Index Tab
# =========================================================================
with tab4:
    st.header("4. Global Policy Divergence Index 🌎")
    st.markdown("Visualizing the difference between RBI's Repo Rate and the US Federal Reserve's rate, and its correlation with the Rupee (INR/USD).")

    fig = go.Figure()
    # Add Divergence Index (Bar Chart)
    fig.add_trace(go.Bar(x=mock_df['Date'], y=mock_df['Global_Divergence_Index'], name='Policy Divergence (Percentage Points)', yaxis='y1'))
    
    # Add INR/USD Rate (Line on secondary axis)
    fig.add_trace(go.Scatter(x=mock_df['Date'], y=mock_df['INR_USD'], mode='lines', name='INR/USD Exchange Rate', yaxis='y2'))

    fig.update_layout(
        title='Global Policy Divergence vs. INR/USD Exchange Rate',
        yaxis=dict(title='Policy Divergence Index (pp)', side='left'),
        yaxis2=dict(title='INR/USD', side='right', overlaying='y', range=[75, 85]) # Example range
    )

    st.plotly_chart(fig, use_container_width=True)

# =========================================================================
# 5. Sectoral Credit Impulse Tab
# =========================================================================
with tab5:
    st.header("5. Sectoral Credit Impulse Tracker 🏗️")
    st.markdown("Measures the change in new credit flow relative to GDP to assess which sectors are actively leveraging credit post-policy changes.")

    # Mock data for Sectoral Credit Impulse (last 12 months)
    sector_impulse = {
        'Sector': ['Infrastructure', 'Manufacturing', 'Services', 'Housing', 'Agriculture'],
        'Credit_Impulse': [0.8, 1.2, 0.6, 1.5, 0.4], # Higher is better/more impulse
        'Credit_Flow_YoY': [15.2, 10.5, 18.0, 22.1, 7.8],
        'GDP_Share': [10, 20, 50, 5, 15]
    }
    impulse_df = pd.DataFrame(sector_impulse)
    
    fig = px.sunburst(
        impulse_df, 
        path=['Sector'], 
        values='GDP_Share', 
        color='Credit_Impulse', 
        color_continuous_scale='RdYlGn', 
        title='Sectoral Credit Impulse Breakdown (Credit Impulse score determines color)'
    )

    st.plotly_chart(fig, use_container_width=True)
