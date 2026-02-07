import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from simulation import run_simulation, calculate_statistics

st.set_page_config(page_title="Retirement Planner", page_icon="📈")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 700px; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem; }
    [data-testid="stMetricValue"] { font-size: 1.3rem; }
</style>
""", unsafe_allow_html=True)

st.title("Retirement Planner")
st.caption("Monte Carlo simulation to estimate if your savings will last through retirement.")

# --- Inputs in main area ---
with st.form("params_form"):
    st.subheader("Your Information")
    c1, c2, c3 = st.columns(3)
    current_age = c1.number_input("Current Age", min_value=18, max_value=80, value=30)
    retirement_age = c2.number_input("Retirement Age", min_value=19, max_value=90, value=50)
    life_expectancy = c3.number_input("Life Expectancy", min_value=20, max_value=120, value=90)

    st.subheader("Finances")
    savings_raw = st.text_input("Current Savings", value="$2,400,000", key="savings")
    f1, f2 = st.columns(2)
    contribution_raw = f1.text_input("Annual Contribution", value="$90,000", key="contribution")
    spending_raw = f2.text_input("Retirement Spending / yr", value="$400,000", key="spending")

    with st.expander("Market Assumptions"):
        st.markdown("**Accumulation Phase**")
        a1, a2 = st.columns(2)
        accumulation_return = a1.slider("Return (%)", 0.0, 20.0, 9.0, 0.5, key="accum_ret")
        accumulation_std = a2.slider("Std Dev (%)", 0.0, 40.0, 15.0, 0.5, key="accum_std")

        st.markdown("**Retirement Phase**")
        r1, r2 = st.columns(2)
        retirement_return = r1.slider("Return (%)", 0.0, 20.0, 6.0, 0.5, key="ret_ret")
        retirement_std = r2.slider("Std Dev (%)", 0.0, 40.0, 3.0, 0.5, key="ret_std")

        st.markdown("**Other**")
        o1, o2 = st.columns(2)
        inflation_rate = o1.slider("Inflation (%)", 0.0, 10.0, 3.0, 0.25)
        num_simulations = o2.select_slider("Simulations", [100, 500, 1000, 5000, 10000], 1000)

    submitted = st.form_submit_button("Run Simulation", type="primary", use_container_width=True)


def parse_dollar(raw, default):
    try:
        return int(raw.replace("$", "").replace(",", "").strip())
    except ValueError:
        st.error(f"Invalid dollar value: {raw}")
        return default


if submitted:
    current_savings = parse_dollar(savings_raw, 2_400_000)
    annual_contribution = parse_dollar(contribution_raw, 90_000)
    annual_spending = parse_dollar(spending_raw, 400_000)

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

        with st.spinner("Running simulations..."):
            results = run_simulation(params, num_simulations)
            stats = calculate_statistics(results, params)

        st.divider()

        # --- Success rate ---
        rate = stats["success_rate"]
        if rate >= 80:
            color = "green"
        elif rate >= 50:
            color = "orange"
        else:
            color = "red"

        st.markdown(
            f"<h2 style='color:{color}; margin-bottom:0'>{'✅' if rate >= 80 else '⚠️' if rate >= 50 else '❌'} "
            f"{rate:.1f}% Success Rate</h2>",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        col1.metric("Median at Retirement", f"${stats['retirement_median']:,.0f}")
        col2.metric("Median Final Portfolio", f"${stats['final_median']:,.0f}")

        # --- Portfolio trajectory chart ---
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
            hovermode="x unified", height=350,
            margin=dict(l=0, r=0, t=30, b=40),
            legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center", font=dict(size=10)),
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Summary stats ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Best Case", f"${stats['final_best']:,.0f}")
        col2.metric("Median", f"${stats['final_median']:,.0f}")
        col3.metric("Worst Case", f"${stats['final_worst']:,.0f}")

        # --- Histogram ---
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

        # --- Detailed table ---
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

else:
    st.info("Press **Enter** or click **Run Simulation** to see results.")
