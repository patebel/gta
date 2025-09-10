#!/usr/bin/env python3
import argparse
import os

import matplotlib.pyplot as plt
import pandas as pd
from sumolib import net as sumonet

# Plot formatting constants
BASE_FONT = 13  # axis labels, default text
TITLE_FONT = 14  # title text (unused if titles are removed)
ANNOTATE_FONT = 13  # default annotation font
SMALL_ANNOTATE_FONT = 13  # smaller annotation font
LEGEND_FONT = 13  # legend text
TICK_FONT = 13  # tick labels
FIGSIZE = (14, 8)  # unified figure size


def filter_stations_by_bbox(excel_path, xmin, ymin, xmax, ymax, sheet_name=None):
    xlsx = pd.ExcelFile(excel_path, engine="openpyxl")
    sheet = sheet_name if sheet_name is not None else xlsx.sheet_names[0]
    df = pd.read_excel(excel_path, sheet_name=sheet, engine="openpyxl")
    df.columns = df.columns.str.lower().str.strip()
    df.rename(columns={'länge (wgs84)': 'longitude', 'breite (wgs84)': 'latitude'}, inplace=True)
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    return df[(df.longitude >= xmin) & (df.longitude <= xmax) & (df.latitude >= ymin) & (df.latitude <= ymax)]


def get_q_kfz_det_hr(filepath: str, det_id: str, date_str: str, sep: str = None):
    df = pd.read_csv(filepath, sep=sep, engine='python', dtype=str, encoding='utf-8-sig')
    df.columns = df.columns.str.lower().str.strip()
    df['stunde'] = pd.to_numeric(df['stunde'], errors='coerce').fillna(0).astype(int)
    df['q_kfz_det_hr'] = pd.to_numeric(df['q_kfz_det_hr'], errors='coerce').fillna(0.0)
    df['tag'] = pd.to_datetime(df['tag'], dayfirst=True, errors='coerce').dt.date
    target = pd.to_datetime(date_str, dayfirst=True).date()
    sel = df[(df['detid_15'] == str(det_id)) & (df['tag'] == target)]
    counts = sel.set_index('stunde')['q_kfz_det_hr'].reindex(range(24), fill_value=0.0)
    return counts.tolist()


def plot_station_map(net_file, stations_excel, csv_file, date_str, out_pdf):
    net = sumonet.readNet(net_file)
    # Wedding bbox
    xmin, ymin = 13.3015376, 52.5356604
    xmax, ymax = 13.3749244, 52.5644452

    # 1) load & filter stations
    df = filter_stations_by_bbox(stations_excel, xmin, ymin, xmax, ymax)

    # 2) compute each detector's daily count
    detcol = 'detid_15' if 'detid_15' in df.columns else 'det_id15'
    df['daily_count'] = df[detcol].astype(str) \
        .apply(lambda d: sum(get_q_kfz_det_hr(csv_file, d, date_str)))

    # 3) aggregate by station name
    grp = df.groupby('mq_kurzname').agg({
        'longitude': 'mean',
        'latitude': 'mean',
        'daily_count': 'sum'
    }).reset_index()

    # 4) project to SUMO XY, extract y for sorting
    grp['xy'] = grp.apply(lambda r: net.convertLonLat2XY(r.longitude, r.latitude), axis=1)
    grp['y'] = grp['xy'].apply(lambda xy: xy[1])

    # 5) sort by vertical position
    grp = grp.sort_values(by='y').reset_index(drop=True)

    # 6) scatter points
    xs = grp['xy'].apply(lambda xy: xy[0]).tolist()
    ys = grp['xy'].apply(lambda xy: xy[1]).tolist()

    # Set figure size using FIGSIZE constant
    fig, ax = plt.subplots(figsize=FIGSIZE, constrained_layout=True)

    # draw the net in dark gray for higher contrast
    for e in net.getEdges():
        xx, yy = zip(*e.getShape())
        ax.plot(xx, yy, color='gray', linewidth=0.7, zorder=0)

    # scatter stations with a bold color
    ax.scatter(
        xs, ys,
        c='red', s=80,  # deep blue for strong contrast
        edgecolor='white', linewidth=1.2,
        zorder=2
    )

    # 7) stack labels vertically
    label_x_offset = 10  # shift right
    min_sep = 150  # in same units as SUMO XY (meters)
    last_y = None

    for _, row in grp.iterrows():
        x0, y0 = row['xy']
        # start label at point y
        label_y = y0
        # if too close to previous label, raise it
        if last_y is not None and label_y <= last_y + min_sep:
            label_y = last_y + min_sep
        last_y = label_y

        ax.annotate(
            f"{row['mq_kurzname']}",
            xy=(x0, y0),
            xytext=(x0 + label_x_offset, label_y),
            textcoords='data',
            arrowprops=dict(arrowstyle='-', color='black', lw=0.8),
            fontsize=ANNOTATE_FONT,
            va='bottom',
            ha='left',
            color='black',
            bbox=dict(
                boxstyle="round,pad=0.3",
                fc="white",
                ec="black",
                alpha=0.9
            ),
            zorder=3
        )

    ax.set_aspect('equal')
    ax.axis('off')
    # If you want a title, you can uncomment the next line and use TITLE_FONT
    # ax.set_title(f"Real Count Stations (aggregated) – {date_str}", fontsize=TITLE_FONT, pad=12)
    plt.savefig(out_pdf, dpi=300, facecolor='white')
    plt.close(fig)
    print(f"→ Station map (stacked labels) saved to {out_pdf}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Wedding traffic visualizations")
    p.add_argument("--net", required=True, help=".net.xml")
    p.add_argument("--stations-excel", required=True, help="Excel with LÄNGE/BREITE")
    p.add_argument("--csv", required=True, help="CSV of real counts")
    p.add_argument("--date", required=True, help="date, e.g. 16.01.2017")
    p.add_argument("--out-dir", required=True, help="output folder")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    plot_station_map(
        args.net,
        args.stations_excel,
        args.csv,
        args.date,
        os.path.join(args.out_dir, "wedding_stations_named.pdf")
    )
