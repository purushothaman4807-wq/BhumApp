import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- Custom CSS for Professional Look (RBI-Inspired Tones: Blue/Gold/Silver) ---
st.markdown("""
<style>
/* Font and overall container styling */
.main {
    background-color: #F8F9FA; /* Light gray background */
}
h1, h2, h3, h4, .css-1dp5ss7 {
    color: #004D99; /* Deep RBI Blue */
}
.stMetric {
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 12px;
    border-left: 5px solid #FFC300; /* Gold Accent */
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s;
}
.stMetric:hover {
    transform: translateY(-2px);
}
/* Seaborn/Matplotlib styling for chart area */
.stPlotlyChart, .stImage {
    padding: 10px;
    border-radius: 10px;
    background-color: #FFFFFF;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
/* Style for the scenario summary table */
div[data-testid="stTable"] table {
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
""", unsafe_allow_html=True)

# Set Seaborn style globally for better chart aesthetics
sns.set_theme(style="whitegrid")

# --- HYPOTHETICAL CENTRAL BANK PARAMETERS ---
RBI_TARGET_INFLATION = 4.0 # CPI Target set by the government, typically 4% +/- 2%
CURRENT_REPO_RATE = 6.5  # Current hypothetical policy rate

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Monetary Policy Risk Dashboard", layout="wide")

st.title("💹 Monetary Policy Risk Dashboard")
st.markdown("### Simulating Policy Rate and Liquidity Shocks on Macro Outcomes")

# ---------- SIDEBAR INPUTS ----------
st.sidebar.header("Policy Scenario Simulation")
st.sidebar.markdown("Define changes applied to the base scenario:")
interest_rate_change = st.sidebar.slider("Policy Rate (e.g., Repo Rate) Change (bps)", -200.0, 200.0, 0.0, 25.0, format='%.0f') / 100
liquidity_change = st.sidebar.slider("Systemic Liquidity Change (%)", -5.0, 5.0, 0.0, 0.5)
inflation_change = st.sidebar.slider("Exogenous Inflation Shock (%)", -2.0, 2.0, 0.0, 0.25)

# ---------- SIMULATED HISTORICAL DATA ----------
years = list(range(2010, 2026))
gdp = [1000 + i*50 + np.random.randint(-20, 20) for i in range(len(years))] # Example GDP in billions
inflation = [5 + np.random.uniform(-1, 1) for _ in range(len(years))] # Example CPI %

data = pd.DataFrame({
    "Year": years,
    "GDP": gdp,
    "Inflation": inflation
})
data = data.set_index('Year')

# ---------- SIMULATE IMPACT ----------
# Simple econometric-style formulas to simulate effect
data['Projected_GDP'] = data['GDP'] * (1 - 0.002*interest_rate_change + 0.001*liquidity_change - 0.003*inflation_change)
data['Projected_Inflation'] = data['Inflation'] + inflation_change

# --- CALCULATE ADVANCED METRICS ---
latest_gdp = data['Projected_GDP'].iloc[-1]
latest_inflation = data['Projected_Inflation'].iloc[-1]
projected_interest_rate = CURRENT_REPO_RATE + interest_rate_change
real_interest_rate = projected_interest_rate - latest_inflation
inflation_target_gap = latest_inflation - RBI_TARGET_INFLATION

# ---------- RISK SCORE & METRICS (Organized in Columns) ----------
st.subheader("Key Macro Indicators & Scenario Risk")

col1, col2, col3, col4 = st.columns(4)

# 1. Overall Risk Score
risk_score = abs(interest_rate_change)*3 + abs(liquidity_change)*2 + abs(inflation_change)*4
risk_level = ""
if risk_score < 3:
    risk_level = "Low (Green)"
    risk_color = "green"
elif risk_score < 6:
    risk_level = "Medium (Yellow)"
    risk_color = "orange"
else:
    risk_level = "High (Red)"
    risk_color = "red"

col1.metric(
    label="⚠️ Overall Risk Score (0-10)", 
    value=f"{risk_score:.1f}", 
    delta=f"Level: {risk_level}",
    delta_color=risk_color
)

# 2. Real Interest Rate
col2.metric(
    label="Real Interest Rate (%)",
    value=f"{real_interest_rate:.2f}",
    help="Policy Rate minus Latest Projected Inflation. Positive implies tighter policy."
)

# 3. Inflation Target Gap
gap_delta_color = "red" if inflation_target_gap > 0.5 else ("green" if inflation_target_gap < -0.5 else "off")
col3.metric(
    label=f"Inflation Target Gap (Target: {RBI_TARGET_INFLATION}%)",
    value=f"{inflation_target_gap:.2f} pp",
    delta=f"Projected Inflation: {latest_inflation:.2f}%",
    delta_color=gap_delta_color
)

# 4. Projected GDP Growth
gdp_growth_rate = (data['Projected_GDP'].iloc[-1] / data['GDP'].iloc[-2] - 1) * 100
gdp_delta = gdp_growth_rate - (data['GDP'].iloc[-1] / data['GDP'].iloc[-2] - 1) * 100
col4.metric(
    label="Projected GDP Growth Rate (YoY)",
    value=f"{gdp_growth_rate:.2f}%",
    delta=f"{gdp_delta:.2f} pp change from baseline"
)

st.markdown("---")

# ---------- CHARTS (Organized in Two Columns) ----------
chart_col1, chart_col2 = st.columns(2)

# Prepare data for Seaborn/Matplotlib
data_reset = data.reset_index()

with chart_col1:
    st.subheader("GDP vs Projected GDP (in billions)")
    
    # Matplotlib Figure 1: GDP
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    
    # GDP (Baseline)
    sns.lineplot(x='Year', y='GDP', data=data_reset, ax=ax1, label='Baseline GDP', color='#004D99', linewidth=2)
    
    # Projected GDP (Scenario)
    sns.lineplot(x='Year', y='Projected_GDP', data=data_reset, ax=ax1, label='Projected GDP', color='#FFC300', linestyle='--', linewidth=2)
    
    ax1.set_title("GDP vs Projected GDP (in billions)", fontsize=14)
    ax1.set_ylabel("GDP (in billions)", fontsize=12)
    ax1.set_xlabel("Year", fontsize=12)
    ax1.legend(loc='upper left')
    plt.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1) # Close figure to prevent memory warning

with chart_col2:
    st.subheader("Inflation vs Projected Inflation (%)")
    
    # Matplotlib Figure 2: Inflation
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    
    # Inflation (Baseline)
    sns.lineplot(x='Year', y='Inflation', data=data_reset, ax=ax2, label='Baseline Inflation', color='#D9534F', linewidth=2)
    
    # Projected Inflation (Scenario)
    sns.lineplot(x='Year', y='Projected_Inflation', data=data_reset, ax=ax2, label='Projected Inflation', color='#5CB85C', linestyle='--', linewidth=2)
    
    # Add RBI Target Line
    ax2.axhline(RBI_TARGET_INFLATION, color='gray', linestyle=':', label=f'Target ({RBI_TARGET_INFLATION}%)')
    
    ax2.set_title("Inflation vs Projected Inflation (%)", fontsize=14)
    ax2.set_ylabel("Inflation (%)", fontsize=12)
    ax2.set_xlabel("Year", fontsize=12)
    ax2.legend(loc='upper left')
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2) # Close figure to prevent memory warning

st.markdown("---")

# ---------- SCENARIO SUMMARY & POLICY INSIGHTS ----------

summary_col, insight_col = st.columns([1.5, 2])

with summary_col:
    st.subheader("📊 Scenario Summary: Policy Inputs")
    summary_data = {
        "Policy": ["Interest Rate Change (bps)", "Liquidity Change (%)", "Exogenous Inflation Shock (%)"],
        "Change Applied": [interest_rate_change * 100, liquidity_change, inflation_change]
    }
    summary_df = pd.DataFrame(summary_data)
    st.table(summary_df.set_index('Policy'))

with insight_col:
    st.subheader("💡 Policy Commentary")
    st.info(
        f"""
        **Policy Stance:** A change of **{interest_rate_change*100:.0f} bps** to the policy rate, combined with a **{liquidity_change:+.2f}%** liquidity adjustment, leads to a projected **Real Interest Rate of {real_interest_rate:.2f}%**.
        
        This translates to an **Inflation Target Gap of {inflation_target_gap:.2f} pp**. If the gap is positive, inflation is expected to be above the RBI's target. The central bank would likely need a tighter monetary stance (higher policy rates) to anchor expectations.
        """
    )


st.markdown("""
---
*Disclaimer:* This dashboard uses simplified simulation formulas to demonstrate the qualitative effects of monetary policy. For real-world analysis, integrating actual RBI data and sophisticated econometric models (e.g., Dynamic Stochastic General Equilibrium models) would be necessary.
""")
