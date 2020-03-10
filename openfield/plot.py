import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib import dates, cm
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

def heatmap(hourly_utci_values, plot_type="utci", location_string=None, tone_color="#555555", save_path=None, cb_orientation="horizontal"):

    idx = pd.date_range(start="2018-01-01 00:00:00", end="2019-01-01 00:00:00", freq="60T", closed="left")

    # Data preparation
    if plot_type == "comfort":
        bins = [-1000, -40, -27, -13, 0, 9, 26, 32, 38, 46, 1000]
        bins_replacement = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4]
        series = pd.Series(
            pd.cut(pd.Series(np.array(hourly_utci_values)), bins, labels=bins_replacement).astype(int).values,
            name="Universal Thermal Climate Index", index=idx)
        cmap = ListedColormap(colors=['#0D104B', '#262972', '#3452A4', '#3C65AF', '#37BCED', '#2EB349',
                                      '#F38322', '#C31F25', '#7F1416', '#580002'])
        cb_lims = [-5.5, 4.5]
        bounds = np.arange(-5, 6, 1)
        cb_ticks = bounds
        cb_tick_labels = ["Extreme\nheat stress", "Very strong\nheat stress", "Strong\nheat stress",
                          "Moderate\nheat stress", "No\nthermal stress", "Slight\ncold stress",
                          "Moderate\ncold stress", "Strong\ncold stress", "Very strong\ncold stress",
                          "Extreme\ncold stress"][::-1]
        cb_label = "UTCI heat stress category"
    elif plot_type == "utci":
        series = pd.Series(hourly_utci_values, name="Universal Thermal Climate Index", index=idx)
        cmap = cm.get_cmap("magma")
        cb_lims = [-40, 46]
        bounds = np.arange(-40, 47, 1)
        cb_ticks = np.arange(cb_lims[0], cb_lims[-1] + 1, 5)
        cb_tick_labels = cb_ticks
        cb_label = "UTCI °C"
    elif plot_type == "diff":
        series = pd.Series(hourly_utci_values, name="Universal Thermal Climate Index Comparison", index=idx)
        cmap = cm.get_cmap("RdBu_r")
        cb_lims = [-5, 5]
        bounds = np.arange(-5, 6, 1)
        cb_ticks = np.arange(cb_lims[0], cb_lims[-1] + 1, 1)
        cb_tick_labels = cb_ticks
        cb_label = "UTCI difference °C"

    df = series.to_frame()
    title = "{} - {}".format(location_string, series.name) if location_string else "{}".format(series.name)

    # Data plotting
    fig, ax = plt.subplots(1, 1, figsize=(15, 5))
    heatmap = ax.imshow(
        pd.pivot_table(df, index=df.index.time, columns=df.index.date, values=series.name).values[::-1],
        extent=[dates.date2num(df.index.min()), dates.date2num(df.index.max()), 726449, 726450],
        aspect='auto', cmap=cmap, interpolation='none', vmin=bounds.min(), vmax=bounds.max())

    # Axes formatting
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(dates.DateFormatter('%b'))
    ax.yaxis_date()
    ax.yaxis.set_major_formatter(dates.DateFormatter('%H:%M'))
    ax.invert_yaxis()

    # Ticks, labels and spines formatting
    ax.tick_params(labelleft=True, labelbottom=True)
    plt.setp(ax.get_xticklabels(), ha='left', color=tone_color)
    plt.setp(ax.get_yticklabels(), color=tone_color)
    [ax.spines[spine].set_visible(False) for spine in ['top', 'bottom', 'left', 'right']]
    ax.grid(b=True, which='major', color='white', linestyle='--', alpha=0.9)
    [tick.set_color(tone_color) for tick in ax.get_yticklines()]
    [tick.set_color(tone_color) for tick in ax.get_xticklines()]

    # Colorbar
    heatmap.set_clim(cb_lims[0], cb_lims[-1])
    if cb_orientation == "horizontal":
        cb = fig.colorbar(heatmap, cmap=cmap, orientation='horizontal', drawedges=False, ticks=cb_ticks, fraction=0.05, aspect=100, pad=0.125)  #
        plt.setp(plt.getp(cb.ax.axes, 'xticklabels'), color=tone_color)
        [tick.set_color(tone_color) for tick in cb.ax.axes.get_xticklines()]
        cb.ax.axes.set_xticklabels(cb_tick_labels, fontsize="medium")
        cb.ax.set_xlabel(cb_label, fontsize="medium", color=tone_color)
        cb.ax.xaxis.set_label_position('top')
    elif cb_orientation == "vertical":
        cb = fig.colorbar(heatmap, cmap=cmap, orientation='vertical', drawedges=False, ticks=cb_ticks, fraction=0.05, aspect=20, pad=0.075)  # , fraction=0.05, aspect=20, pad=0.075
        cb.ax.yaxis.set_ticks_position('left')
        plt.setp(plt.getp(cb.ax.axes, 'yticklabels'), color=tone_color)
        [tick.set_color(tone_color) for tick in cb.ax.axes.get_yticklines()]
        cb.ax.axes.set_yticklabels(cb_tick_labels, fontsize="small")
    cb.outline.set_visible(False)

    # Title
    ax.set_title(title, color=tone_color, ha="left", va="bottom", x=0)

    # Tidy up
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, bbox_inches="tight", dpi=300, transparent=False)
