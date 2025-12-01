# Bhum_dashboard_enhanced.py
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# Try to import matplotlib for heatmap plotting; if not available we fall back.
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Monetary Policy Risk Dashboard (Enhanced)", layout="wide")

# ---------- THEME SELECTOR (simple CSS tweak) ----------
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown(
        """
        <style>
        .stApp { background-color: #0f1724; color: #e6eef8; }
        .stButton>button { background-color:#0b84ff; color: white; }
        .css-1d391kg { color: #e6eef8; }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    # minimal reset for light theme
    st.markdown("<style>.stApp{background-color: white; color: black;}</style>", unsafe_allow_html=True)

st.title("💹 Monetary Policy Risk Dashboard — Enhanced")
st.markdown(
    "Interactive simulation of monetary policy shocks with uncertainty, heatmap risk, per-capita views, and automatic insights."
)

# ---------- SIDEBAR INPUTS ----------
st.sidebar.header("Policy Scenario Inputs")

# baseline inputs (so we can compute real rates)
baseline_policy_rate = st.sidebar.number_input("Baseline Policy Rate (%)", min_value=0.0, max_value=20.0, value=6.0, step=0.25)
baseline_inflation = st.sidebar.number_input("Baseline Inflation (%)", min_value=-5.0, max_value=20.0, value=5.0, step=0.1)

interest_rate_change = st.sidebar.slider("Interest Rate Change (percentage points)", -2.0, 2.0, 0.0, 0.25)
liquidity_change = st.sidebar.slider("Liquidity Change (%)", -5.0, 5.0, 0.0, 0.5)
inflation_change = st.sidebar.slider("Inflation Change (percentage points)", -2.0, 2.0, 0.0, 0.25)

# population inputs for per-capita
st.sidebar.markdown("---")
base_population = st.sidebar.number_input("Base Population (millions)", min_value=1.0, value=1400.0, step=1.0)  # millions
pop_growth_rate = st.sidebar.slider("Annual Population Growth (%)", 0.0, 2.5, 0.9, 0.1)

# scenario presets
scenario = st.sidebar.selectbox("Scenario Preset", ["Custom", "Tightening cycle", "Easing cycle", "Liquidity shock", "Inflation shock", "Stagflation"])
if scenario != "Custom":
    if scenario == "Tightening cycle":
        interest_rate_change = 1.0
        liquidity_change = -1.0
        inflation_change = -0.25
    elif scenario == "Easing cycle":
        interest_rate_change = -1.0
        liquidity_change = 2.0
        inflation_change = 0.25
    elif scenario == "Liquidity shock":
        interest_rate_change = 0.0
        liquidity_change = -4.0
        inflation_change = 0.2
    elif scenario == "Inflation shock":
        interest_rate_change = 0.5
        liquidity_change = 0.0
        inflation_change = 1.5
    elif scenario == "Stagflation":
        interest_rate_change = 0.5
        liquidity_change = -1.5
        inflation_change = 1.2

# ---------- SIMULATED HISTORICAL DATA ----------
years = list(range(2010, 2026))
rng = np.random.default_rng(seed=42)  # deterministic noise for reproducibility

# baseline historical GDP (in billions) and inflation (%)
gdp = [1000 + i * 50 + int(rng.integers(-20, 20)) for i in range(len(years))]
inflation = [5.0 + float(rng.uniform(-1.0, 1.0)) for _ in range(len(years))]

data = pd.DataFrame({"Year": years, "GDP": gdp, "Inflation": inflation})
data = data.set_index("Year")

# ---------- ADVANCED / NONLINEAR SIMULATION ----------
# We'll compute projected values and also a best/worst (confidence band).
# Nonlinear formula idea:
# - interest effect: larger hikes have accelerating negative impact (quadratic)
# - liquidity effect: positive liquidity helps but with diminishing returns (saturating)
# - inflation effect: higher inflation reduces real GDP (linear + quadratic penalty above 2%)
#
# We'll also produce per-capita GDP with user population inputs.

# helper params (tunable)
alpha_int = 0.6   # sensitivity to interest change (linear)
beta_int = 0.25   # quadratic term coefficient (accelerating effect)
alpha_liq = 0.15  # sensitivity to liquidity (linear)
gamma_infl = 0.35 # sensitivity to inflation change
quadratic_infl_threshold = 2.0  # if inflation_change above this, extra penalty

projected_gdp = []
projected_infl = []
proj_gdp_best = []
proj_gdp_worst = []

# Historical volatility to generate confidence bands
gdp_vol_pct = np.std(np.diff(data["GDP"])) / np.mean(data["GDP"])  # rough
if np.isnan(gdp_vol_pct) or gdp_vol_pct <= 0:
    gdp_vol_pct = 0.02

for y in data.index:
    base_gdp = data.loc[y, "GDP"]
    base_infl = data.loc[y, "Inflation"]

    # Nonlinear interest effect (percentage of GDP)
    int_lin = alpha_int * interest_rate_change
    int_quad = beta_int * (max(0, interest_rate_change) ** 2) if interest_rate_change > 0 else beta_int * (min(0, interest_rate_change) ** 2)  # symmetric
    interest_effect_pct = int_lin + int_quad  # positive means % reduction when interest goes up

    # Liquidity effect (diminishing returns): use tanh-like saturating function scaled
    liquidity_effect_pct = alpha_liq * np.tanh(liquidity_change / 5.0)  # scaled so +/-5 maps into tanh range

    # Inflation penalty: linear plus extra quadratic penalty beyond threshold
    infl_effect_pct = gamma_infl * inflation_change
    if abs(inflation_change) > quadratic_infl_threshold:
        infl_effect_pct += 0.05 * (abs(inflation_change) - quadratic_infl_threshold) ** 2 * np.sign(inflation_change)  # extra penalty

    # Combined percent change to GDP (positive means growth, negative means contraction)
    combined_pct = -interest_effect_pct + liquidity_effect_pct - infl_effect_pct

    # Convert percentage (units are percentage points) into absolute GDP change
    projected = base_gdp * (1 + combined_pct / 100.0)
    # ensure projected not negative
    projected = max(projected, 0.0)

    # Confidence band +/- based on volatility and magnitude of shocks
    shock_strength = (abs(interest_rate_change) * 0.6 + abs(liquidity_change) * 0.3 + abs(inflation_change) * 0.8)
    band_multiplier = 1 + min(0.6, shock_strength / 5.0)  # bigger shocks -> wider band up to 60% increase in band
    band = base_gdp * gdp_vol_pct * band_multiplier

    best = projected + band
    worst = max(projected - band, 0.0)

    projected_gdp.append(projected)
    proj_gdp_best.append(best)
    proj_gdp_worst.append(worst)

    # Inflation projection is simpler: base + inflation_change + small diffusion
    projected_inflation = base_infl + inflation_change
    # Clip unrealistic inflation
    projected_inflation = float(np.clip(projected_inflation, -10, 50))
    projected_infl.append(projected_inflation)

# add to dataframe
data["Projected_GDP"] = projected_gdp
data["GDP_Best"] = proj_gdp_best
data["GDP_Worst"] = proj_gdp_worst
data["Projected_Inflation"] = projected_infl

# ---------- PER-CAPITA CALCULATION ----------
# Build population timeline based on user base pop and growth rate
pop_millions = [base_population * ((1 + pop_growth_rate / 100.0) ** i) for i in range(len(years))]
pop = np.array(pop_millions)  # in millions
data["Population_millions"] = pop
# GDP per capita in thousands (so it's readable) -> (GDP billions) / (population millions) * 1000 = per-capita in thousands
data["GDP_per_capita_k"] = (data["GDP"] / data["Population_millions"]) * 1000.0
data["Projected_GDP_per_capita_k"] = (data["Projected_GDP"] / data["Population_millions"]) * 1000.0

# ---------- REAL EFFECTIVE INTEREST RATE ----------
# We interpret baseline_policy_rate and baseline_inflation as levels; compute new real rate after change
# Note: user provided baseline_inflation and baseline_policy_rate above
new_nominal_rate = baseline_policy_rate + interest_rate_change
new_inflation_rate = baseline_inflation + inflation_change
real_rate = new_nominal_rate - new_inflation_rate

# ---------- RISK SCORE: improved (weighted + contributions + heatmap input) ----------
# Build contributions per component (normalized)
contrib_interest = abs(interest_rate_change) * 3.0
contrib_liquidity = abs(liquidity_change) * 2.0
contrib_inflation = abs(inflation_change) * 4.0
risk_score = contrib_interest + contrib_liquidity + contrib_inflation
# Normalize to 0-10 scale roughly
risk_score_normalized = min(10.0, (risk_score / 9.0) * 10.0)

if risk_score_normalized < 3:
    risk_level = "Low"
elif risk_score_normalized < 6:
    risk_level = "Medium"
else:
    risk_level = "High"

# ---------- UI LAYOUT ----------
st.subheader("Scenario Overview")
left, right = st.columns([2, 1])
with left:
    st.write("**Policy inputs**")
    st.write(f"- Baseline policy rate: **{baseline_policy_rate:.2f}%**")
    st.write(f"- Baseline inflation: **{baseline_inflation:.2f}%**")
    st.write(f"- Scenario preset: **{scenario}**")
    st.write(f"- Interest rate change: **{interest_rate_change:+.2f} pp**")
    st.write(f"- Liquidity change: **{liquidity_change:+.2f}%**")
    st.write(f"- Inflation change: **{inflation_change:+.2f} pp**")
    st.write(f"- Base population: **{base_population:.1f}M**, growth: **{pop_growth_rate:.2f}%**")
with right:
    st.metric("Risk Score (0-10)", f"{risk_score_normalized:.2f}", delta=f"Level: {risk_level}")
    st.metric("Real Policy Rate (%)", f"{real_rate:.2f}", delta=f"Nominal: {new_nominal_rate:.2f}%, Inflation: {new_inflation_rate:.2f}%")

# ---------- PLOTS (Streamlit native charts) ----------
st.subheader("GDP & Projections")
gdp_plot = data[["GDP", "Projected_GDP"]].copy()
st.line_chart(gdp_plot)

# show confidence bands as area chart (we'll show best and worst as area fill)
st.subheader("Projected GDP with Confidence Bands")
band_df = data[["Projected_GDP", "GDP_Best", "GDP_Worst"]].reset_index()
# area chart: project worst->projected->best as three lines. Streamlit can't fill between easily; we show lines and also table.
st.line_chart(band_df.set_index("Year")[["Projected_GDP", "GDP_Best", "GDP_Worst"]])

st.subheader("Inflation Projection")
st.line_chart(data[["Inflation", "Projected_Inflation"]])

st.subheader("GDP per Capita (thousands)")
st.line_chart(data[["GDP_per_capita_k", "Projected_GDP_per_capita_k"]])

# ---------- 1. Baseline vs Scenario comparison table ----------
st.subheader("Baseline vs Projected (Latest Year Comparison)")
latest_year = data.index.max()
baseline_gdp_latest = data.loc[latest_year, "GDP"]
projected_gdp_latest = data.loc[latest_year, "Projected_GDP"]
baseline_infl_latest = data.loc[latest_year, "Inflation"]
projected_infl_latest = data.loc[latest_year, "Projected_Inflation"]

comparison = pd.DataFrame({
    "Metric": ["GDP (billions)", "Inflation (%)", "GDP per capita (k)"],
    "Baseline": [baseline_gdp_latest, baseline_infl_latest, data.loc[latest_year, "GDP_per_capita_k"]],
    "Projected": [projected_gdp_latest, projected_infl_latest, data.loc[latest_year, "Projected_GDP_per_capita_k"]]
})
comparison["Change_pct"] = ((comparison["Projected"] - comparison["Baseline"]) / comparison["Baseline"]) * 100.0
st.table(comparison.style.format({"Baseline": "{:.2f}", "Projected": "{:.2f}", "Change_pct": "{:+.2f}%"}))

# ---------- 4. Risk Contribution Heatmap (per component) ----------
st.subheader("Risk Contribution (per component) — Safe Mode")

heat_df = pd.DataFrame({
    "Component": ["Interest Rate", "Liquidity", "Inflation"],
    "Change": [interest_rate_change, liquidity_change, inflation_change],
    "Contribution_raw": [contrib_interest, contrib_liquidity, contrib_inflation]
}).set_index("Component")

# Normalized 0–1 safely (no ptp/empty errors)
ptp_val = heat_df["Contribution_raw"].max() - heat_df["Contribution_raw"].min()
if ptp_val == 0:
    heat_df["Normalized"] = 0.5
else:
    heat_df["Normalized"] = (heat_df["Contribution_raw"] - heat_df["Contribution_raw"].min()) / ptp_val

# SAFE & CLEAN TABLE (no matplotlib, no seaborn)
st.write("Heatmap disabled due to Streamlit Cloud matplotlib limitations.")
st.dataframe(
    heat_df.style.format({
        "Change": "{:+.2f}",
        "Contribution_raw": "{:.2f}",
        "Normalized": "{:.2f}"
    })
)


# ---------- 5. Dynamic Insights (AI-like logic) ----------
st.subheader("Automated Insights")
insights = []
# Insight based on contributions
dominant = heat_df["Contribution (raw)"].idxmax()
insights.append(f"- The largest contributor to risk is **{dominant}** (contribution: {heat_df.loc[dominant, 'Contribution (raw)']:.2f}).")

# Interpret direction
if interest_rate_change > 0:
    insights.append(f"- Rising interest rates ({interest_rate_change:+.2f} pp) are likely to **slow GDP growth** and tighten financial conditions.")
elif interest_rate_change < 0:
    insights.append(f"- Cutting interest rates ({interest_rate_change:+.2f} pp) provides stimulus and may boost growth.")
else:
    insights.append("- Interest rate stance unchanged in this scenario.")

if liquidity_change < 0:
    insights.append(f"- Liquidity contraction ({liquidity_change:+.2f}%) could pressure markets and credit availability.")
elif liquidity_change > 0:
    insights.append(f"- Liquidity injection ({liquidity_change:+.2f}%) supports activity and financial markets.")
else:
    insights.append("- No major change in liquidity.")

if inflation_change > 0.5:
    insights.append(f"- Inflation is rising by {inflation_change:+.2f} pp — monetary tightening may be appropriate to anchor expectations.")
elif inflation_change < -0.5:
    insights.append(f"- Inflation is falling by {inflation_change:+.2f} pp — policy could stay accommodative to support demand.")
else:
    insights.append("- Inflation change is modest.")

# Put a combined risk insight
if risk_score_normalized >= 7:
    insights.append("- Overall assessment: **High risk**. Consider combining measured liquidity support with targeted supply-side measures.")
elif risk_score_normalized >= 4:
    insights.append("- Overall assessment: **Medium risk**. Monitor incoming data and be ready to adjust policy.")
else:
    insights.append("- Overall assessment: **Low risk**. Scenario appears manageable.")

for line in insights:
    st.write(line)

# ---------- DOWNLOAD BUTTON ----------
st.subheader("Download Simulation Data")
csv = data.reset_index().to_csv(index=False).encode("utf-8")
st.download_button("Download full simulation CSV", csv, file_name="monetary_simulation.csv", mime="text/csv")

# ---------- OPTIONAL: Show raw table and last-year summary ----------
with st.expander("Show full simulation table"):
    st.dataframe(data.reset_index().round(3))

st.subheader("Last Year / Snapshot")
snapshot = pd.DataFrame({
    "Metric": ["Baseline GDP (b)", "Projected GDP (b)", "Baseline Inflation (%)", "Projected Inflation (%)", "Real Policy Rate (%)"],
    "Value": [baseline_gdp_latest, projected_gdp_latest, baseline_infl_latest, projected_infl_latest, real_rate]
})
st.table(snapshot.style.format({"Value": "{:.2f}"}))

st.markdown(
    """
    ---
    **Notes:** 
    - This is a simplified simulation tool for scenario exploration. For formal policy work integrate high-frequency macro time-series and structural models.
    - Nonlinear terms and confidence bands are illustrative.
    """
)
