import requests
import pandas as pd
from utils import update_datetime
from statics import API_NAME_OANDA_PRACTICE
from statics import PARAMS_NAME_OANDA_ACC, PARAMS_NAME_OANDA_COUNT, \
    PARAMS_NAME_OANDA_END, PARAMS_NAME_OANDA_START, PARAMS_NAME_OANDA_D_ALIGN, \
    PARAMS_NAME_OANDA_W_ALIGN, PARAMS_NAME_OANDA_INSTRUMENT, \
    PARAMS_NAME_OANDA_BAR_FORMAT, PARAMS_NAME_OANDA_GRANULARITY, \
    PARAMS_NAME_OANDA_TZ_ALIGN
from statics import URL_OANDA_INSTRUMENTS, URL_OANDA_BARS, URL_OANDA_ACC
from statics import OANDAPracticeConfig
from errors import ApiRequestError, ApiClientError

__author__ = 'zed'


# ----------------------------------------------------------------------
# OANDA Client Object


class OANDAClient:
    """

    """

    __api_name = API_NAME_OANDA_PRACTICE

    def __init__(self, config):
        """

        :param config: OANDAPracticeConfig object; contains all information
        used to make requests to OANDA server.
        :return:
        """
        if config.__class__ == OANDAPracticeConfig:
            self.config = config
            self.header = config.body['header']
            self.account_id = config.body['account_id']
        else:
            msg = '[API]: Cannot construct, invalid config.'
            raise ApiClientError(msg)

    def __access(self, url, method, params):
        """

        :param url: string; url that is to be accessed.
        :param params: dict; request parameters.
        :param method: string<enum>; 'GET' or 'POST'.
        :return: resp: requests.models.Response; The response.
        """
        # Type check.
        if type(url) != str or type(params) != dict \
                or method not in ['GET', 'POST']:
            msg = '[API]: Invalid url/requestParams/method type(s).'
            raise TypeError(msg)

        s = requests.session()
        # prepare and send the request.
        try:
            if method == 'GET':
                req = requests.Request(method, url=url,
                                       headers=self.header, params=params)
            else:  # elif method == 'POST'
                req = requests.Request(method, url=url,
                                       headers=self.header, data=params)
            # for POST, params should be included in request body.
            prepped = s.prepare_request(req)  # prepare the request
            resp = s.send(prepped, stream=False, verify=True)

            # Check response code.
            if resp.status_code != 200:
                msg = '[API]: Bad request, unexpected response status: ' + \
                      str(resp.status_code)
                raise ApiRequestError(msg)

            return resp
        except Exception, e:
            msg = '[API]: Bad request.' + str(e)
            raise ApiRequestError(msg)

    def get_instruments(self):
        """
        Get instruments list.
        :return: requests.models.Response; The response.
        """
        return self.__access(URL_OANDA_INSTRUMENTS, 'GET',
                             {PARAMS_NAME_OANDA_ACC: self.account_id})

    def get_account(self):
        """
        Get account info.
        :return: requests.models.Response; The response.
        """
        url = URL_OANDA_ACC + '/{}'.format(self.account_id)
        return self.__access(url, 'GET', dict())

    def __retrieve_bars(self, instrument, granularity, count=500,
                        candle_format='midpoint', daily_alignment=None,
                        alignment_timezone=None, weekly_alignment="Monday",
                        start=None, end=None):
        """
        Retrieve historical bar data of certain instrument.

        :param instrument: string; the name of instrument.

        :param granularity: granularity: string<structured>;
        sample rate of bar data.
            <Examples>:
                - 'S10' 10-seconds bar.
                - 'M1' 1-minute bar.
                - 'H3' 3-hours bar.
                - 'D'/'W'/'M' day/week/month(one).

        :param count: int; the number of bars to be retrieved, maximum is
        5000, should not be specified if both start and end are specified.
            <Default>: 500.

        :param candle_format: string<enums[2]>; candlestick representation.
            <Values>:
                - 'bidask', the Bid/Ask based candlestick.
                - <Default>'midpoint', the midpoint based candlestick.

        :param daily_alignment: int; the hour of day used to align candles
        with hourly, daily, weekly, or monthly granularity. Note that
        The value specified here is interpreted as an hour in the timezone
        set through the alignment_timezone parameter.
            <Default>: None.

        :param alignment_timezone: string; timezone used for daily alignment.
            <Default>: None.

        :param weekly_alignment: string; the day of the week used to align
        candles with weekly granularity.
            <Default>: 'Monday'.

        :param start: string; timestamp for the start of candles requested.
            <Default>: None.

        :param end: string; timestamp for the end of candles requested.
            <Default>: None.

        :return: requests.models.Response; The response.
        """
        params = {
            PARAMS_NAME_OANDA_ACC: self.account_id,
            PARAMS_NAME_OANDA_INSTRUMENT: instrument,
            PARAMS_NAME_OANDA_GRANULARITY: granularity,
            PARAMS_NAME_OANDA_BAR_FORMAT: candle_format,
            PARAMS_NAME_OANDA_COUNT: count,
            PARAMS_NAME_OANDA_D_ALIGN: daily_alignment,
            PARAMS_NAME_OANDA_TZ_ALIGN: alignment_timezone,
            PARAMS_NAME_OANDA_W_ALIGN: weekly_alignment,
            PARAMS_NAME_OANDA_START: start,
            PARAMS_NAME_OANDA_END: end
        }
        return self.__access(URL_OANDA_BARS, 'GET', params)

    def get_bars(self, instrument, granularity, count=500,):
        """
        Wrapper of __retrieve_bars()
        :param instrument: refer to __retrieve_bars()
        :param granularity: refer to __retrieve_bars()
        :param count: refer to __retrieve_bars()
        :return: pd.DataFrame object.
        """
        data = self.__retrieve_bars(
            instrument, granularity, count).json()['candles']
        map(update_datetime, data)
        return pd.DataFrame(data)


