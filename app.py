import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from simulation import run_simulation, calculate_statistics

st.set_page_config(page_title="Retirement Planner", page_icon="📈")

st.markdown("""
<style>
    .block-container { padding-top: 3rem; padding-bottom: 1rem; max-width: 700px; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem; }
    [data-testid="stMetricValue"] { font-size: 1.3rem; }
    /* Compact form */
    [data-testid="stForm"] [data-testid="stVerticalBlock"] > div { padding-top: 0; padding-bottom: 0; }
    [data-testid="stForm"] .stTextInput, [data-testid="stForm"] .stNumberInput { margin-bottom: -0.5rem; }
    /* Force columns side by side on mobile */
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap; gap: 0.5rem; }
    @media (max-width: 768px) {
        .block-container { padding-left: 0.5rem; padding-right: 0.5rem; padding-top: 2.5rem; }
        .success-heading { font-size: 1.3rem !important; }
        [data-testid="stMetricValue"] { font-size: 1rem; }
        [data-testid="stMetricLabel"] { font-size: 0.7rem; }
        [data-testid="stForm"] [data-testid="stHorizontalBlock"] > div { flex: 1 1 50%; min-width: 0; }
    }
</style>
""", unsafe_allow_html=True)

# Reserve layout slots: chart on top, options in middle, details on bottom
chart_area = st.container()
options_area = st.container()
details_area = st.container()

# --- Options (rendered in middle visually, but defined first for values) ---
with options_area:
    with st.form("params_form"):
        left, right = st.columns(2)
        with left:
            current_age = st.number_input("Age", min_value=18, max_value=80, value=30)
            retirement_age = st.number_input("Retire", min_value=19, max_value=90, value=50)
            life_expectancy = st.number_input("Until", min_value=20, max_value=120, value=90)
        with right:
            savings_raw = st.text_input("Savings", value="$2,400,000", key="savings")
            contribution_raw = st.text_input("Contrib / yr", value="$90,000", key="contribution")
            spending_raw = st.text_input("Spend / yr", value="$400,000", key="spending")

        with st.expander("Advanced"):
            st.caption("Accumulation Phase")
            a1, a2 = st.columns(2)
            accumulation_return = a1.slider("Return %", 0.0, 20.0, 9.0, 0.5, key="accum_ret")
            accumulation_std = a2.slider("Std Dev %", 0.0, 40.0, 15.0, 0.5, key="accum_std")

            st.caption("Retirement Phase")
            r1, r2 = st.columns(2)
            retirement_return = r1.slider("Return %", 0.0, 20.0, 6.0, 0.5, key="ret_ret")
            retirement_std = r2.slider("Std Dev %", 0.0, 40.0, 3.0, 0.5, key="ret_std")

            o1, o2 = st.columns(2)
            inflation_rate = o1.slider("Inflation %", 0.0, 10.0, 3.0, 0.25)
            num_simulations = o2.select_slider("Sims", [100, 500, 1000, 5000, 10000], 1000)

        st.form_submit_button("Run Simulation", type="primary", use_container_width=True)


def parse_dollar(raw, default):
    try:
        return int(raw.replace("$", "").replace(",", "").strip())
    except ValueError:
        return default


# --- Parse inputs ---
current_savings = parse_dollar(savings_raw, 2_400_000)
annual_contribution = parse_dollar(contribution_raw, 90_000)
annual_spending = parse_dollar(spending_raw, 400_000)

# --- Chart (rendered first visually) ---
with chart_area:
    if retirement_age <= current_age:
        st.error("Retirement age must be greater than current age.")
    elif life_expectancy <= retirement_age:
        st.error("Life expectancy must be greater than retirement age.")
    else:
        params = {
            "current_age": current_age,
            "retirement_age": retirement_age,
            "life_expectancy": life_expectancy,
            "current_savings": current_savings,
            "annual_contribution": annual_contribution,
            "annual_spending": annual_spending,
            "accumulation_return": accumulation_return / 100,
            "accumulation_std": accumulation_std / 100,
            "retirement_return": retirement_return / 100,
            "retirement_std": retirement_std / 100,
            "inflation_rate": inflation_rate / 100,
        }

        results = run_simulation(params, num_simulations)
        stats = calculate_statistics(results, params)

        rate = stats["success_rate"]
        color = "green" if rate >= 80 else "orange" if rate >= 50 else "red"
        icon = "✅" if rate >= 80 else "⚠️" if rate >= 50 else "❌"

        st.markdown(
            f"<p class='success-heading' style='color:{color}; margin:0; font-size:1.8rem; font-weight:700'>"
            f"{icon} {rate:.1f}% Success Rate</p>",
            unsafe_allow_html=True,
        )

        # --- Chart ---
        ages = list(range(current_age, life_expectancy + 1))
        p = stats["percentiles"]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ages + ages[::-1],
            y=list(p["p90"]) + list(p["p10"][::-1]),
            fill="toself", fillcolor="rgba(99, 110, 250, 0.15)",
            line=dict(color="rgba(255,255,255,0)"), name="10th–90th",
        ))
        fig.add_trace(go.Scatter(
            x=ages + ages[::-1],
            y=list(p["p75"]) + list(p["p25"][::-1]),
            fill="toself", fillcolor="rgba(99, 110, 250, 0.3)",
            line=dict(color="rgba(255,255,255,0)"), name="25th–75th",
        ))
        fig.add_trace(go.Scatter(
            x=ages, y=list(p["p50"]), mode="lines",
            line=dict(color="rgb(99, 110, 250)", width=3), name="Median",
        ))
        fig.add_vline(x=retirement_age, line_dash="dash", line_color="gray",
                      annotation_text="Retire", annotation_position="top right")
        fig.update_layout(
            xaxis_title="Age", yaxis_title="Portfolio ($)", yaxis_tickformat="$,.0s",
            hovermode="x unified", height=320,
            margin=dict(l=0, r=0, t=25, b=35),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", font=dict(size=10)),
        )
        st.plotly_chart(fig, use_container_width=True)

# --- Detailed Results (rendered last visually) ---
with details_area:
    if retirement_age > current_age and life_expectancy > retirement_age:
        col1, col2, col3 = st.columns(3)
        col1.metric("At Retirement", f"${stats['retirement_median']:,.0f}")
        col2.metric("Best Case", f"${stats['final_best']:,.0f}")
        col3.metric("Worst Case", f"${stats['final_worst']:,.0f}")

        with st.expander("Distribution at Retirement"):
            fig2 = go.Figure()
            fig2.add_trace(go.Histogram(
                x=stats["retirement_values"], nbinsx=50,
                marker_color="rgb(99, 110, 250)", opacity=0.75,
            ))
            fig2.update_layout(
                xaxis_title="Portfolio ($)", xaxis_tickformat="$,.0s",
                yaxis_title="Count", height=250,
                margin=dict(l=0, r=0, t=10, b=40),
            )
            st.plotly_chart(fig2, use_container_width=True)

        with st.expander("Detailed Results Table"):
            runs = stats["representative_runs"]
            df = pd.DataFrame({
                "Age": ages,
                "10th Pctl": runs["p10"],
                "25th Pctl": runs["p25"],
                "Median": runs["p50"],
                "75th Pctl": runs["p75"],
                "90th Pctl": runs["p90"],
            })
            df.set_index("Age", inplace=True)
            st.dataframe(df.style.format("${:,.0f}"), use_container_width=True, height=400)
