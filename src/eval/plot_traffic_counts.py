import argparse
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sumolib import net as sumonet

# Plot formatting constants
BASE_FONT = 20  # axis labels, default text
ANNOTATE_FONT = 15  # default annotation font
SMALL_ANNOTATE_FONT = 8  # smaller annotation font
LEGEND_FONT = 20  # legend text
TICK_FONT = 20
FIGSIZE = (10, 8)  # unified figure size


def get_q_kfz_det_hr(filepath: str, det_id: str, date_str: str, sep: Optional[str] = None) -> List[float]:
    """Return 24-hour counts for a given detector and date, filling missing hours with zeros."""
    df = pd.read_csv(filepath, sep=sep, engine='python', dtype=str, encoding='utf-8-sig')
    df.columns = df.columns.str.lower().str.strip()
    for col in ('detid_15', 'tag', 'stunde', 'q_kfz_det_hr'):
        if col not in df.columns:
            raise KeyError(f"Missing column '{col}' in CSV")

    df['stunde'] = pd.to_numeric(df['stunde'], errors='coerce').fillna(0).astype(int)
    df['q_kfz_det_hr'] = pd.to_numeric(df['q_kfz_det_hr'], errors='coerce').fillna(0.0)
    df['tag'] = pd.to_datetime(df['tag'], dayfirst=True, errors='coerce').dt.date

    target = datetime.strptime(date_str, "%d.%m.%Y").date()
    sel = df.loc[(df['detid_15'] == str(det_id)) & (df['tag'] == target)]
    counts = sel.set_index('stunde')['q_kfz_det_hr'].reindex(range(24), fill_value=0.0)
    return counts.tolist()


def hourly_entered_counts_by_edge(meandata_file: str, edge_id: str) -> List[int]:
    """Parse SUMO meandata XML, summing 'entered' counts per hour for one edge."""
    counts = [0] * 24
    for _, elem in ET.iterparse(meandata_file, events=('end',)):
        if elem.tag == 'interval':
            hour = int(float(elem.get('begin', 0)) // 3600)
            for edge_elem in elem.findall('edge'):
                if edge_elem.get('id') == edge_id:
                    counts[hour] += int(edge_elem.get('entered', 0))
            elem.clear()
    return counts


def plot_comparison(flows: List[float], real: List[float], normalized: bool, use_bar: bool,
                    save_path: Optional[str] = None):
    """Plot real vs simulated vehicle counts with consistent formatting, placing the legend outside."""
    hours = np.arange(24)
    sim_arr = np.array(flows, dtype=float)
    real_arr = np.array(real, dtype=float)

    if normalized:
        sim_arr = sim_arr / sim_arr.max() if sim_arr.max() else sim_arr
        real_arr = real_arr / real_arr.max() if real_arr.max() else real_arr
        suffix = ' (Normalized)'
    else:
        suffix = ''

    # Create figure and axes explicitly, so we can place legend outside
    fig, ax = plt.subplots(figsize=FIGSIZE)

    if use_bar:
        w = 0.4
        ax.bar(hours - w / 2, sim_arr, w, label='Simulated' + suffix)
        ax.bar(hours + w / 2, real_arr, w, label='Real' + suffix)
    else:
        ax.plot(hours, sim_arr, 'o-', label='Simulated' + suffix)
        ax.plot(hours, real_arr, 'x--', label='Real' + suffix)

    ax.grid(linestyle='--', alpha=0.5)

    # Axis labels
    ax.set_xlabel('Hour', fontsize=BASE_FONT)
    ax.set_ylabel('Count' + (' (Normalized)' if normalized else ''), fontsize=BASE_FONT)

    # Tick parameters
    ax.set_xticks(hours)
    ax.tick_params(axis='x', labelsize=TICK_FONT)
    ax.tick_params(axis='y', labelsize=TICK_FONT)

    # Place the legend outside on the right
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=4, frameon=False,
              fontsize=LEGEND_FONT)
    # ax.legend(fontsize=LEGEND_FONT, loc='upper left', bbox_to_anchor=(1.02, 1), frameon=False)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"→ Saved plot: {save_path}")

    plt.close()


def filter_stations_by_bbox(excel_path: str, xmin: float, ymin: float, xmax: float, ymax: float,
                            sheet_name: Optional[Union[str, int]] = None) -> pd.DataFrame:
    """Load station metadata and filter by bounding box."""
    xlsx = pd.ExcelFile(excel_path, engine='openpyxl')
    sheet = sheet_name if sheet_name is not None else xlsx.sheet_names[0]
    df = pd.read_excel(excel_path, sheet_name=sheet, engine='openpyxl')
    df.columns = df.columns.str.lower().str.strip()
    df.rename(columns={'länge (wgs84)': 'longitude', 'breite (wgs84)': 'latitude'}, inplace=True)
    for col in ('longitude', 'latitude'):
        if col not in df.columns:
            raise KeyError(f"Missing column '{col}' in Excel sheet '{sheet}'")
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    return df[
        (df['longitude'] >= xmin) & (df['longitude'] <= xmax) & (df['latitude'] >= ymin) & (df['latitude'] <= ymax)]


def run_analysis(filtered_df: pd.DataFrame, net: sumonet.Net, csv_path: str, meandata_xml: str, date_str: str,
                 results_path: str) -> None:
    required = {'det_id15', 'mq_kurzname', 'longitude', 'latitude'}
    if not required.issubset(filtered_df.columns):
        raise KeyError(f"Filtered DF missing columns: {required - set(filtered_df.columns)}")

    summary = []
    os.makedirs(results_path, exist_ok=True)

    for name, group in filtered_df.groupby('mq_kurzname'):
        det_ids = group['det_id15'].astype(str).to_list()
        # find first matching edge per group
        edges = []
        for det_id in det_ids:
            lon, lat = group.loc[group['det_id15'].astype(str) == det_id, ['longitude', 'latitude']].iloc[0]
            x, y = net.convertLonLat2XY(lon, lat)
            nbrs = net.getNeighboringEdges(x, y, r=10, includeJunctions=False, allowFallback=True)
            if nbrs:
                edges.append(sorted(nbrs, key=lambda x: x[1])[0][0].getID())
        if not edges:
            print(f"No edges found for station '{name}'")
            continue
        sim_edge = edges[0]

        # aggregate real counts across all detectors
        real_tot = [0] * 24
        for det_id in det_ids:
            real_tot = [r + v for r, v in zip(real_tot, get_q_kfz_det_hr(csv_path, det_id, date_str))]
        sim_tot = hourly_entered_counts_by_edge(meandata_xml, sim_edge)

        # compute metrics and normalized arrays
        sim_arr = np.array(sim_tot, float)
        real_arr = np.array(real_tot, float)
        sim_norm_arr = sim_arr / sim_arr.max() if sim_arr.max() else sim_arr
        real_norm_arr = real_arr / real_arr.max() if real_arr.max() else real_arr
        rmse = np.sqrt(np.mean((sim_arr - real_arr) ** 2))
        rmse_norm = np.sqrt(np.mean((sim_norm_arr - real_norm_arr) ** 2))

        # collect summary
        summary.append({
            'name': name,
            'real_sum': real_arr.sum(),
            'sim_sum': sim_arr.sum(),
            'rmse': rmse,
            'rmse_norm': rmse_norm,
            'real_counts': real_arr.tolist(),
            'sim_counts': sim_arr.tolist(),
            'real_norm_counts': real_norm_arr.tolist(),
            'sim_norm_counts': sim_norm_arr.tolist()
        })

        outdir = os.path.join(results_path, name)
        os.makedirs(outdir, exist_ok=True)
        for norm in (False, True):
            for bar in (False, True):
                suffix = f"{name}_{'norm' if norm else 'not_norm'}_{'bar' if bar else 'line'}"
                plot_path = os.path.join(outdir, f"{suffix}.pdf")
                plot_comparison(sim_tot, real_tot, norm, bar, plot_path)

        info_path = os.path.join(outdir, 'info.txt')
        with open(info_path, 'w') as f:
            f.write(f"Date: {date_str}\nStation: {name}\nDetectors: {', '.join(det_ids)}\nSim Edge: {sim_edge}\n")
            f.write(
                f"Totals -> Real: {real_arr.sum()}, Sim: {sim_arr.sum()}\nRMSE: {rmse:.2f}, Norm RMSE: {rmse_norm:.2f}\n\nDetails:\n{group.to_string(index=False)}\n")
        print(f"→ Saved {info_path}")

    # write summary files with per-hour counts and normalized values
    summary_txt = os.path.join(results_path, 'summary.txt')
    with open(summary_txt, 'w') as f:
        header = ['Station', 'RealTotal', 'SimTotal', 'RMSE', 'NormRMSE',
                  'RealCounts', 'SimCounts', 'RealNormCounts', 'SimNormCounts']
        f.write('\t'.join(header) + '\n')
        for s in summary:
            row = [
                s['name'],
                str(s['real_sum']),
                str(s['sim_sum']),
                f"{s['rmse']:.2f}",
                f"{s['rmse_norm']:.2f}",
                ','.join(map(str, s['real_counts'])),
                ','.join(map(str, s['sim_counts'])),
                ','.join(f"{v:.4f}" for v in s['real_norm_counts']),
                ','.join(f"{v:.4f}" for v in s['sim_norm_counts'])
            ]
            f.write('\t'.join(row) + '\n')
    print(f"→ Saved {summary_txt}")

    # existing LaTeX summary (unchanged)
    latex_path = os.path.join(results_path, 'summary.tex')
    with open(latex_path, 'w') as f:
        f.write('\\begin{tabular}{lrrrr}\n')
        f.write('Station & Real & Sim & RMSE & NormRMSE \\\\\n')
        f.write('\\hline\n')
        for s in summary:
            f.write(f"{s['name']} & {s['real_sum']} & {s['sim_sum']} & {s['rmse']:.2f} & {s['rmse_norm']:.2f} \\\\\n")
        f.write('\\end{tabular}\n')
    print(f"→ Saved {latex_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Filter station data by bounding box, load SUMO network, and run traffic analysis."
    )
    parser.add_argument(
        '--excel-file',
        default='../../data/traffic_counts/Stammdaten_Verkehrsdetektion_2022_07_20.xlsx',
        help='Path to the Excel file with station master data'
    )
    parser.add_argument(
        '--net-file',
        default='../../data/open_street_map/wedding/wedding.net.xml',
        help='Path to the SUMO network XML file'
    )
    parser.add_argument(
        '--csv-file',
        default='../../data/traffic_counts/det_val_hr_2017_01.csv',
        help='Path to the CSV with hourly detection values'
    )
    parser.add_argument(
        '--meandata-xml',
        default='../../results/experiments/01-c-default-sumo-wedding/sumo_run/edge_data.xml',
        help='Path to the SUMO mean-data XML file'
    )
    parser.add_argument(
        '--date',
        default='16.01.2017',
        help='Date string for analysis (e.g., DD.MM.YYYY)'
    )
    parser.add_argument(
        '--results-path',
        default='../../results/experiments/01-c-default-sumo-wedding/sumo_run/traffic_counts',
        help='Directory where analysis results will be stored'
    )
    parser.add_argument(
        '--bbox',
        nargs=4,
        type=float,
        metavar=('XMIN', 'YMIN', 'XMAX', 'YMAX'),
        default=[13.3015376, 52.5356604, 13.3749244, 52.5644452],
        help='Bounding box for station filtering: xmin ymin xmax ymax'
    )

    args = parser.parse_args()

    # Filter station dataframe by bounding box
    xmin, ymin, xmax, ymax = args.bbox
    df = filter_stations_by_bbox(args.excel_file, xmin, ymin, xmax, ymax)

    # Read SUMO network
    net = sumonet.readNet(args.net_file)

    # Ensure results directory exists
    os.makedirs(args.results_path, exist_ok=True)

    # Run analysis
    run_analysis(
        df,
        net,
        args.csv_file,
        args.meandata_xml,
        args.date,
        args.results_path
    )

    print(f"Analysis complete. Results saved in {args.results_path}.")


if __name__ == '__main__':
    main()
