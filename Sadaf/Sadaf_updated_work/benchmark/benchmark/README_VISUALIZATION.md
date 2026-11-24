# External benchmark, held-out 2025

Section 06 uses the original paired comparison outputs in `benchmark/benchmark_comparison_2025.csv` and `benchmark/nfl4th_results_2025.csv`, and the browser-readable data file `static/data/benchmark_2025.json` generated from the comparison CSV. No model is retrained and no numbers are fabricated.

Run `python app.py` from the project root, then open `http://127.0.0.1:5001`. Go to Section 06 and filter the real 2025 scenarios. The visualizations are generated with D3. This section works offline except for the existing D3 CDN script requirement.

The reference sample contains 90 fourth-down plays (30 of each ACTUAL coaching choice). The pairwise comparison is only over actions available in nfl4th's output, with 63 complete three-action cases (27 cases with missing `punt_wp`). Recommendation agreement is 64/90 = 71.1% over shared actions, 43/63 = 68.3% over complete three-action cases. `go_wp`, `fg_wp`, `punt_wp` are nfl4th estimates and `our_go_wp`, `our_fg_wp`, `our_punt_wp` are the user's engine estimates from the benchmark run. This measures agreement and numerical differences, not optimality or causal accuracy. For derived comparisons, see the raw benchmark CSV.

Filter-specific confusion matrices use ONLY cases with all three actions available. Close vs clear categorization (< 2 percentage points) is similarly limited to three-action cases. Absolute WP difference bars use all rows with available values for that action.

The punt outcomes CSV is not in this packaged baseline because it was not uploaded here. Copy your existing `data/punt_outcomes.csv` into this project's `data/` folder before using the live punt engine. The benchmark visualizations themselves reflect the exported comparison values, independently of that optional dataset.
