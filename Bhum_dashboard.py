import streamlit as st
import pandas as pd
import numpy as np
# Removed: import plotly.graph_objects as go 

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
data = data.set_index('Year') # Set Year as index for cleaner Streamlit charting

# ---------- SIMULATE IMPACT ----------
# Simple formulas to simulate effect
data['Projected_GDP'] = data['GDP'] - 0.2*interest_rate_change*data['GDP']/100 + 0.1*liquidity_change*data['GDP']/100 - 0.3*inflation_change*data['GDP']/100
data['Projected_Inflation'] = data['Inflation'] + inflation_change


# ---------- PLOTS (Now using Streamlit Native Charts) ----------

st.subheader("GDP vs Projected GDP (in billions)")
# Select and plot both columns
gdp_plot_data = data[['GDP', 'Projected_GDP']]
st.line_chart(gdp_plot_data)

st.subheader("Inflation vs Projected Inflation (%)")
# Select and plot both columns
inflation_plot_data = data[['Inflation', 'Projected_Inflation']]
st.line_chart(inflation_plot_data)


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
# Reset index for table display
summary_df = pd.DataFrame(summary_data)
st.table(summary_df)

st.markdown("""
---
**Note:** This dashboard uses simplified simulation formulas to demonstrate the effects of monetary policy. For real-world analysis, integrate actual RBI data and econometric models.
""")
