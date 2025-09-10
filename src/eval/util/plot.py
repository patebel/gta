import os
import warnings

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from upsetplot import UpSet, from_indicators

# ─── GLOBAL CONFIG ──────────────────────────
BASE_FONT = 20  # axis labels, default text
ANNOTATE_FONT = 15  # default annotation font
SMALL_ANNOTATE_FONT = 8  # smaller annotation font
LEGEND_FONT = 20  # legend text
TICK_FONT = 20  # tick labels
FIGSIZE = (14, 10)  # unified figure size
BUBBLE_LABEL_THRESHOLD = 3  # min % for bubble labels

# rcParams defaults
mpl.rcParams.update({
    "font.size": BASE_FONT,
    "axes.labelsize": BASE_FONT,
    "xtick.labelsize": TICK_FONT,
    "ytick.labelsize": TICK_FONT,
    "legend.fontsize": LEGEND_FONT,
    "figure.figsize": FIGSIZE,
    "figure.dpi": 300,
    "figure.autolayout": True,
    "lines.linewidth": 1.0,
    "lines.markersize": 4,
})


# Utility to align dict keys
def align_dict_keys(dict1, dict2):
    missing1 = set(dict2) - set(dict1)
    missing2 = set(dict1) - set(dict2)
    if missing1 or missing2:
        warnings.warn(
            f"Mismatch in keys detected. "
            f"Missing in dict1: {missing1}, Missing in dict2: {missing2}"
        )
    all_keys = set(dict1) | set(dict2)
    for k in all_keys:
        dict1.setdefault(k, 0)
        dict2.setdefault(k, 0)
    return dict1, dict2


# Annotate bars: only if height >= threshold
def _annotate_bars(bars, ax, fontsize=ANNOTATE_FONT):
    for bar in bars:
        h = bar.get_height()
        ax.annotate(
            f'{h:.1f}%',
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 2), textcoords="offset points",
            ha='center', va='bottom', fontsize=fontsize
        )


# Annotate stacked bars: only if segment >= threshold
def _annotate_bars_stacked(bars, bottoms, heights, ax, fontsize=ANNOTATE_FONT, threshold=3):
    for bar, bottom, height in zip(bars, bottoms, heights):
        if height >= threshold:
            ax.annotate(
                f'{height:.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, bottom + height / 2),
                xytext=(0, 0), textcoords="offset points",
                ha='center', va='center', fontsize=fontsize
            )


# ─── PLOT FUNCTIONS ───────────────────

def plot_upset(data, xlabel="", ylabel="", path=None, file_name="upset_plot", size=FIGSIZE):
    """
    Create an UpSet plot from a DataFrame of indicator columns.

    Parameters:
    - data: pandas.DataFrame with boolean indicator columns
    - xlabel: label for the x-axis (default: "")
    - ylabel: label for the y-axis (default: "")
    - path: optional folder path to save the plot (as PDF)
    - file_name: base filename (without extension) for saving
    - size: figure size tuple
    """
    upset_data = from_indicators(data.columns, data)
    upset = UpSet(upset_data, subset_size='count', show_counts=True, sort_by="cardinality")
    fig = plt.figure(figsize=size)
    upset.plot(fig=fig)
    fig.subplots_adjust(top=0.88, bottom=0.15)

    # Apply overall x and y labels, if provided
    if xlabel:
        try:
            fig.supxlabel(xlabel, fontsize=BASE_FONT)
        except AttributeError:
            fig.text(0.5, 0.01, xlabel, ha='center', va='bottom', fontsize=BASE_FONT)
    if ylabel:
        try:
            fig.supylabel(ylabel, fontsize=BASE_FONT)
        except AttributeError:
            fig.text(0.01, 0.5, ylabel, va='center', ha='left', rotation='vertical', fontsize=BASE_FONT)

    # Adjust font size of count labels
    for ax in fig.axes:
        for txt in ax.texts:
            if txt.get_text().isdigit():
                txt.set_fontsize(SMALL_ANNOTATE_FONT)

    fig.text(0.98, 0.02, f"Total routes: {len(data)}",
             ha='right', va='bottom', fontsize=SMALL_ANNOTATE_FONT)
    if path:
        plt.savefig(os.path.join(path, f"{file_name}.pdf"), bbox_inches='tight')
    else:
        plt.show()


def plot_percentage_bars(dict1, dict2,
                         dict1_label="Dataset 1", dict2_label="Dataset 2",
                         xlabel="Categories", ylabel="Percentage (%)",
                         path=None, file_name="percentage_bars_plot", size=FIGSIZE):
    """
    Plot two side-by-side bar charts of percentages for corresponding categories.

    Parameters:
    - dict1: dictionary mapping category -> percentage for first dataset
    - dict2: dictionary mapping category -> percentage for second dataset
    - dict1_label: label for the first dataset in the legend
    - dict2_label: label for the second dataset in the legend
    - xlabel: label for the x-axis (default: "Categories")
    - ylabel: label for the y-axis (default: "Percentage (%)")
    - path: optional folder path to save the plot (as PDF)
    - file_name: base filename (without extension) for saving
    - size: figure size tuple
    """
    dict1, dict2 = align_dict_keys(dict1, dict2)
    cats = list(dict1.keys())
    n_cat = len(cats)

    # Choose annotation font depending on number of categories (bars)
    if n_cat > 4:
        annotate_font = SMALL_ANNOTATE_FONT
    else:
        annotate_font = ANNOTATE_FONT

    v1 = [dict1[c] for c in cats]
    v2 = [dict2[c] for c in cats]
    x = np.arange(n_cat)
    w = 0.35

    fig, ax = plt.subplots(figsize=size)
    bars1 = ax.bar(x - w / 2, v1, w, label=dict1_label, color='skyblue')
    bars2 = ax.bar(x + w / 2, v2, w, label=dict2_label, color='lightcoral')

    # Increase font size for axis labels
    ax.set_xlabel(xlabel, fontsize=BASE_FONT)
    ax.set_ylabel(ylabel, fontsize=BASE_FONT)

    # Set tick labels and make them bigger
    ax.set_xticks(x)
    ax.set_xticklabels(cats, rotation=45, ha="right")
    ax.tick_params(axis='x', labelsize=TICK_FONT)

    # Place legend outside on the top center with bigger font
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2, frameon=False, fontsize=LEGEND_FONT)

    # Annotate bars
    _annotate_bars(bars1, ax, fontsize=annotate_font)
    _annotate_bars(bars2, ax, fontsize=annotate_font)

    plt.tight_layout()
    if path:
        plt.savefig(f"{path}/{file_name}.pdf", bbox_inches='tight')
    else:
        plt.show()


def plot_grouped_stacked_percentage_bars(
        data1, data2,
        category_labels, subcategory_labels,
        dataset1_label="Dataset 1", dataset2_label="Dataset 2",
        xlabel="Categories", ylabel="Percentage (%)",
        colors=None,
        path=None, file_name="grouped_stacked_bars_plot", size=FIGSIZE
):
    """
    Plot two grouped & stacked percentage bar charts side by side.

    Parameters:
    - data1: list of dicts for first dataset; each dict maps subcategory -> percentage
    - data2: list of dicts for second dataset; same structure as data1
    - category_labels: list of category names (one per position on x-axis)
    - subcategory_labels: list of subcategory names (used for stacking)
    - dataset1_label: label to annotate under first group
    - dataset2_label: label to annotate under second group
    - xlabel: label for the x-axis (default: "Categories")
    - ylabel: label for the y-axis (default: "Percentage (%)")
    - colors: optional mapping or sequence of colors for subcategories
    - path: optional folder path to save the plot (as PDF)
    - file_name: base filename (without extension) for saving
    - size: figure size tuple
    """
    n_cat = len(category_labels)
    x = np.arange(n_cat)
    bar_w = 0.25
    spacing = 0.125

    # Choose annotation font depending on number of categories (bars)
    if n_cat > 3:
        annotate_font = SMALL_ANNOTATE_FONT
    else:
        annotate_font = ANNOTATE_FONT

    if colors is None:
        colors = plt.cm.Set1(np.linspace(0, 1, len(subcategory_labels)))
    cmap = {sub: col for sub, col in zip(subcategory_labels, colors)}

    fig, ax = plt.subplots(figsize=size)

    # Plot datasets side by side
    for data, offset, ds_label in zip(
            [data1, data2],
            [-bar_w / 2 - spacing / 2, bar_w / 2 + spacing / 2],
            [dataset1_label, dataset2_label]
    ):
        bottoms = np.zeros(n_cat)
        for subcat in subcategory_labels:
            heights = [d.get(subcat, 0) for d in data]
            bars = ax.bar(x + offset, heights, bar_w, bottom=bottoms, color=cmap[subcat])
            _annotate_bars_stacked(bars, bottoms, heights, ax, fontsize=annotate_font)
            bottoms += heights
        # Annotate dataset label under bars
        for xi in x:
            ax.text(xi + offset, -6, ds_label, ha='center', va='top', fontsize=annotate_font)

    # Increase font size for axis labels
    ax.set_xlabel(xlabel, fontsize=BASE_FONT)
    ax.set_ylabel(ylabel, fontsize=BASE_FONT)

    ax.set_xticks(x)
    ax.set_xticklabels(category_labels, rotation=45, ha="right")
    ax.tick_params(axis='x', labelsize=TICK_FONT)

    # Legend outside on the right with bigger font

    # Place legend outside on the top center bigger font
    ax.legend(subcategory_labels, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=4, frameon=False, fontsize=LEGEND_FONT)

    # ax.legend(subcategory_labels, title="Modalities", loc='upper left', bbox_to_anchor=(1.02, 1),
    #           frameon=False, fontsize=LEGEND_FONT, title_fontsize=LEGEND_FONT)

    ax.set_ylim(-15, 105)
    plt.tight_layout()
    fig.subplots_adjust(bottom=0.3, right=0.825)
    if path:
        plt.savefig(f"{path}/{file_name}.pdf", bbox_inches='tight')
    else:
        plt.show()


def plot_bubble_chart(categories, modes, data, colors,
                      xlabel="Categories", ylabel="",
                      path=None, file_name="bubble_chart_plot", size=FIGSIZE):
    """
    Plot a bubble chart where each row corresponds to a mode and each column to a category.

    Parameters:
    - categories: list of category names (x-axis)
    - modes: list of mode names (rows in the bubble chart)
    - data: dict mapping mode -> list of values (percentages) for each category
    - colors: dict mapping mode -> color string
    - xlabel: label for the x-axis (default: "Categories")
    - ylabel: label for the y-axis (default: "")
    - path: optional folder path to save the plot (as PDF)
    - file_name: base filename (without extension) for saving
    - size: figure size tuple
    """
    fig, ax = plt.subplots(figsize=size)
    x = np.arange(len(categories))

    for idx, (mode, vals) in enumerate(data.items()):
        sizes = np.array(vals) * 80
        ax.scatter(x, [idx] * len(vals), s=sizes, color=colors.get(mode), alpha=0.8)
        for xi, yi, v in zip(x, [idx] * len(vals), vals):
            if v >= BUBBLE_LABEL_THRESHOLD:
                ax.text(xi, yi, f"{v:.1f}", ha="center", va="center", fontsize=SMALL_ANNOTATE_FONT, color="white",
                        weight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha="right")
    ax.tick_params(axis='x', labelsize=TICK_FONT)

    # Increase font size for axis labels
    ax.set_xlabel(xlabel, fontsize=BASE_FONT)
    ax.set_ylabel(ylabel, fontsize=BASE_FONT)

    # Remove y-axis ticks (modes are implied by rows)
    ax.set_yticks([])
    ax.grid(axis="x", linestyle="-", alpha=0.8)
    ax.margins(x=0.1, y=0.2)
    fig.subplots_adjust(left=0.1, right=0.825, bottom=0.15)

    # Legend outside on the right with bigger font
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label=mode, markerfacecolor=colors.get(mode), markersize=8)
        for mode in modes
    ]

    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=4, frameon=False,
              fontsize=LEGEND_FONT)
    # ax.legend(handles=legend_elements, title="Modalities", loc='upper left', bbox_to_anchor=(1.02, 1),
    #           frameon=False, fontsize=LEGEND_FONT, title_fontsize=LEGEND_FONT)

    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.tight_layout()
    if path:
        plt.savefig(f"{path}/{file_name}.pdf", bbox_inches='tight')
    else:
        plt.show()
