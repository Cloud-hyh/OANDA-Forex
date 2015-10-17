import matplotlib
import matplotlib.ticker
import matplotlib.pyplot as plt

from utils import extract_columns_less, ensure_time_format, sma
from statics import OrderType

__author__ = 'zed'


def report(kernel, fig_size=(16, 10), ma1=12, ma2=26):
    """

    :param kernel:
    :param fig_size:
    :param ma1:
    :param ma2:
    :return:
    """
    # export data.
    data = kernel.data
    nav_series = kernel.account.record_nav
    positions = kernel.export_positions()
    orders = kernel.export_executed_orders()
    pnls = positions['realized_pnl']
    long_orders = orders[(orders['direction'] == OrderType.buy) |
                         (orders['direction'] == OrderType.fill)]
    short_orders = orders[(orders['direction'] == OrderType.sell) |
                          (orders['direction'] == OrderType.short)]
    # clean data.
    indices, close_series, volume_series, time_labels = \
        extract_columns_less(data)
    long_order_time_labels = long_orders['time']
    short_order_time_labels = short_orders['time']
    long_order_indices = [i for i in range(len(data))
                          if time_labels[i] in list(long_order_time_labels)]
    short_order_indices = [i for i in range(len(data))
                           if time_labels[i] in list(short_order_time_labels)]
    win_pnl = [pnl for pnl in pnls if pnl > 0]
    lose_pnl = [pnl for pnl in pnls if pnl <= 0]

    # Make plot.
    fig = plt.figure(figsize=fig_size)
    plt.gca().yaxis.set_major_locator(
        matplotlib.ticker.MaxNLocator(prune='lower'))
    plt.subplots_adjust(left=.07, bottom=.10,
                        right=.94, top=.95,
                        wspace=.24, hspace=.0)

    ax_equity = plt.subplot2grid((6, 8), (0, 0), rowspan=2, colspan=6)
    ax_equity.set_ylabel('Net Asset Value')
    ax_benchmark = plt.subplot2grid((6, 8), (2, 0), rowspan=2, colspan=6)
    ax_benchmark.set_ylabel('Forex Rate and Volume')
    ax_position_pnl = plt.subplot2grid((6, 8), (2, 6), rowspan=2, colspan=2)

    ax_position_pnl = histogram_win_loss_pnl(ax_position_pnl,
                                             win_pnl, lose_pnl, len(pnls)/2)
    ax_benchmark = plot_ts(ax_benchmark, data, ma1, ma2)
    ax_equity = plot_nav(ax_equity, nav_series, time_labels,
                         long_order_indices, short_order_indices)

    ax_equity.axes.xaxis.set_ticklabels([])
    #ax_position_pnl.axes.yaxis.set_ticklabels([])
    return ax_position_pnl, ax_benchmark, ax_equity


def plot_ts(ax, data, ma1=None, ma2=None, max_locator=10, text_rotation=30):
    """

    :param ax:
    :param data:
    :param ma1:
    :param ma2:
    :param max_locator:
    :param text_rotation:
    :return:
    """
    indices, close_series, volume_series, time_labels = \
        extract_columns_less(data)
    volume_min = 0
    # Determine time format.
    time_format = ensure_time_format(time_labels)

    # Main series.
    ax.plot(indices, close_series, label="rate", linewidth=0.8)
    if type(ma1) == int:
        sma_series1 = sma(close_series, ma1)
        ax.plot(indices, sma_series1, label="ma1", linewidth=0.5)
    if type(ma2) == int:
        sma_series2 = sma(close_series, ma2)
        ax.plot(indices, sma_series2, label="ma2", linewidth=0.5)
    # Settings.
    ax.set_xticklabels([dt.strftime(time_format) for dt in list(
        time_labels)[0::len(data) / (max_locator + 1)]])
    [label.set_rotation(text_rotation) for label in ax.xaxis.get_ticklabels()]
    # Number of x-tickers.
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(max_locator))
    ax.grid(True)
    ax_vol = embed_volume_plot(ax, indices, volume_series, volume_min)
    return ax, ax_vol


def embed_volume_plot(ax, indices, volume_series, volume_threshold):
    """

    :param ax:
    :param indices:
    :param volume_series:
    :return:
    """
    ax_vol = ax.twinx()
    ax_vol.fill_between(indices, volume_threshold, volume_series,
                        facecolor='black', alpha=.12)
    # Settings.
    ax_vol.grid(False)
    ax_vol.axes.yaxis.set_ticklabels([])
    ax_vol.set_ylim(0, 1.4 * volume_series.max())
    return ax_vol


def plot_nav(ax, nav_series, time_labels, long_orders=None, short_orders=None,
             max_locator=10, text_rotation=30):
    """

    :param ax:
    :param nav_series:
    :param time_labels:
    :param long_orders:
    :param short_orders:
    :param max_locator:
    :param text_rotation:
    :return:
    """
    time_format = ensure_time_format(time_labels)

    # Settings.
    ax.set_xticklabels([dt.strftime(time_format) for dt in list(
        time_labels)[0::(len(time_labels) / max_locator)]])
    [label.set_rotation(text_rotation) for label in ax.xaxis.get_ticklabels()]
    # Number of x-tickers.
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(max_locator))

    ax.grid(True)
    # Plot orders
    if long_orders:
        for x in long_orders:
            ax.axvline(x, linestyle='-', linewidth=0.5, alpha=0.5, color='green')
    if short_orders:
        for x in short_orders:
            ax.axvline(x, linestyle='-', linewidth=0.5, alpha=0.5, color='red')
    # Main series.
    ax.fill_between(range(len(nav_series)), nav_series[0], nav_series,
                    facecolor='blue', alpha=.1)
    ax.plot(range(len(time_labels)), nav_series, label='nav',
            linewidth=1, alpha=1)
    return ax


def histogram_win_loss_pnl(ax, win_pnl, lose_pnl, num_bins):
    """

    :param ax:
    :param win_pnl:
    :param lose_pnl:
    :param num_bins:
    :return:
    """
    pnls = win_pnl + lose_pnl
    ax.grid(True)
    ax.hist(win_pnl, num_bins, color='blue', alpha=0.7)
    ax.hist(lose_pnl, num_bins, color='red', alpha=0.7)
    return ax
