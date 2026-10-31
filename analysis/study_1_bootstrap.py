import numpy as np
import pandas as pd

"""
  Bootstrap confidence intervals for the gap decomposition in study_1.py.

  Does NOT call the OpenAI API. Reuses the correctness labels already saved
  in data/study1/saved_results.csv (condition #2) together with the static
  condition #1/#3/#4 columns. Primary estimates give each of the ten scenarios
  equal weight. Uncertainty is estimated by within-scenario resampling for the
  direct condition and participant-clustered resampling for patient conditions.

  Run from the healthcare-llm-eval-gap directory:
      python analysis/study_1_bootstrap.py
"""

N_BOOT = 5000
RNG = np.random.default_rng(0)


def ci(vals, alpha=0.05):
    lo, hi = np.percentile(vals, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return lo, hi


def scenario_balanced_mean(df, cols, scenario_col='scenario_id'):
    """Mean of scenario-level means, giving each scenario equal weight."""
    return df.groupby(scenario_col, sort=True)[cols].mean().mean().to_numpy()


def bootstrap_within_scenario(df, cols, scenario_col='scenario_id',
                              n_boot=N_BOOT):
    """Resample rows within each scenario and average scenario means equally."""
    scenarios = np.sort(df[scenario_col].unique())
    out = np.zeros((n_boot, len(cols)))

    for scenario in scenarios:
        vals = df.loc[df[scenario_col] == scenario, cols].to_numpy(dtype=float)
        idx = RNG.integers(0, len(vals), size=(n_boot, len(vals)))
        out += vals[idx].mean(axis=1)

    return {col: out[:, j] / len(scenarios) for j, col in enumerate(cols)}


def bootstrap_participant_clustered(df, cols, cluster_col='participant_id',
                                    scenario_col='scenario_id',
                                    n_boot=N_BOOT):
    """Resample participants, keeping all of each participant's rows together.

    Within each replicate, compute scenario means and average them equally.
    The p2/p3/p4 columns remain paired within each id because the same sampled
    rows are used for every column. The returned paired changes are recomputed
    from within-id differences within each scenario.
    """
    clusters = df[cluster_col].drop_duplicates().to_numpy()
    scenarios = np.sort(df[scenario_col].unique())
    index = pd.MultiIndex.from_product([clusters, scenarios],
                                       names=[cluster_col, scenario_col])
    grouped = df.groupby([cluster_col, scenario_col], sort=False)
    cluster_sums = grouped[cols].sum().reindex(index, fill_value=0)
    cluster_counts = grouped.size().reindex(index, fill_value=0)
    cluster_sums = cluster_sums.to_numpy(dtype=float).reshape(
        len(clusters), len(scenarios), len(cols)
    )
    cluster_counts = cluster_counts.to_numpy(dtype=float).reshape(
        len(clusters), len(scenarios)
    )

    n_clusters = len(clusters)
    cluster_idx = RNG.integers(0, n_clusters, size=(n_boot, n_clusters))
    sums = cluster_sums[cluster_idx].sum(axis=1)
    counts = cluster_counts[cluster_idx].sum(axis=1)
    scenario_means = sums / counts[:, :, None]
    means = scenario_means.mean(axis=1)

    out = {col: means[:, j] for j, col in enumerate(cols)}
    for left, right in [('p2', 'p3'), ('p3', 'p4'), ('p2', 'p4')]:
        left_idx, right_idx = cols.index(left), cols.index(right)
        differences = (sums[:, :, right_idx] - sums[:, :, left_idx]) / counts
        out[f'delta_{left}_{right}'] = differences.mean(axis=1)
    return out


# ---------------------------------------------------------------------
# Load exactly the same source data as study_1.py, but never call the API
# ---------------------------------------------------------------------

# #1: Expert query, single-turn
direct = pd.read_csv('data/study1/direct_trials_condition.csv', index_col=0)
gpt_direct = direct[direct['model'] == 'GPT 4o']
gpt_direct['differential_correct'] = gpt_direct[
    'differential_correct'
].astype(float)

# #2/#3/#4: paired on the same 600 patient-scenario ids
ex = pd.read_csv('data/study1/clean_examples.csv', index_col=0)
gpt4o_ex = ex[ex['treatment_id'] == 2].copy()

saved = pd.read_csv('data/study1/saved_results.csv', index_col=0)  # p2, already computed
prescored = pd.read_csv('data/study1/clean_prescored.csv')

merged = gpt4o_ex.merge(saved[['id', 'correct']], on='id') \
                 .merge(prescored[['id', 'differential_correct_bot', 'differential_correct']], on='id')

merged = merged.rename(columns={
    'correct': 'p2',
    'differential_correct_bot': 'p3',
    'differential_correct': 'p4',
})
merged[['p2', 'p3', 'p4']] = merged[['p2', 'p3', 'p4']].astype(float)

point_values = {
    'p1': gpt_direct.rename(columns={'differential_correct': 'p1'}),
    'p2': merged[['scenario_id', 'p2']],
    'p3': merged[['scenario_id', 'p3']],
    'p4': merged[['scenario_id', 'p4']],
}
point = {
    key: scenario_balanced_mean(value, [key])[0]
    for key, value in point_values.items()
}

# ---------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------

# p1 comes from a separate, unpaired sample (expert-written benchmark rows),
# so it is resampled independently within each scenario.
p1_boot = bootstrap_within_scenario(
    gpt_direct.rename(columns={'differential_correct': 'p1'}), ['p1']
)['p1']

# p2/p3/p4 are computed on the same rows, so they are resampled together
# (paired). Participant-clustered resampling also keeps the two cases from a
# participant together, accounting for dependence across that participant's
# separate patient-scenario interactions.
paired_boot = bootstrap_participant_clustered(
    merged, ['p2', 'p3', 'p4'], cluster_col='participant_id'
)
p2_boot, p3_boot, p4_boot = paired_boot['p2'], paired_boot['p3'], paired_boot['p4']

gaps = {
    'Total gap (#1 -> #4)':            p1_boot - p4_boot,
    'Query distribution (#1 -> #2)':   p1_boot - p2_boot,
    'First turn - multi-turn (#2->#3)': -paired_boot['delta_p2_p3'],
    'Outcome / uptake (#3 -> #4)':      -paired_boot['delta_p3_p4'],
    'Paired gap (#2 -> #4)':             -paired_boot['delta_p2_p4'],
    'Task total (#1 -> #3)':            p1_boot - p3_boot,
}

point_gaps = {
    'Total gap (#1 -> #4)':            point['p1'] - point['p4'],
    'Query distribution (#1 -> #2)':   point['p1'] - point['p2'],
    'First turn - multi-turn (#2->#3)': point['p2'] - point['p3'],
    'Outcome / uptake (#3 -> #4)':      point['p3'] - point['p4'],
    'Paired gap (#2 -> #4)':             point['p2'] - point['p4'],
    'Task total (#1 -> #3)':            point['p1'] - point['p3'],
}

# ---------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------

print(f"── Bootstrapped point estimates (n_boot={N_BOOT}) ─────────────────────")
for k, boot in [('p1', p1_boot), ('p2', p2_boot), ('p3', p3_boot), ('p4', p4_boot)]:
    lo, hi = ci(boot)
    print(f"  {k}: {point[k]:.3f}  [95% CI {lo:.3f}, {hi:.3f}]")

print()
print("── Gap decomposition with 95% bootstrap CIs ────────────────────────────")
for name, boot in gaps.items():
    lo, hi = ci(boot)
    print(f"  {name:38s} {point_gaps[name]:+.3f}  [95% CI {lo:+.3f}, {hi:+.3f}]")

print()
print("── Is each gap distinguishable from zero? ──────────────────────────────")
for name, boot in gaps.items():
    lo, hi = ci(boot)
    crosses_zero = lo <= 0 <= hi
    print(f"  {name:38s} {'CI crosses zero (not distinguishable)' if crosses_zero else 'CI excludes zero'}")
