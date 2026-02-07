import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from simulation import run_simulation, calculate_statistics

st.set_page_config(page_title="Retirement Planner", page_icon="📈", layout="wide")

st.title("Retirement Planning — Monte Carlo Simulator")
st.markdown(
    "Estimate the probability of your savings lasting through retirement "
    "using Monte Carlo simulations with randomized market returns."
)

# --- Sidebar form (Enter key submits) ---
with st.sidebar.form("params_form"):
    st.header("Your Information")

    current_age = st.number_input("Current Age", min_value=18, max_value=80, value=30)
    retirement_age = st.number_input(
        "Retirement Age", min_value=19, max_value=90, value=50
    )
    life_expectancy = st.number_input(
        "Life Expectancy", min_value=20, max_value=120, value=90
    )

    st.header("Finances")

    savings_raw = st.text_input("Current Savings", value="$2,400,000", key="savings")
    contribution_raw = st.text_input("Annual Contribution", value="$90,000", key="contribution")
    spending_raw = st.text_input("Annual Retirement Spending", value="$400,000", key="spending")

    st.header("Accumulation Phase Returns")

    accumulation_return = st.slider(
        "Expected Return (%)", min_value=0.0, max_value=20.0, value=9.0, step=0.5, key="accum_ret"
    )
    accumulation_std = st.slider(
        "Return Std Deviation (%)", min_value=0.0, max_value=40.0, value=15.0, step=0.5, key="accum_std"
    )

    st.header("Retirement Phase Returns")

    retirement_return = st.slider(
        "Expected Return (%)", min_value=0.0, max_value=20.0, value=6.0, step=0.5, key="ret_ret"
    )
    retirement_std = st.slider(
        "Return Std Deviation (%)", min_value=0.0, max_value=40.0, value=3.0, step=0.5, key="ret_std"
    )

    st.header("Inflation")

    inflation_rate = st.slider(
        "Inflation Rate (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.25
    )

    st.header("Simulation")

    num_simulations = st.select_slider(
        "Number of Simulations", options=[100, 500, 1000, 5000, 10000], value=1000
    )

    submitted = st.form_submit_button("Run Simulation", type="primary", use_container_width=True)


def parse_dollar(raw, default):
    """Parse a dollar string like '$2,400,000' into an int."""
    try:
        return int(raw.replace("$", "").replace(",", "").strip())
    except ValueError:
        st.sidebar.error(f"Invalid dollar value: {raw}")
        return default


# --- Run simulation ---
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

        # --- Success rate ---
        rate = stats["success_rate"]
        if rate >= 80:
            color = "green"
        elif rate >= 50:
            color = "orange"
        else:
            color = "red"

        col1, col2, col3 = st.columns(3)
        col1.metric("Success Rate", f"{rate:.1f}%")
        col2.metric("Median Final Portfolio", f"${stats['final_median']:,.0f}")
        col3.metric("Median at Retirement", f"${stats['retirement_median']:,.0f}")

        st.markdown(
            f"<h3 style='color:{color}'>{'✅' if rate >= 80 else '⚠️' if rate >= 50 else '❌'} "
            f"{rate:.1f}% of simulations succeeded</h3>",
            unsafe_allow_html=True,
        )

        # --- Portfolio trajectory chart ---
        st.subheader("Portfolio Value Over Time")

        ages = list(range(current_age, life_expectancy + 1))
        p = stats["percentiles"]

        fig = go.Figure()

        # Shaded confidence band (10th–90th)
        fig.add_trace(go.Scatter(
            x=ages + ages[::-1],
            y=list(p["p90"]) + list(p["p10"][::-1]),
            fill="toself",
            fillcolor="rgba(99, 110, 250, 0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            name="10th–90th percentile",
        ))

        # 25th–75th band
        fig.add_trace(go.Scatter(
            x=ages + ages[::-1],
            y=list(p["p75"]) + list(p["p25"][::-1]),
            fill="toself",
            fillcolor="rgba(99, 110, 250, 0.3)",
            line=dict(color="rgba(255,255,255,0)"),
            name="25th–75th percentile",
        ))

        # Median line
        fig.add_trace(go.Scatter(
            x=ages, y=list(p["p50"]),
            mode="lines",
            line=dict(color="rgb(99, 110, 250)", width=3),
            name="Median",
        ))

        # Retirement age marker
        fig.add_vline(x=retirement_age, line_dash="dash", line_color="gray",
                      annotation_text="Retirement", annotation_position="top right")

        fig.update_layout(
            xaxis_title="Age",
            yaxis_title="Portfolio Value ($)",
            yaxis_tickformat="$,.0f",
            hovermode="x unified",
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

        # --- Histogram of portfolio values at retirement ---
        st.subheader("Distribution of Portfolio Value at Retirement")

        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=stats["retirement_values"],
            nbinsx=50,
            marker_color="rgb(99, 110, 250)",
            opacity=0.75,
        ))
        fig2.update_layout(
            xaxis_title="Portfolio Value ($)",
            xaxis_tickformat="$,.0f",
            yaxis_title="Number of Simulations",
            height=400,
        )

        st.plotly_chart(fig2, use_container_width=True)

        # --- Summary table ---
        st.subheader("Summary Statistics")

        col1, col2, col3 = st.columns(3)
        col1.metric("Best Case (Final)", f"${stats['final_best']:,.0f}")
        col2.metric("Median (Final)", f"${stats['final_median']:,.0f}")
        col3.metric("Worst Case (Final)", f"${stats['final_worst']:,.0f}")

        # --- Percentile table by age (actual simulation runs) ---
        with st.expander("View Detailed Results Table"):
            ages = list(range(current_age, life_expectancy + 1))
            runs = stats["representative_runs"]
            df = pd.DataFrame({
                "Age": ages,
                "10th Percentile Run": runs["p10"],
                "25th Percentile Run": runs["p25"],
                "Median Run": runs["p50"],
                "75th Percentile Run": runs["p75"],
                "90th Percentile Run": runs["p90"],
            })
            df.set_index("Age", inplace=True)
            st.dataframe(
                df.style.format("${:,.0f}"),
                use_container_width=True,
                height=400,
            )

else:
    st.info("Adjust your parameters in the sidebar and press **Enter** to see results.")
