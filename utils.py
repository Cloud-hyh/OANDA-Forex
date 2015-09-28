import pandas as pd
from datetime import datetime, timedelta

from statics import BarColNames

__author__ = 'zed'


# ----------------------------------------------------------------------
# Utils Methods


def serialize_dict(dic):
    """
    Serialize and copy a dictionary to one with string values.
    WITHOUT changing its values.
    :return: dict.
    """
    serialized_dic = dict()
    for d in dic:
        serialized_dic[d] = str(dic[d])
    return serialized_dic


def serialize_merge_dict(dic1, dic2):
    """
    Serialize and copy two dictionaries to one with string values.
    WITHOUT changing their values.
    :return: dict.
    """
    serialized_dic = dict()
    for d in dic1:
        serialized_dic[d] = str(dic1[d])
    for d in dic2:
        serialized_dic[d] = str(dic2[d])
    return serialized_dic


def map_to_holding_values(positions, prices):
    """
    Map prices to multiple positions and calculate holding values.
    :param positions: list; the list of Position objects.
    :param prices: dict; {instrument: current price} pairs.
    :return: list; a list of holding values corresponding to positions.
    """
    if len(prices) == 1:  # trivial case.
        curr_price = prices.values()[0]
        return [p.holding_value(curr_price) for p in positions]
    else:
        return [p.holding_value(prices[p.body['instrument']])
                for p in positions]


def map_to_unrealized_pnl(positions, prices):
    """
    Map prices to multiple positions and calculate unrealized pnl.
    :param positions: list; the list of Position objects.
    :param prices: dict; {instrument: current price} pairs.
    :return: list; a list of holding values corresponding to positions.
    """
    if len(prices) == 1:  # trivial case.
        curr_price = prices.values()[0]
        return [p.unrealized_pnl(curr_price) for p in positions]
    else:
        return [p.unrealized_pnl(prices[p.body['instrument']])
                for p in positions]


def map_dt_to_indices(complete_series, series):
    """
    Use complete series to construct mapping, then map series.dt to
    corresponding indices.
    :param complete_series:
    :param series:
    :return:
    """
    mapping = dict(zip(list))


def update_datetime(d):
    """
    Update dictionary with timestamps with datetime attribute.
    :param d: dict
    :return:
    """
    d.update({'datetime': datetime.fromtimestamp(
        int(d['time']) / 1000000)})


def ensure_time_format(time_labels):
    """
    Determine time format according to time_labels' frequency
    :param time_labels:
    :return:
    """
    if time_labels[1] - time_labels[0] < timedelta(days=1):
        time_format = '%Y-%m-%d %H:%M:%S'
    else:
        time_format = '%Y-%m-%d'
    return time_format


def extract_columns_less(data):
    """
    Extract series from dataframe.
    :param data: pd.DataFrame; bar dataframe.
    :return:
    """
    indices = data.index
    close_series = data[BarColNames.close.value]
    volume_series = data[BarColNames.volume.value]
    time_labels = data[BarColNames.time.value]
    return indices, close_series, volume_series, time_labels


def sma(series, window):
    """
    Simple moving average.
    :param series:
    :param window:
    :return:
    """
    return pd.rolling_mean(pd.Series(series), window)
