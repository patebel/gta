import argparse
import logging
import os
import traceback
from collections import OrderedDict

from eval.results_access.mid_survey_results import MidSurveyResults
from eval.results_access.simulation_results import SimulationResults
from eval.util.logging import log_metrics, setup_logger
from eval.util.metric import compute_rmse
from eval.util.plot import (
    plot_percentage_bars,
)

MODE_ORDER = ["By foot", "Bicycle", "MIT", "Public Transport"]


def sort_modal_dict(mod_dict):
    return OrderedDict((mode, mod_dict.get(mode, 0.0)) for mode in MODE_ORDER)


def get_modality_split_sim_for_ids(sim_dataset, person_ids):
    mod = sim_dataset.calculate_modality_percent(person_id_list=person_ids)
    mod = SimulationResults.standardize_keys(mod)
    return sort_modal_dict(mod)


def plot_modality_comparison(mid_dataset: MidSurveyResults,
                             sim_default: SimulationResults,
                             sim_other: SimulationResults,
                             title: str,
                             output_path: str,
                             logger: logging.Logger,
                             file_name: str,
                             label_other: str):
    person_ids = mid_dataset.get_person_ids(person_filter=None)

    default_mod = sim_default.calculate_modality_percent(person_id_list=person_ids)
    default_mod = SimulationResults.standardize_keys(default_mod)
    default_mod = sort_modal_dict(default_mod)

    other_mod = sim_other.calculate_modality_percent(person_id_list=person_ids)
    other_mod = SimulationResults.standardize_keys(other_mod)
    other_mod = sort_modal_dict(other_mod)

    rmse_value = compute_rmse(default_mod, other_mod)
    log_metrics(title, rmse_value, logger)

    plot_percentage_bars(
        default_mod,
        other_mod,
        dict1_label="Default Experiment",
        dict2_label=label_other,
        xlabel="Mode of Transportation",
        ylabel="Percentage (%)",
        path=output_path,
        file_name=file_name,
    )
    return rmse_value


def main():
    parser = argparse.ArgumentParser(
        description="Compare default simulation to other experiments with modality plots."
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
        help='Base folder for simulation experiment results'
    )
    parser.add_argument(
        '--default-folder',
        default='01-a-default-sumo-orig-03-no-system-prompt',
        help='Name of the default experiment subfolder'
    )
    parser.add_argument(
        '--other',
        nargs=2,
        action='append',
        metavar=('LABEL', 'FOLDER'),
        default=[
            ['Free public transport', '06-03-thought-experiment'],
            ['Protected bike lanes', '06-04-thought-experiment'],
        ],
        help=('Pairs of label and folder-name for additional experiments. '
              'Use multiple times: --other "Label" folder')
    )
    args = parser.parse_args()

    # Load survey results
    mid = MidSurveyResults(args.mid_path, bland=args.bland_code)

    # Prepare default simulation
    default_path = os.path.join(args.results_base, args.default_folder)
    if not os.path.isdir(default_path):
        raise FileNotFoundError(f"Default experiment folder not found: {default_path}")
    sim_default = SimulationResults(default_path)

    # Compare against each other experiment
    for label, folder in args.other:
        other_path = os.path.join(args.results_base, folder)
        if not os.path.isdir(other_path):
            print(f"Warning: Experiment folder '{folder}' not found; skipping '{label}'.")
            continue

        # Setup output directory and logger
        out_dir = os.path.join(other_path, 'comparison_plots')
        os.makedirs(out_dir, exist_ok=True)
        log_file = os.path.join(out_dir, 'comparison.log')
        logger = setup_logger(log_file)
        logger.info("Comparing default '%s' to '%s' (%s)", args.default_folder, label, folder)

        try:
            sim_other = SimulationResults(other_path)
            plot_modality_comparison(
                mid,
                sim_default,
                sim_other,
                title=f"Modality Split: Default vs {label}",
                output_path=out_dir,
                logger=logger,
                file_name="modality_split_comparison",
                label_other=label
            )
            logger.info("Completed comparison for '%s'", label)
        except Exception as e:
            logger.exception("Error processing '%s': %s", label, str(e))
            traceback.print_exc()

    print("All comparisons complete.")


if __name__ == '__main__':
    main()
