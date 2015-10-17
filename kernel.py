import json
import numpy as np
import pandas as pd

from utils import serialize_dict, serialize_merge_dict, \
    map_to_unrealized_pnl, map_to_holding_values

from statics import OrderType, PositionType, PositionStatus, CurrencyType, \
    TradingExecuteFlag, BarColNames, ORD_POS_MAPPING
from errors import KernelOrderError, KernelPositionError, KernelAccountError, \
    KernelBacktestError
__author__ = 'zed'

# ----------------------------------------------------------------------
# Order object.


class Order:
    """
    Json-like trading order profile object.
    <example>
        body = {
            'instrument': 'EUR_USD',
            'direction': 'ORD_SHORT',
            'time': datetime(2015,10,08,12,0,0),
            'price': 2.588,
            'volume': 100,
        }
    """
    __keys = ['instrument', 'direction', 'time', 'price', 'volume', 'target']

    def __init__(self, instrument, direction, time, price, volume,
                 target_id=None):
        """
        Constructor.
        :param instrument: String; name of instrument.
        :param direction: OrderType(Enum[5]) object; order direction.
            <Values>:
                - OrderType.buy = 'ORD_BUY'
                - OrderType.short = 'ORD_SHORT'
                - OrderType.fill = 'ORD_FILL'
                - OrderType.sell = 'ORD_SELL'
                - OrderType.none = 'ORD_NONE'
        :param time: datetime.datetime object; placement time.
        :param price: double.
        :param volume: int/double; Required only by buy/short order.
        :param target_id: <>; target position id.
            <Default>: None, Required only by partial sell/fill order.
        :return:
        """
        # Type check.
        if self.__type_check(direction):
            values = [instrument, direction, time, price, volume, target_id]
            self.body = dict(zip(self.__keys, values))
            self.instrument = values[0]
            self.direction = values[1]

    @staticmethod
    def __type_check(direction):
        """
        Type check for constructor
        :return:
        """
        if not direction.__class__ == OrderType:
            msg = '[KERNEL::Order]: Unable to construct Order object. '
            raise KernelOrderError(msg)
        return True

    @classmethod
    def open(cls, instrument, direction, time, price, volume):
        """
        Reload constructor for order that opens a position.
        :return: Order object.
        """
        # Type check.
        if not (direction in [OrderType.buy, OrderType.short]):
            msg = '[KERNEL::Order]: Unable to construct Order object. '
            raise KernelOrderError(msg)
        return cls(instrument, direction, time, price, volume)

    @classmethod
    def close(cls, instrument, direction, time, price):
        """
        Reload constructor for order that closes a position.
        Does not require volume parameter.
        :return: Order object.
        """
        # Type check.
        if not (direction in [OrderType.sell, OrderType.fill]):
            msg = '[KERNEL::Order]: Unable to construct Order object. '
            raise KernelOrderError(msg)
        return cls(instrument, direction, time, price, None)

    @classmethod
    def close_partial(cls, instrument, direction, time, price,
                      volume, target_id):
        """
        Reload constructor for order that partially closes a position.
        :return: Order object.
        """
        # Type check.
        if not (direction in [OrderType.sell, OrderType.fill]):
            msg = '[KERNEL::Order]: Unable to construct Order object. '
            raise KernelOrderError(msg)
        return cls(instrument, direction, time, price, volume, target_id)

    def cash_flow(self):
        """
        :return: double; order cash flow.
        """
        return self.body['volume'] * self.body['price']

    def export_price_dict(self):
        """
        :return: dict; {instrument: price} pair.
        """
        return {self.instrument: self.body['price']}

    def export_to_position(self):
        """
        Export data in order to construct corresponding Position.
        For OrderType in [buy, short].
        :return: list; [instrument, PositionType, vol, time, price]
        """
        return [self.body['instrument'], ORD_POS_MAPPING[self.direction],
                self.body['volume'], self.body['time'], self.body['price']]

    def export_time_price(self):
        """
        Export data in order to close Position.
        For OrderType in [sell, fill],
        :return: list; [time, price]
        """
        return [self.body['time'], self.body['price']]

    def view(self):
        """
        Print order.
        :return:
        """
        print json.dumps(serialize_dict(self.body), indent=4, sort_keys=True)

# ----------------------------------------------------------------------
# Position object.


class Position:
    """
    Json-like position log object.

    <privates>
        - status: status flag.
            - POSITION_STATUS_OPEN = 'POS_OPENING'
            - POSITION_STATUS_CLOSED = 'POS_CLOSED'
        - body: dict; position content.

            <example>
            body = {
                'instrument': 'EUR_USD',
                'direction': 'POS_LONG',
                'volume': 10000,
                'openTime': datetime(2015,9,12,0,0,0),
                'openPrice': 1.8502,
                'closeTime': datetime(2015,9,15,0,0,0),
                'closePrice': 1.8507,
                'realizedPnL': 5,
    """
    # Keys of self.body dict.
    __keys = ['instrument', 'direction', 'volume', 'open_time', 'open_price',
              'close_time', 'close_price', 'realized_pnl']
    __keys_open = ['instrument', 'direction', 'volume',
                   'open_time', 'open_price']
    __keys_close = ['close_time', 'close_price']

    def __init__(self, order):
        """
        Constructor.
        :param order: Order object; with order.direction either buy/short.
        :return:
        """
        if self.__type_check(order):
            values = order.export_to_position()
            self.body = dict(zip(self.__keys_open, values))
            self.status = PositionStatus.open
            self.direction = self.body['direction']

    @staticmethod
    def __type_check(order):
        """
        Type check for constructor.
        :return:
        """
        if order.direction not in [OrderType.buy, OrderType.short]:
            msg = '[KERNEL::Position]: Unable to construct Position object. '
            raise KernelPositionError(msg)
        return True

    def __is_open(self):
        """
        Check status.
        :return: boolean; True if status is open.
        """
        return self.status == PositionStatus.open

    def view(self, curr_price=None):
        """
        Print position with/without unrealized pnl.
        :param curr_price: double; current price.
            <Default>: None; do not print unrealized pnl.
        :return:
        """
        if (curr_price is not None) and (self.status == PositionStatus.open):
            d = {'unrealized_pnl': self.unrealized_pnl(curr_price)}
            print json.dumps(serialize_merge_dict(self.body, d),
                             indent=4, sort_keys=True)
        else:
            print json.dumps(serialize_dict(self.body),
                             indent=4, sort_keys=True)

    def open_value(self):
        """
        :return: double; position's opening value
        """
        return self.body['open_price'] * self.body['volume']

    def close_value(self):
        """
        :return: double; position's closing value
        """
        return self.body['close_price'] * self.body['volume']

    def holding_value(self, curr_price):
        """
        Calculate an opening position's holding value.
        :param curr_price: double; current price.
        :return: double; calculated holding value.
        """
        # Check status
        if self.__is_open():
            return curr_price * self.body['volume']

    def unrealized_pnl(self, curr_price):
        """
        Calculate an opening position's unrealized pnl.
        :param curr_price: double; current price.
        :return: double; calculated unrealized pnl.
        """
        # Check status.
        if not self.__is_open():
            return
        if self.direction == PositionType.long:
            return self.body['volume'] * (curr_price - self.body['open_price'])
        elif self.direction == PositionType.short:
            return self.body['volume'] * (self.body['open_price'] - curr_price)

    def __realized_pnl(self):
        """
        Calculate realized pnl.
        :return: double; unrealized_pnl(self.body['close_price'])
        """
        return self.unrealized_pnl(self.body['close_price'])

    def close(self, order):
        """
        Close this position, calculate realized pnl and record.
        :param order: Order object.
        :return: double; realized pnl.
        """
        if not self.__is_open():
            return
        try:
            if self.direction == PositionType.short:
                assert order.direction == OrderType.fill
            elif self.direction == PositionType.long:
                assert order.direction == OrderType.sell
            # Update body.
            values = order.export_time_price()  # [time, price]
            self.body.update(dict(zip(self.__keys_close, values)))

            # Realize PnL:
            self.body['realized_pnl'] = self.__realized_pnl()

            # Close position.
            self.status = PositionStatus.closed
            # Return realized PnL
            return self.body['realized_pnl']
        except AssertionError:
            msg = '[KERNEL::Position]: Invalid order type ' \
                  'to close a position.'
            raise KernelPositionError(msg)


# ----------------------------------------------------------------------
# Account object.

class Account:
    """
    Trading account object.
    Suppose the account base is US dollar, then:
        - curr_balance has unit of USD.
        - positions [BASE/QUOTE: BID/ASK]: sell 1 base for (BID) quote currency.
          Buy 1 base at (ASK) quote currency.
          Sell 1 base then buy it back, pnl = -1 spread (quote) = BID-ASK < 0

        <notes>
            - [USD/JPY: 121.0000/121.0001]: volume-(USD), price*volume-(JPY)
                pnl-(JPY), margin_used(USD) <- volume.

            - [EUR/USD: 1.2204/1.2205]: volume-(EUR), price*volume-(USD)
                pnl-(USD), margin_used(USD) <- price*volume.

            - [EUR/HKD: 8.6107/8.6108]: volume-(EUR), price*volume-(HKD)
                pnl-(HKD), margin_used(USD) <- volume*(EUR/USD)
                (i.e. convert volume to USD)

        <invokes>
            - utils.map_to_holding_values(): return price*volume of Position,
              unit is quote currency.
            - utils.map_to_unrealized_pnl(): return realized pnl on a Position,
              unit is quote currency.

        <privates>
            * init_cash: double; initial balance.
            * leverage: int; account leverage setting.
            * base: string; base currency of the account.
    """

    def __init__(self, init_cash, leverage, base):
        """
        Constructor.
        :param init_cash: double/int; initial cash.
        :param leverage: int; leverage.
        :param base: CurrencyType(Enum); base currency of this account.
        :return:
        """
        if self.__type_check(init_cash, leverage, base):
            self.curr_balance = self.__init_cash = init_cash
            self.__leverage = leverage
            self.__margin_rate = 1.0/leverage
            self.__base = base

            # History Containers
            self.longs, self.shorts, self.closed = [], [], []
            self.record_longs, self.record_shorts, self.record_nav = [], [], []
            self.record_orders = []

    @staticmethod
    def __type_check(init_cash, leverage, base):
        """
        Type check for constructor
        :return:
        """
        if not (base.__class__ == CurrencyType and (
                        init_cash > 0 and leverage >= 1)):
            msg = '[KERNEL::Account]: Unable to construct Account object. '
            raise KernelAccountError(msg)
        return True

    @classmethod
    def usd_std(cls):
        """
        Construct a USD account with 1 million, leverage = 20.
        :return:
        """
        return cls(1000000, 20, CurrencyType.USD)

    def view(self, curr_prices=None):
        """
        View account.
        :param curr_prices: dict; {instrument: current price} pairs.
        :return:
        """
        prompt = {
            'base': self.__base,
            'leverage': self.__leverage,
            'marginRate': self.__margin_rate,
            'balance': self.curr_balance,
            'longPositions': [p.body for p in self.longs],
            'shortPositions': [p.body for p in self.shorts],
            'closedPositions': [p.body for p in self.closed]
        }
        if curr_prices:
            additional = {
                'nav': self.nav(curr_prices),
                'marginUsed': self.margin_used(curr_prices),
                'marginAvailable': self.margin_available(curr_prices)
            }
            prompt.update(additional)
        print json.dumps(serialize_dict(prompt), indent=4, sort_keys=True)

    def clear_all(self):
        """
        Reset account.
        :return:
        """
        self.curr_balance = self.__init_cash
        self.longs, self.shorts, self.closed = [], [], []
        # Historical log
        self.record_nav, self.record_orders = [], []
        self.record_longs, self.record_shorts = [], []

    def nav(self, curr_prices):
        """
        Calculate net asset value.
        :param curr_prices: dict; {instrument: current price} pairs.
        :return: double; nav.
        """
        # list of unrealized pnl:
        unrealized_pnl = map_to_unrealized_pnl(
            positions=(self.longs+self.shorts),
            prices=curr_prices)
        return self.curr_balance + sum(unrealized_pnl)

    def margin_used(self, curr_prices):
        """
        Calculate margin used.
        :param curr_prices: dict; {instrument: current price} pairs.
        :return: double; margin used.
        """
        holding_values = map_to_holding_values(
            self.longs+self.shorts, curr_prices)
        return sum(holding_values) * self.__margin_rate

    def margin_available(self, curr_prices):
        """
        Calculate margin available.
        :param curr_prices: dict; {instrument: current price} pairs.
        :return: double; margin available.
        """
        return max(0, (self.nav(curr_prices)-self.margin_used(curr_prices)))

    def __to_sell(self):
        """
        Pop a long position.
        :return: Position object; or None, if self.longs is [].
        """
        return self.longs.pop() if self.longs else None

    def __to_fill(self):
        """
        Pop a short position.
        :return: Position object; or None, if self.shorts is [].
        """
        return self.shorts.pop() if self.shorts else None

    def __check_margin(self, order, curr_prices):
        """
        Check margin for an open order.
        :param order: Order object (buy/short).
        :param curr_prices: dict; {instrument: current price} pairs.
        :return: boolean; enough margin or not.
        """
        return (self.margin_available(curr_prices) >=
                order.cash_flow())

    def handle_mkt_order(self, order, curr_prices=-1):
        """
        Handle the order.
        :param order: Order object; order to be handled.
        :param curr_prices: dict; {instrument: current price} pairs.
            <Default>: -1; only one instrument, export pair from order.
        :return: TradingExecuteFlag(Enum[2]) object.
            - TradingExecuteFlag.good: trade was executed.
            - TradingExecuteFlag.bad: trade was not executed.
        """
        if order.direction == OrderType.none:   # If NONE order:
            return TradingExecuteFlag.bad
        # Account has single instrument.
        if curr_prices == -1:
            curr_prices = order.export_price_dict()
        # Buy/Short, prepare to open position.
        if order.direction in [OrderType.buy, OrderType.short]:
            # Check margin.
            if self.__check_margin(order, curr_prices):
                if order.direction == OrderType.short:
                    self.shorts.append(Position(order))
                elif order.direction == OrderType.buy:
                    self.longs.append(Position(order))
                return TradingExecuteFlag.good
            else:
                # Fail margin check.
                return TradingExecuteFlag.bad
        # Sell/Fill, prepare to close position.
        else:
            if order.direction == OrderType.fill:
                p = self.__to_fill()
            elif order.direction == OrderType.sell:
                p = self.__to_sell()
            else:
                p = None
            if p:
                this_realized_pnl = p.close(order)
                self.closed.append(p)
                # Update current balance.
                self.curr_balance += this_realized_pnl
                return TradingExecuteFlag.good
            else:
                return TradingExecuteFlag.bad

    def record_nav_ts(self, curr_prices):
        """
        Write current to record_nav timeseries.
        :param curr_prices: dict; {instrument: current price} pairs.
        :return:
        """
        # there won't be empty record.
        self.record_nav.append(self.nav(curr_prices))

    def record_executed_order(self, order):
        """

        :param order:
        :return:
        """
        self.record_orders.append(order)

    def record_position_ts(self, curr_prices):
        """
        Write current volumes, holding values
        to record_longs/shorts timeseries.
        :param curr_prices: dict; {instrument: current price} pairs.
        :return:
        """
        # Initialize as empty.
        long_record_one_row = {
            'instrument': None,
            'direction': PositionType.long,
            'volume': 0,
            'value': 0
        }
        short_record_one_row = {
            'instrument': None,
            'direction': PositionType.short,
            'volume': 0,
            'value': 0
        }
        # If opening positions list is non-empty:
        if self.longs:
            long_record_one_row['volume'] = sum(
                [p.body['volume'] for p in self.longs])
            long_record_one_row['value'] = sum(
                map_to_holding_values(self.longs, curr_prices))
        if self.shorts:
            short_record_one_row['volume'] = sum(
                [p.body['volume'] for p in self.shorts])
            short_record_one_row['value'] = sum(
                map_to_holding_values(self.shorts, curr_prices))
        # Write to main list.
        self.record_longs.append(long_record_one_row)
        self.record_shorts.append(short_record_one_row)

    def export_executed_orders(self):
        """

        :return:
        """
        all_executed_orders = [order.body for order in self.record_orders]
        return pd.DataFrame(all_executed_orders)

    def export_positions(self):
        """
        Export a frame of all Position objects.
        :return: pd.Dataframe object.
        """
        all_closed_positions = [p.body for p in self.closed]
        return pd.DataFrame(all_closed_positions)

    def export_long_position_ts(self):
        """
        Export time series of long position summaries.
        :return: pd.Dataframe object.
        """
        return pd.DataFrame(self.record_longs)

    def export_short_position_ts(self):
        """
        Export time series of short position summaries.
        :return: pd.Dataframe object.
        """
        return pd.DataFrame(self.record_shorts)

# ----------------------------------------------------------------------
# Backtest Kernel


class Kernel:
    """

    """

    def __init__(self, data, account):
        """

        :param data: pd.Dataframe object; bar data.
        :param account: Account object;
        :return:
        """
        if self.__type_check(account):
            self.data = data
            self.account = account

    @staticmethod
    def __type_check(account):
        """
        Type check for constructor
        :return:
        """
        if not (account.__class__ == Account):
            msg = '[KERNEL::Kernel]: Unable to construct backtest kernel. '
            raise KernelBacktestError(msg)
        return True

    @classmethod
    def naive(cls, data):
        """
        Naive one-instrument kernel using Account.usd_std()
        :return:
        """
        return cls(data, Account.usd_std())

    def __clear_all(self):
        """
        Clear all records.
        :return:
        """
        self.account.clear_all()

    def log(self, curr_prices, order):
        """

        :param curr_prices:
        :param order:
        :return:
        """
        self.account.record_nav_ts(curr_prices)
        self.account.record_position_ts(curr_prices)


    def run_naive(self, strategy):
        """
        Run backtest on strategy for <single instrument>.
        :param strategy: Strategy object.
        :return:
        """
        # Clear all records before running.
        self.__clear_all()
        instrument = strategy.instrument

        # Distribute bars.
        for row in self.data.iterrows():
            bar = row[1]    # row is tuple, [0]->index, [1]->data
            curr_prices = {instrument: bar[BarColNames.close.value]}
            curr_time = bar[BarColNames.time.value]

            # Run strategy logic.
            order_direction, volume = strategy.on_bar(bar)
            # Make order.
            order = Order(instrument=instrument,
                          direction=order_direction,
                          time=curr_time,
                          price=bar[BarColNames.close.value],
                          volume=volume)
            # Handle order.
            trading_executed_flag = self.account.handle_mkt_order(
                order, curr_prices)
            # Make records.
            self.log(curr_prices, order)
            # Only record executed orders.
            if trading_executed_flag == TradingExecuteFlag.good:
                self.account.record_executed_order(order)

        return self.account.record_nav

    def export_positions(self):
        """

        :return: pd.DataFrame
        """
        return self.account.export_positions()

    def export_executed_orders(self):
        """

        """
        return self.account.export_executed_orders()

# ----------------------------------------------------------------------
# Strategy Template.


class StrategyTemplate:
    """
    Strategy Template object.

    """

    def __init__(self, fast, slow, instrument='EUR_USD'):
        """

        """
        self.instrument = instrument
        self.history = []
        self.slow = slow
        self.fast = fast
        self.has_long = 0
        self.open_price = 0
        self.take_profit = 0

    def on_bar(self, bar):
        """
        Receive one bar, return signal, volume.
        :param bar: dict;
        :return: OrderType(Enum) object.
        """

        self.history.append(bar)
        curr_price = bar[BarColNames.close.value]
        # ---------------------------- #
        slow = np.mean([b[BarColNames.close.value]
                        for b in self.history[-1*self.slow:]])
        fast = np.mean([b[BarColNames.close.value]
                        for b in self.history[-1*self.fast:]])
        if fast > slow and (not self.has_long):
            self.has_long = 1
            self.open_price = curr_price
            return OrderType.buy, 10000
        if fast > slow and curr_price - self.open_price >= 0.01:  # take profit
            self.has_long = 1
            self.open_price = 0
            return OrderType.sell, 10000
        if curr_price - self.open_price <= -0.005:  # stop loss
            self.has_long = 1
            self.open_price = 0
            return OrderType.sell, 10000
        elif fast < slow:
            self.has_long = 0
            return OrderType.sell, 10000

        # ---------------------------- #
        return OrderType.none, 0
