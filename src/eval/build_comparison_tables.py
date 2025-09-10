import argparse
import os

import pandas as pd

from eval.results_access.mid_survey_results import MidSurveyResults
from eval.results_access.simulation_results import SimulationResults


def build_comparison_tables(mid: MidSurveyResults, sim_data: dict, experiments: list):
    """
    Build comparison tables for:
      1) Overall modality split
      2) Route lengths distribution
      3) Route durations distribution
      4) Route lengths by modality
      5) Route durations by modality
      6) Possible‐routes counts (for simulations)
    Returns a dict of DataFrames.
    """
    modes = ["By foot", "Bicycle", "MIT", "Public Transport"]
    length_cats = ["<0.5 km", "0.5-1 km", "1-2 km", "2-5 km",
                   "5-10 km", "10-20 km", "20-50 km", "50-100 km", ">100 km"]
    dur_cats = ["<5 min", "5-10 min", "10-15 min", "15-20 min",
                "20-30 min", "30-45 min", "45-60 min", ">60 min"]

    # ─── Baseline (MiD) ────────────────────────────────────────────────────────
    mid_mod = mid.get_modality_split()
    modality_data = {m: {"MiD (%)": mid_mod.get(m, 0.0)} for m in modes}

    mid_len = mid.get_route_lengths()
    length_data = {cat: {"MiD (%)": mid_len.get(cat, 0.0)} for cat in length_cats}

    mid_dur = mid.get_route_durations()
    duration_data = {cat: {"MiD (%)": mid_dur.get(cat, 0.0)} for cat in dur_cats}

    # unpack the tuple-return and rebuild the “by modality” tables
    mid_len_dict, _, _ = mid.get_route_lengths_by_modalities()
    mid_len_by_mod_df = pd.DataFrame(mid_len_dict, index=length_cats).T
    mid_len_by_mod = (
        mid_len_by_mod_df
        .stack()
        .rename("MiD (%)")
        .reset_index()
        .rename(columns={"level_0": "Mode", "level_1": "Length"})
    )

    mid_dur_dict, _, _ = mid.get_route_durations_by_modalities()
    mid_dur_by_mod_df = pd.DataFrame(mid_dur_dict, index=dur_cats).T
    mid_dur_by_mod = (
        mid_dur_by_mod_df
        .stack()
        .rename("MiD (%)")
        .reset_index()
        .rename(columns={"level_0": "Mode", "level_1": "Duration"})
    )

    # prepare to collect simulation tables
    sim_len_by_mod_flat = []
    sim_dur_by_mod_flat = []
    upset_counts = {}

    for exp_label in experiments:
        sim = sim_data[exp_label]

        # 1) modality split
        sim_mod = sim.calculate_modality_percent()
        sim_mod = SimulationResults.standardize_keys(sim_mod)
        for m in modes:
            sim_pct = sim_mod.get(m, 0.0)
            delta = sim_pct - modality_data[m]["MiD (%)"]
            modality_data[m][f"{exp_label} (Sim %)"] = sim_pct
            modality_data[m][f"{exp_label} (Δ)"] = delta

        # 2) route‐length distribution
        sim_len = sim.get_route_lengths()
        for cat in length_cats:
            sim_pct = sim_len.get(cat, 0.0)
            delta = sim_pct - length_data[cat]["MiD (%)"]
            length_data[cat][f"{exp_label} (Sim %)"] = sim_pct
            length_data[cat][f"{exp_label} (Δ)"] = delta

        # 3) route‐duration distribution
        sim_dur = sim.get_route_durations()
        for cat in dur_cats:
            sim_pct = sim_dur.get(cat, 0.0)
            delta = sim_pct - duration_data[cat]["MiD (%)"]
            duration_data[cat][f"{exp_label} (Sim %)"] = sim_pct
            duration_data[cat][f"{exp_label} (Δ)"] = delta

        # 4) lengths by modality
        slm_dict, _, _ = sim.get_route_lengths_by_modalities()
        sim_len_df = pd.DataFrame(slm_dict, index=length_cats).T
        df_slm = (
            sim_len_df
            .stack()
            .rename(f"{exp_label} (Sim %)")
            .reset_index()
            .rename(columns={"level_0": "Mode", "level_1": "Length"})
        )
        df_slm = df_slm.merge(mid_len_by_mod, on=["Mode", "Length"])
        df_slm[f"{exp_label} (Δ)"] = (
                df_slm[f"{exp_label} (Sim %)"] - df_slm["MiD (%)"]
        )
        sim_len_by_mod_flat.append(df_slm)

        # 5) durations by modality
        sdm_dict, _, _ = sim.get_route_durations_by_modalities()
        sim_dur_df = pd.DataFrame(sdm_dict, index=dur_cats).T
        df_sdm = (
            sim_dur_df
            .stack()
            .rename(f"{exp_label} (Sim %)")
            .reset_index()
            .rename(columns={"level_0": "Mode", "level_1": "Duration"})
        )
        df_sdm = df_sdm.merge(mid_dur_by_mod, on=["Mode", "Duration"])
        df_sdm[f"{exp_label} (Δ)"] = (
                df_sdm[f"{exp_label} (Sim %)"] - df_sdm["MiD (%)"]
        )
        sim_dur_by_mod_flat.append(df_sdm)

        # 6) possible‐routes upset counts
        upset_counts[exp_label] = sim.count_possible_routes()

    # ─── Assemble final DataFrames ────────────────────────────────────────────
    modality_df = pd.DataFrame.from_dict(modality_data, orient='index')
    length_df = pd.DataFrame.from_dict(length_data, orient='index')
    duration_df = pd.DataFrame.from_dict(duration_data, orient='index')

    lengths_by_modality = pd.concat(sim_len_by_mod_flat, ignore_index=True).pivot_table(
        index=["Mode", "Length"],
        values=["MiD (%)"] +
               [f"{e} (Sim %)" for e in experiments] +
               [f"{e} (Δ)" for e in experiments]
    )

    durations_by_modality = pd.concat(sim_dur_by_mod_flat, ignore_index=True).pivot_table(
        index=["Mode", "Duration"],
        values=["MiD (%)"] +
               [f"{e} (Sim %)" for e in experiments] +
               [f"{e} (Δ)" for e in experiments]
    )

    upset_df = (
        pd.DataFrame.from_dict(upset_counts, orient='index')
        .fillna(0)
        .astype(int)
    )

    return {
        "modality_overall": modality_df,
        "route_length_dist": length_df,
        "route_duration_dist": duration_df,
        "lengths_by_modality": lengths_by_modality,
        "durations_by_modality": durations_by_modality,
        "upset_counts": upset_df,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build and log comparison tables between survey and simulation results."
    )
    parser.add_argument(
        '--mid-path',
        default='../../data/census/B1_Standard-Datensatzpaket/CSV',
        help='Path to the folder containing MID survey CSV files'
    )
    parser.add_argument(
        '--bland-code',
        type=int,
        default=11,
        help='Bland code to filter survey results'
    )
    parser.add_argument(
        '--sim-base-folder',
        default='../../results/experiments',
        help='Base folder under which experiment subfolders live'
    )
    parser.add_argument(
        '--experiments',
        nargs='+',
        default=['Exp1a_Default', 'Exp1b_OTP'],
        help='Labels of the experiments (space-separated list)'
    )
    parser.add_argument(
        '--exp-folders',
        nargs='+',
        default=[
            '01-a-default-sumo-orig-03-no-system-prompt',
            '01-b-default-otp'
        ],
        help='Corresponding folder names for each experiment label'
    )
    parser.add_argument(
        '--output-file',
        default='comparison_results.txt',
        help='Path to the text file where tables will be written'
    )

    args = parser.parse_args()

    mid = MidSurveyResults(args.mid_path, args.bland_code)
    sim_data = {
        label: SimulationResults(os.path.join(args.sim_base_folder, folder))
        for label, folder in zip(args.experiments, args.exp_folders)
    }

    tables = build_comparison_tables(mid, sim_data, args.experiments)
    pd.set_option('display.float_format', '{:.2f}'.format)

    with open(args.output_file, 'w') as f:
        f.write("===== 1) Overall Modality Split =====\n\n")
        f.write(tables["modality_overall"].to_string())
        f.write("\n\n===== 2) Route Length Distribution =====\n\n")
        f.write(tables["route_length_dist"].to_string())
        f.write("\n\n===== 3) Route Duration Distribution =====\n\n")
        f.write(tables["route_duration_dist"].to_string())
        f.write("\n\n===== 4) Route Lengths by Modality =====\n\n")
        f.write(tables["lengths_by_modality"].to_string())
        f.write("\n\n===== 5) Route Durations by Modality =====\n\n")
        f.write(tables["durations_by_modality"].to_string())
        f.write("\n\n===== 6) Possible‐Routes Upset Counts (Simulation Only) =====\n\n")
        f.write(tables["upset_counts"].to_string())

    print(f"All comparison tables have been logged to '{args.output_file}'.")


if __name__ == "__main__":
    main()
