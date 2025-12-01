import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go # Using graph_objects instead of express

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Monetary Policy Risk Dashboard", layout="wide")

st.title("💹 Monetary Policy Risk Dashboard")
st.markdown("""
This dashboard allows you to simulate the impact of changes in **interest rates, liquidity, and inflation** on GDP and inflation. Adjust the sliders to see projected risks.
""")

# ---------- SIDEBAR INPUTS ----------
st.sidebar.header("Policy Scenario Simulation")
interest_rate_change = st.sidebar.slider("Interest Rate Change (%)", -2.0, 2.0, 0.0, 0.25)
liquidity_change = st.sidebar.slider("Liquidity Change (%)", -5.0, 5.0, 0.0, 0.5)
inflation_change = st.sidebar.slider("Inflation Change (%)", -2.0, 2.0, 0.0, 0.25)

# ---------- SIMULATED HISTORICAL DATA ----------
years = list(range(2010, 2026))
gdp = [1000 + i*50 + np.random.randint(-20, 20) for i in range(len(years))] # Example GDP in billions
inflation = [5 + np.random.uniform(-1, 1) for _ in range(len(years))] # Example CPI %

data = pd.DataFrame({
    "Year": years,
    "GDP": gdp,
    "Inflation": inflation
})

# ---------- SIMULATE IMPACT ----------
# Simple formulas to simulate effect
data['Projected_GDP'] = data['GDP'] - 0.2*interest_rate_change*data['GDP']/100 + 0.1*liquidity_change*data['GDP']/100 - 0.3*inflation_change*data['GDP']/100
data['Projected_Inflation'] = data['Inflation'] + inflation_change

# ---------- PLOTS (Now using plotly.graph_objects) ----------

# GDP Plot
fig_gdp = go.Figure()
fig_gdp.add_trace(go.Scatter(
    x=data['Year'], 
    y=data['GDP'], 
    mode='lines+markers', 
    name='GDP'
))
fig_gdp.add_trace(go.Scatter(
    x=data['Year'], 
    y=data['Projected_GDP'], 
    mode='lines+markers', 
    name='Projected_GDP'
))
fig_gdp.update_layout(
    title="GDP vs Projected GDP",
    xaxis_title='Year',
    yaxis_title='GDP (in billions)'
)

# Inflation Plot
fig_inflation = go.Figure()
fig_inflation.add_trace(go.Scatter(
    x=data['Year'], 
    y=data['Inflation'], 
    mode='lines+markers', 
    name='Inflation'
))
fig_inflation.add_trace(go.Scatter(
    x=data['Year'], 
    y=data['Projected_Inflation'], 
    mode='lines+markers', 
    name='Projected_Inflation'
))
fig_inflation.update_layout(
    title="Inflation vs Projected Inflation",
    xaxis_title='Year',
    yaxis_title='Inflation (%)'
)

# ---------- DISPLAY ----------
st.plotly_chart(fig_gdp, use_container_width=True)
st.plotly_chart(fig_inflation, use_container_width=True)

# ---------- RISK SCORE ----------
risk_score = abs(interest_rate_change)*3 + abs(liquidity_change)*2 + abs(inflation_change)*4
risk_level = ""
if risk_score < 3:
    risk_level = "Low"
elif risk_score < 6:
    risk_level = "Medium"
else:
    risk_level = "High"

st.subheader("⚠️ Overall Risk Assessment")
st.metric(label="Risk Score (0-10)", value=f"{risk_score:.1f}", delta=f"Level: {risk_level}")

# ---------- SCENARIO SUMMARY ----------
st.subheader("📊 Scenario Summary")
summary_data = {
    "Policy": ["Interest Rate Change (%)", "Liquidity Change (%)", "Inflation Change (%)"],
    "Change Applied": [interest_rate_change, liquidity_change, inflation_change]
}
summary_df = pd.DataFrame(summary_data)
st.table(summary_df)

st.markdown("""
---
**Note:** This dashboard uses simplified simulation formulas to demonstrate the effects of monetary policy. For real-world analysis, integrate actual RBI data and econometric models.
""")
