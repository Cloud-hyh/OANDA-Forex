import json
from enum import Enum

__author__ = 'zed'

# ----------------------------------------------------------------------
# Const Definitions

API_NAME_VOID = 'API_VOID'
API_NAME_OANDA_SANDBOX = 'API_OANDA_SANDBOX'
API_NAME_OANDA_PRACTICE = 'API_OANDA_PRACTICE'

PARAMS_NAME_OANDA_ACC = 'accountId'
PARAMS_NAME_OANDA_INSTRUMENT = 'instrument'
PARAMS_NAME_OANDA_BAR_FORMAT = 'candleFormat'
PARAMS_NAME_OANDA_GRANULARITY = 'granularity'
PARAMS_NAME_OANDA_COUNT = 'count'
PARAMS_NAME_OANDA_D_ALIGN = 'dailyAlignment'
PARAMS_NAME_OANDA_W_ALIGN = 'weeklyAlignment'
PARAMS_NAME_OANDA_TZ_ALIGN = 'alignmentTimezone'
PARAMS_NAME_OANDA_START = 'start'
PARAMS_NAME_OANDA_END = 'end'

RESP_NAME_OANDA_BARS = 'candles'
RESP_NAME_OANDA_TIME = 'time'

URL_OANDA_DOMAIN = 'https://api-fxpractice.oanda.com'
URL_OANDA_STREAM = 'https://stream-fxpractice.oanda.com'
URL_OANDA_INSTRUMENTS = URL_OANDA_DOMAIN + '/v1/instruments'
URL_OANDA_ACC = URL_OANDA_DOMAIN + '/v1/accounts'
URL_OANDA_BARS = URL_OANDA_DOMAIN + '/v1/candles'


class BarColNames(Enum):
    close = 'closeMid'
    open = 'openMid'
    high = 'highMid'
    low = 'lowMid'
    time = 'datetime'
    volume = 'volume'


class OrderType(Enum):
    buy = 'ORD_BUY'
    short = 'ORD_SHORT'
    fill = 'ORD_FILL'
    sell = 'ORD_SELL'

    # TODO: extended orders
    limit_buy = 'ORD_LIMIT_BUY'
    limit_sell = 'ORD_LIMIT_SELL'
    take_profit = 'ORD_TAKE_PROFIT'
    stop_loss = 'ORD_STOP_LOSS'
    none = 'ORD_NONE'


class PositionType(Enum):
    long = 'POS_LONG'
    short = 'POS_SHORT'
    none = 'POS_NONE'


class PositionStatus(Enum):
    open = 'POS_OPENING'
    closed = 'POS_CLOSED'


class TradingExecuteFlag(Enum):
    good = 'TRADE_SUCCESSFUL'
    bad = 'TRADE_FAILED'


class CurrencyType(Enum):
    USD = 'CURRENCY_US_DOLLAR'
    EUR = 'CURRENCY_EURO'
    JPY = 'CURRENCY_JAPAN_YEN'
    CNY = 'CURRENCY_CHN_YUAN'
    CAD = 'CURRENCY_CANADA_DOLLAR'


ORD_POS_MAPPING = {
    OrderType.buy: PositionType.long,
    OrderType.short: PositionType.short
}


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

# ----------------------------------------------------------------------
# Config objects.


class ConfigTemplate:
    """

    """
    __api_name = API_NAME_VOID

    def __init__(self, body):
        """
        :param body:
        :return:
        """
        self.body = body

    def view(self):
        """
        Serialize self.body to a message.
        :return:
        """
        print json.dumps(serialize_dict(self.body),
                         indent=4, sort_keys=True)


class OANDAPracticeConfig(ConfigTemplate):
    """

    """
    __api_name = API_NAME_OANDA_PRACTICE

    def __init__(self):
        """
        Constructor for OANDA Practice API Config.
        :return:
        """
        token = 'af755ad66f0c3db4da0b886c93c114f2-' \
                '799e7d60d85fb3b3c58cfe3ba9d8fe25'
        body = {
            'username': 'zedyang',
            'password': 'cmbjx1008',
            'account_id': 8878848,
            'domain': 'api-fxpractice.oanda.com',  # sandbox environment
            'domain_stream': 'stream-fxpractice.oanda.com',
            'ssl': True,  # http or https.
            'version': 'v1',
            'header': {
                "Content-Type": "application/x-www-form-urlencoded",
                'Connection': 'keep-alive',
                'Authorization': 'Bearer ' + token,
                'X-Accept-Datetime-Format': 'unix'
            }
        }
        # Superclass initialization.
        ConfigTemplate.__init__(self, body)
