import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go

from simulation import run_simulation, calculate_statistics

st.set_page_config(page_title="Retirement Planner", page_icon="📈")

components.html("""
<script>
    var head = parent.document.head;

    // SEO meta tags
    var metas = [
        {name: 'description', content: 'Free Monte Carlo retirement calculator. Simulate thousands of market scenarios to find your chance of a successful retirement.'},
        {name: 'keywords', content: 'retirement calculator, FIRE calculator, Monte Carlo simulation, retirement planning, can I retire, early retirement'},
        {name: 'author', content: 'Retirement Planner'},
        {property: 'og:title', content: 'Retirement Planner - Monte Carlo Simulator'},
        {property: 'og:description', content: 'Run thousands of simulations to see if your retirement plan will succeed. Free, fast, and no signup required.'},
        {property: 'og:type', content: 'website'},
        {name: 'twitter:card', content: 'summary'},
        {name: 'twitter:title', content: 'Retirement Planner - Monte Carlo Simulator'},
        {name: 'twitter:description', content: 'Run thousands of simulations to see if your retirement plan will succeed.'},
        {name: 'google-adsense-account', content: 'ca-pub-7451296231922651'}
    ];
    metas.forEach(function(m) {
        var sel = m.name ? 'meta[name="'+m.name+'"]' : 'meta[property="'+m.property+'"]';
        if (!head.querySelector(sel)) {
            var tag = parent.document.createElement('meta');
            if (m.name) tag.name = m.name;
            if (m.property) tag.setAttribute('property', m.property);
            tag.content = m.content;
            head.appendChild(tag);
        }
    });

    // AdSense script
    if (!head.querySelector('script[src*="adsbygoogle"]')) {
        var script = parent.document.createElement('script');
        script.async = true;
        script.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7451296231922651';
        script.crossOrigin = 'anonymous';
        head.appendChild(script);
    }
</script>
""", height=0)

st.markdown("""
<style>
    header[data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 700px; margin: 0 auto; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem; }
    [data-testid="stMetricValue"] { font-size: 1.3rem; }
    /* Compact inputs */
    .stTextInput, .stNumberInput { margin-bottom: -0.5rem; }
    /* Force columns side by side on mobile */
    [data-testid="stHorizontalBlock"] { flex-wrap: nowrap; gap: 0.5rem; }
    @media (max-width: 768px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 0.5rem; }
        .success-heading { font-size: 1.3rem !important; }
        [data-testid="stMetricValue"] { font-size: 1rem; }
        [data-testid="stMetricLabel"] { font-size: 0.7rem; }
        [data-testid="stHorizontalBlock"] > div { flex: 1 1 50%; min-width: 0; }
    }
</style>
""", unsafe_allow_html=True)

# Reserve layout slots: chart on top, options in middle, details on bottom
chart_area = st.container()
options_area = st.container()
details_area = st.container()

# --- Options (rendered in middle visually, but defined first for values) ---
with options_area:
    left, right = st.columns(2)
    with left:
        age_raw = st.text_input("Age", value="30", key="age")
        retire_raw = st.text_input("Retire", value="50", key="retire")
        until_raw = st.text_input("Until", value="90", key="until")
    with right:
        savings_raw = st.text_input("Savings", value="$2,400,000", key="savings")
        contribution_raw = st.text_input("Contribution / yr", value="$90,000", key="contribution")
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

    st.button("Run Simulation", type="primary", use_container_width=True)


def parse_int(raw, default):
    try:
        return int(raw.replace("$", "").replace(",", "").strip())
    except ValueError:
        return default


# --- Parse inputs ---
current_age = parse_int(age_raw, 30)
retirement_age = parse_int(retire_raw, 50)
life_expectancy = parse_int(until_raw, 90)
current_savings = parse_int(savings_raw, 2_400_000)
annual_contribution = parse_int(contribution_raw, 90_000)
annual_spending = parse_int(spending_raw, 400_000)

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
            hovermode=False, height=260,
            margin=dict(l=0, r=0, t=25, b=35),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", font=dict(size=10)),
            xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True),
            dragmode=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

# --- Detailed Results (rendered last visually) ---
with details_area:
    if retirement_age > current_age and life_expectancy > retirement_age:
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

components.html("""
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7451296231922651"
     crossorigin="anonymous"></script>
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-7451296231922651"
     data-ad-slot="auto"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({});
</script>
""", height=100)
