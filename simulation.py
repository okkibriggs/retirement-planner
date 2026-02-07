import numpy as np


def run_simulation(params, num_simulations=1000):
    """Run Monte Carlo retirement simulations.

    Returns a 2D numpy array of shape (num_simulations, total_years + 1)
    representing portfolio value at each age from current_age to life_expectancy.
    """
    current_age = params["current_age"]
    retirement_age = params["retirement_age"]
    life_expectancy = params["life_expectancy"]
    current_savings = params["current_savings"]
    annual_contribution = params["annual_contribution"]
    accumulation_return = params["accumulation_return"]
    accumulation_std = params["accumulation_std"]
    retirement_return = params["retirement_return"]
    retirement_std = params["retirement_std"]
    inflation_rate = params["inflation_rate"]
    annual_spending = params["annual_spending"]

    total_years = life_expectancy - current_age
    accumulation_years = retirement_age - current_age
    distribution_years = total_years - accumulation_years
    results = np.zeros((num_simulations, total_years + 1))
    results[:, 0] = current_savings

    # Generate random returns for each phase separately
    accum_returns = np.random.normal(accumulation_return, accumulation_std, (num_simulations, accumulation_years))
    retire_returns = np.random.normal(retirement_return, retirement_std, (num_simulations, distribution_years))
    annual_returns = np.concatenate([accum_returns, retire_returns], axis=1)

    for year in range(1, total_years + 1):
        growth = results[:, year - 1] * (1 + annual_returns[:, year - 1])

        if year <= accumulation_years:
            # Accumulation phase: add contributions
            results[:, year] = growth + annual_contribution
        else:
            # Distribution phase: subtract inflation-adjusted spending
            years_in_retirement = year - accumulation_years - 1
            adjusted_spending = annual_spending * (1 + inflation_rate) ** years_in_retirement
            results[:, year] = growth - adjusted_spending

        # Floor at zero — can't have negative portfolio
        results[:, year] = np.maximum(results[:, year], 0)

    return results


def calculate_statistics(results, params):
    """Calculate summary statistics from simulation results."""
    total_years = results.shape[1] - 1
    retirement_year = params["retirement_age"] - params["current_age"]

    # Success = portfolio > 0 at end of life expectancy
    final_values = results[:, -1]
    success_rate = np.mean(final_values > 0) * 100

    # Percentile trajectories
    percentiles = {
        "p10": np.percentile(results, 10, axis=0),
        "p25": np.percentile(results, 25, axis=0),
        "p50": np.percentile(results, 50, axis=0),
        "p75": np.percentile(results, 75, axis=0),
        "p90": np.percentile(results, 90, axis=0),
    }

    # Actual runs closest to each percentile of final values
    sorted_indices = np.argsort(final_values)
    n = len(final_values)
    representative_runs = {}
    for label, pct in [("p10", 10), ("p25", 25), ("p50", 50), ("p75", 75), ("p90", 90)]:
        idx = sorted_indices[int(n * pct / 100)]
        representative_runs[label] = results[idx]

    # Portfolio value at retirement
    retirement_values = results[:, retirement_year]

    return {
        "success_rate": success_rate,
        "percentiles": percentiles,
        "representative_runs": representative_runs,
        "final_median": np.median(final_values),
        "final_worst": np.min(final_values),
        "final_best": np.max(final_values),
        "retirement_values": retirement_values,
        "retirement_median": np.median(retirement_values),
    }
