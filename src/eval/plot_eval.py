import argparse
import os
import traceback

import numpy as np

from eval.results_access.mid_survey_results import MidSurveyResults
from eval.results_access.persons_filter import (
    high_economic_filter, medium_economic_filter, low_economic_filter,
    full_time_or_learning_filter, part_time_filter, child_or_pupil_filter, not_working_filter, retired_filter
)
from eval.results_access.simulation_results import SimulationResults
from eval.util.logging import log_metrics, setup_logger
from eval.util.metric import compute_rmse
from eval.util.plot import (
    plot_percentage_bars, plot_grouped_stacked_percentage_bars,
    plot_bubble_chart, plot_upset
)


def compute_mid_blend_rmse(path_mid, berlin_bland, logger):
    """
    Computes RMSE values for the MiD modality split by comparing the modality split
    of the Berlin bland (e.g., bland=11) with all other blands.
    Assumes that valid bland values range from 1 to 16.
    """
    all_blands = list(range(1, 17))
    other_blands = [b for b in all_blands if b != berlin_bland]
    mid_dataset_berlin = MidSurveyResults(path_mid, bland=berlin_bland)
    berlin_modality = mid_dataset_berlin.get_modality_split()
    berlin_modality = MidSurveyResults.standardize_keys(berlin_modality)
    rmse_results = {}
    for bland in other_blands:
        mid_dataset_other = MidSurveyResults(path_mid, bland=bland)
        other_modality = mid_dataset_other.get_modality_split()
        other_modality = MidSurveyResults.standardize_keys(other_modality)
        rmse_value = compute_rmse(berlin_modality, other_modality)
        rmse_results[bland] = rmse_value
        logger.info("Modality RMSE between Berlin bland (%d) and bland %d: %.2f", berlin_bland, bland, rmse_value)
    return rmse_results


def compute_mid_blend_rmse_route_durations(path_mid, berlin_bland, logger):
    """
    Computes RMSE values for the MiD route durations by comparing the durations
    of the Berlin bland (e.g., bland=11) with all other blands.
    """
    all_blands = list(range(1, 17))
    other_blands = [b for b in all_blands if b != berlin_bland]
    mid_dataset_berlin = MidSurveyResults(path_mid, bland=berlin_bland)
    berlin_durations = mid_dataset_berlin.get_route_durations()
    rmse_results = {}
    for bland in other_blands:
        mid_dataset_other = MidSurveyResults(path_mid, bland=bland)
        other_durations = mid_dataset_other.get_route_durations()
        rmse_value = compute_rmse(berlin_durations, other_durations)
        rmse_results[bland] = rmse_value
        logger.info("Route Durations RMSE between Berlin bland (%d) and bland %d: %.2f", berlin_bland, bland,
                    rmse_value)
    return rmse_results


def compute_mid_blend_rmse_route_lengths(path_mid, berlin_bland, logger):
    """
    Computes RMSE values for the MiD route lengths by comparing the lengths
    of the Berlin bland (e.g., bland=11) with all other blands.
    """
    all_blands = list(range(1, 17))
    other_blands = [b for b in all_blands if b != berlin_bland]
    mid_dataset_berlin = MidSurveyResults(path_mid, bland=berlin_bland)
    berlin_lengths = mid_dataset_berlin.get_route_lengths()
    rmse_results = {}
    for bland in other_blands:
        mid_dataset_other = MidSurveyResults(path_mid, bland=bland)
        other_lengths = mid_dataset_other.get_route_lengths()
        rmse_value = compute_rmse(berlin_lengths, other_lengths)
        rmse_results[bland] = rmse_value
        logger.info("Route Lengths RMSE between Berlin bland (%d) and bland %d: %.2f", berlin_bland, bland, rmse_value)
    return rmse_results


# ------------------------
# Plot Functions with RMSE Calculations
# ------------------------
def get_modality_split(mid_dataset, sim_dataset, persons_filter):
    mid_modality = mid_dataset.get_modality_split(person_filter=persons_filter)
    mid_modality = MidSurveyResults.standardize_keys(mid_modality)
    person_ids = mid_dataset.get_person_ids(person_filter=persons_filter)
    sim_modality = sim_dataset.calculate_modality_percent(person_id_list=person_ids)
    sim_modality = SimulationResults.standardize_keys(sim_modality)
    return mid_modality, sim_modality


def plot_modality_split(mid_dataset, sim_dataset, persons_filter, title, path, logger, file_name):
    mid_modality, sim_modality = get_modality_split(mid_dataset, sim_dataset, persons_filter)
    rmse_value = compute_rmse(sim_modality, mid_modality)
    log_metrics(title, rmse_value, logger)
    plot_percentage_bars(
        mid_modality,
        sim_modality,
        dict1_label="MiD 2017",
        dict2_label="Simulation",
        xlabel="Mode of Transportation",
        ylabel="Percentage (%)",
        path=path,
        file_name=file_name,
    )
    return rmse_value


def plot_all_modality_split(mid_dataset, sim_dataset, path, logger, file_name):
    title = "Modal Split"
    rmse = plot_modality_split(mid_dataset, sim_dataset, persons_filter=None,
                               title=title, path=path, logger=logger,
                               file_name=file_name)
    return rmse


def plot_in_one_modality_by_economic_status(mid_dataset, sim_dataset, path, logger, file_name):
    mid_modality_low, sim_modality_low = get_modality_split(mid_dataset, sim_dataset, low_economic_filter)
    mid_modality_medium, sim_modality_medium = get_modality_split(mid_dataset, sim_dataset, medium_economic_filter)
    mid_modality_high, sim_modality_high = get_modality_split(mid_dataset, sim_dataset, high_economic_filter)
    for label, mid_mod, sim_mod in zip(
            ["Low", "Medium", "High"],
            [mid_modality_low, mid_modality_medium, mid_modality_high],
            [sim_modality_low, sim_modality_medium, sim_modality_high]
    ):
        rmse_val = compute_rmse(sim_mod, mid_mod)
        log_metrics(f"Modal Split ({label} Economic)", rmse_val, logger)
    mid = [mid_modality_low, mid_modality_medium, mid_modality_high]
    sim = [sim_modality_low, sim_modality_medium, sim_modality_high]
    category_labels = ["Low", "Medium", "High"]
    subcategory_labels = mid_modality_low.keys()
    colors = {
        "By foot": "#5A9BD5",
        "Bicycle": "#E27D60",
        "MIT": "#F7C59F",
        "Public Transport": "#88B04B",
    }.values()
    plot_grouped_stacked_percentage_bars(
        mid, sim,
        category_labels, subcategory_labels,
        dataset1_label="MiD",
        dataset2_label="Simulation",
        xlabel="Economic Status",
        ylabel="Percentage (%)",
        colors=colors,
        path=path,
        file_name=file_name,
    )


def plot_in_one_modality_by_occupation(mid_dataset, sim_dataset, path, logger, file_name):
    filters = [
        (full_time_or_learning_filter, "Full time or learning"),
        (part_time_filter, "Part time"),
        # (working_other_filter, "Working (other)"),
        (child_or_pupil_filter, "Child or pupil"),
        # (student_filter, "Student"),
        (not_working_filter, "Not Working"),
        (retired_filter, "Retired")
    ]
    modality_data_mid = []
    modality_data_sim = []
    for filt, label in filters:
        mid_mod, sim_mod = get_modality_split(mid_dataset, sim_dataset, filt)
        rmse_val = compute_rmse(sim_mod, mid_mod)
        log_metrics(f"Modal Split ({label})", rmse_val, logger)
        modality_data_mid.append(mid_mod)
        modality_data_sim.append(sim_mod)
    category_labels = [label for _, label in filters]
    subcategory_labels = modality_data_mid[0].keys()
    colors = {
        "By foot": "#5A9BD5",
        "Bicycle": "#E27D60",
        "MIT": "#F7C59F",
        "Public Transport": "#88B04B",
    }.values()
    plot_grouped_stacked_percentage_bars(
        modality_data_mid, modality_data_sim,
        category_labels, subcategory_labels,
        dataset1_label="MiD",
        dataset2_label="Simulation",
        xlabel="Occupation",
        ylabel="Percentage (%)",
        colors=colors,
        path=path,
        file_name=file_name,
    )


def plot_in_one_bubble_chart_way_length_by_modality_mid(mid_dataset, path, file_name, logger):
    colors = {
        "By foot": "#5A9BD5",
        "Bicycle": "#E27D60",
        "MIT": "#F7C59F",
        "Public Transport": "#88B04B",
    }
    data, categories, modes = mid_dataset.get_route_lengths_by_modalities()
    log_metrics(file_name, data, logger)
    plot_bubble_chart(
        categories, modes, data, colors,
        xlabel="Length Category",
        ylabel="Mode of Transportation",
        path=path,
        file_name=file_name,
    )


def plot_in_one_bubble_chart_way_length_by_modality_sim(sim_dataset, path, file_name, logger):
    colors = {
        "By foot": "#5A9BD5",
        "Bicycle": "#E27D60",
        "MIT": "#F7C59F",
        "Public Transport": "#88B04B",
    }
    data, categories, modes = sim_dataset.get_route_lengths_by_modalities()
    log_metrics(file_name, data, logger)
    plot_bubble_chart(
        categories, modes, data, colors,
        xlabel="Length Category",
        ylabel="Mode of Transportation",
        path=path,
        file_name=file_name,
    )


def plot_in_one_bubble_chart_way_duration_by_modality_mid(mid_dataset, path, file_name, logger):
    colors = {
        "By foot": "#5A9BD5",
        "Bicycle": "#E27D60",
        "MIT": "#F7C59F",
        "Public Transport": "#88B04B",
    }
    data, categories, modes = mid_dataset.get_route_durations_by_modalities()
    log_metrics(file_name, data, logger)
    plot_bubble_chart(
        categories, modes, data, colors,
        xlabel="Duration Category",
        ylabel="Mode of Transportation",
        path=path,
        file_name=file_name,
    )


def plot_in_one_bubble_chart_way_duration_by_modality_sim(sim_dataset, path, file_name, logger):
    colors = {
        "By foot": "#5A9BD5",
        "Bicycle": "#E27D60",
        "MIT": "#F7C59F",
        "Public Transport": "#88B04B",
    }
    data, categories, modes = sim_dataset.get_route_durations_by_modalities()
    log_metrics(file_name, data, logger)
    plot_bubble_chart(
        categories, modes, data, colors,
        xlabel="Duration Category",
        ylabel="Mode of Transportation",
        path=path,
        file_name=file_name,
    )


def plot_route_durations(mid_dataset, sim_dataset, path, logger, file_name):
    title = "Route durations"
    mid_durations = mid_dataset.get_route_durations()
    logger.info("MiD Route Durations (percentages): %s", mid_durations)
    sim_durations = sim_dataset.get_route_durations()
    logger.info("Simulated Route Durations (percentages): %s", sim_durations)
    rmse_value = compute_rmse(sim_durations, mid_durations)
    log_metrics(title, rmse_value, logger)
    plot_percentage_bars(
        mid_durations,
        sim_durations,
        dict1_label="MiD 2017",
        dict2_label="Simulation",
        xlabel="Duration Category",
        ylabel="Percentage (%)",
        path=path,
        file_name=file_name,
    )
    return rmse_value


def plot_route_lengths(mid_dataset, sim_dataset, path, logger, file_name):
    title = "Route lengths"
    mid_lengths = mid_dataset.get_route_lengths()
    logger.info("MiD Route Lengths (percentages): %s", mid_lengths)
    sim_lengths = sim_dataset.get_route_lengths()
    logger.info("Simulated Route Lengths (percentages): %s", sim_lengths)
    rmse_value = compute_rmse(sim_lengths, mid_lengths)
    log_metrics(title, rmse_value, logger)
    plot_percentage_bars(
        mid_lengths,
        sim_lengths,
        dict1_label="MiD 2017",
        dict2_label="Simulation",
        xlabel="Length Category",
        ylabel="Percentage (%)",
        path=path,
        file_name=file_name,
    )
    return rmse_value


def plot_upset_possible_modalities(sim_dataset, path, file_name):
    upset_df = sim_dataset.get_possible_routes_upset_data()
    plot_upset(
        upset_df,
        xlabel="Modalities Combination",
        ylabel="Number of Routes",
        path=path,
        file_name=file_name
    )


def write_latex_table(summary_results, mid_blend_table, overall_avgs, output_filepath):
    """
    Creates a LaTeX file summarizing the RMSE values.
    Two tables are produced:
      (1) Simulation vs. MiD RMSE values per result folder.
      (2) MiD Blends comparisons (Berlin vs. each other state) and their overall averages.
    overall_avgs is a tuple:
         (overall_modality, overall_durations, overall_lengths, overall_avg)
    """
    summary_results = sorted(summary_results, key=lambda x: x["folder"])

    table1 = r"""\begin{{table}}[htbp]
\centering
\begin{{tabular}}{{lcccc}}
\hline
\multicolumn{{1}}{{c}}{{Result Folder}} & \multicolumn{{4}}{{c}}{{RMSE}} \\
 & Modality & Durations & Lengths & Weighted \\
\hline
"""
    for res in summary_results:
        table1 += " {} & {:.2f} & {:.2f} & {:.2f} & {:.2f} \\\\\n".format(
            res["folder"],
            res["rmse_modality"],
            res["rmse_durations"],
            res["rmse_lengths"],
            res["weighted"]
        )
    table1 += r"""\hline
\end{{tabular}}
\caption{{Simulation vs. MiD RMSE Comparison per Result Folder}}
\end{{table}}
"""
    table1 = table1.format()

    table2 = r"""\begin{{table}}[htbp]
\centering
\begin{{tabular}}{{lcccc}}
\hline
\multicolumn{{1}}{{c}}{{State}} & \multicolumn{{4}}{{c}}{{RMSE}} \\
 & Modality & Durations & Lengths & Average \\
\hline
""".format()
    for entry in mid_blend_table:
        table2 += " {} & {:.2f} & {:.2f} & {:.2f} & {:.2f} \\\\\n".format(
            entry["state"],
            entry["modality"],
            entry["durations"],
            entry["lengths"],
            entry["avg"]
        )
    overall_modality, overall_durations, overall_lengths, overall_avg = overall_avgs
    table2 += r"""\hline
Overall Average & {:.2f} & {:.2f} & {:.2f} & {:.2f} \\
\hline
\end{{tabular}}
\caption{{MiD Blends Comparison (Berlin vs. Other States)}}
\end{{table}}
""".format(overall_modality, overall_durations, overall_lengths, overall_avg)

    full_content = table1 + "\n\n" + table2
    with open(output_filepath, "w") as f:
        f.write(full_content)


def compare_states(berlin_bland, path_mid, results_base_path, state_names):
    # Berlin vs. each other bland
    final_log_path = os.path.join(results_base_path, "final_results.log")
    final_logger = setup_logger(final_log_path)
    final_logger.info("Computing MiD-Blends for Berlin (bland=%d) vs. all other blands.", berlin_bland)
    global_mid_blend_rmse_modality = compute_mid_blend_rmse(path_mid, berlin_bland, final_logger)
    global_mid_blend_rmse_durations = compute_mid_blend_rmse_route_durations(path_mid, berlin_bland, final_logger)
    global_mid_blend_rmse_lengths = compute_mid_blend_rmse_route_lengths(path_mid, berlin_bland, final_logger)
    # Build mid_blend_table using state names.
    mid_blend_table = []
    for bland in sorted(global_mid_blend_rmse_modality.keys()):
        mod = global_mid_blend_rmse_modality[bland]
        dur = global_mid_blend_rmse_durations[bland]
        leng = global_mid_blend_rmse_lengths[bland]
        avg = (mod + dur + leng) / 3
        mid_blend_table.append({
            "state": state_names.get(bland, str(bland)),
            "modality": mod,
            "durations": dur,
            "lengths": leng,
            "avg": avg
        })
        final_logger.info(
            "Comparison for state %s: Modality RMSE = %.2f, Route Duration RMSE = %.2f, "
            "Route Length RMSE = %.2f, Average = %.2f",
            state_names.get(bland, str(bland)), mod, dur, leng, avg
        )
    # Compute overall averages.
    overall_modality = np.mean([entry["modality"] for entry in mid_blend_table])
    overall_durations = np.mean([entry["durations"] for entry in mid_blend_table])
    overall_lengths = np.mean([entry["lengths"] for entry in mid_blend_table])
    overall_avg = np.mean([entry["avg"] for entry in mid_blend_table])
    final_logger.info(
        "Overall Average RMSE among MiD Blends: Modality = %.2f, Durations = %.2f, "
        "Lengths = %.2f, Average = %.2f",
        overall_modality, overall_durations, overall_lengths, overall_avg
    )
    overall_avgs = (overall_modality, overall_durations, overall_lengths, overall_avg)
    return mid_blend_table, overall_avgs


def plot_sim(folder_path, logger, mid_dataset, output_path):
    sim_dataset = SimulationResults(folder_path)
    rmse_modality = plot_all_modality_split(
        mid_dataset, sim_dataset,
        output_path, logger,
        file_name="01_modal_split"
    )
    plot_in_one_modality_by_economic_status(
        mid_dataset, sim_dataset,
        output_path, logger,
        file_name="02_modal_split_economic_status"
    )
    plot_in_one_modality_by_occupation(
        mid_dataset, sim_dataset,
        output_path, logger,
        file_name="03_modal_split_occupation"
    )
    rmse_lengths = plot_route_lengths(
        mid_dataset, sim_dataset,
        output_path, logger,
        file_name="04_route_lengths"
    )
    rmse_durations = plot_route_durations(
        mid_dataset, sim_dataset,
        output_path, logger,
        file_name="05_route_durations"
    )
    plot_in_one_bubble_chart_way_length_by_modality_mid(
        mid_dataset,
        output_path,
        "06_route_lengths_by_modal_split_mid",
        logger
    )
    plot_in_one_bubble_chart_way_length_by_modality_sim(
        sim_dataset,
        output_path,
        "07_route_lengths_by_modal_split_sim",
        logger
    )
    plot_in_one_bubble_chart_way_duration_by_modality_mid(
        mid_dataset,
        output_path,
        "08_route_durations_by_modal_split_mid",
        logger
    )
    plot_in_one_bubble_chart_way_duration_by_modality_sim(
        sim_dataset,
        output_path,
        "09_route_durations_by_modal_split_sim",
        logger
    )
    plot_upset_possible_modalities(
        sim_dataset,
        output_path,
        file_name="10_upset_plot"
    )
    return rmse_durations, rmse_lengths, rmse_modality


def main():
    parser = argparse.ArgumentParser(
        description="Process simulation folders, compute RMSE metrics, generate plots, and compile a LaTeX summary."
    )
    parser.add_argument(
        '--mid-path',
        default='../../data/census/B1_Standard-Datensatzpaket/CSV',
        help='Path to the MID survey CSV directory'
    )
    parser.add_argument(
        '--bland-code',
        type=int,
        default=11,
        help='Bland code value for Berlin survey'
    )
    parser.add_argument(
        '--results-base',
        default='../../results/experiments',
        help='Base directory containing experiment result folders'
    )
    parser.add_argument(
        '--state-names',
        nargs='*',
        default=[
            '1:Schleswig-Holstein', '2:Hamburg', '3:Niedersachsen', '4:Bremen',
            '5:Nordrhein-Westfalen', '6:Hessen', '7:Rheinland-Pfalz',
            '8:Baden-Württemberg', '9:Bayern', '10:Saarland', '11:Berlin',
            '12:Brandenburg', '13:Mecklenburg-Vorpommern', '14:Sachsen',
            '15:Sachsen-Anhalt', '16:Thüringen'
        ],
        help='Bland-to-state mappings as "code:Name"'
    )
    parser.add_argument(
        '--output-latex',
        default=None,
        help='Optional path for the generated LaTeX summary file (defaults to results-base/rsme_summary.tex)'
    )

    args = parser.parse_args()

    # Parse state mappings
    state_names = {}
    for item in args.state_names:
        code, name = item.split(':', 1)
        state_names[int(code)] = name

    mid_dataset = MidSurveyResults(args.mid_path, bland=args.bland_code)

    summary_results = []

    for folder in os.listdir(args.results_base):
        folder_path = os.path.join(args.results_base, folder)
        if not os.path.isdir(folder_path):
            continue

        # Setup output and logging
        plots_dir = os.path.join(folder_path, 'plots')
        os.makedirs(plots_dir, exist_ok=True)
        log_file = os.path.join(plots_dir, 'processing.log')
        logger = setup_logger(log_file)
        logger.info("Processing folder: %s", folder)

        try:
            rmse_durations, rmse_lengths, rmse_modality = plot_sim(
                folder_path, logger, mid_dataset, plots_dir
            )
            weighted_sum = (rmse_modality + rmse_durations + rmse_lengths) / 3
            log_metrics("Weighted Sum RMSE (Simulation vs MiD)", weighted_sum, logger)

            summary_results.append({
                'folder': folder,
                'rmse_modality': rmse_modality,
                'rmse_durations': rmse_durations,
                'rmse_lengths': rmse_lengths,
                'weighted': weighted_sum
            })
        except Exception as e:
            logger.exception("Error processing %s: %s", folder, str(e))
            traceback.print_exc()
        logger.info("Completed processing: %s", folder)

    # Determine LaTeX output path
    latex_path = args.output_latex or os.path.join(args.results_base, 'rsme_summary.tex')

    # Compare states and write LaTeX
    mid_table, overall_avgs = compare_states(
        args.bland_code,
        args.mid_path,
        args.results_base,
        state_names
    )
    write_latex_table(summary_results, mid_table, overall_avgs, latex_path)

    print(f"LaTeX summary file created at: {latex_path}")
    print("Processing complete for all experiment folders.")


if __name__ == '__main__':
    main()
