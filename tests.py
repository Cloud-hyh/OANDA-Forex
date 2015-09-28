from oanda import *
import numpy as np
from statics import *
from kernel import Order, Position, Account
from datetime import datetime

__author__ = 'zed'


def test_config():
    c = OANDAPracticeConfig()
    print c.__class__ == OANDAPracticeConfig
    api = OANDAClient(config=OANDAPracticeConfig())
    print api.get_instruments().__class__
    print api.get_instruments()


def test_api():
    return OANDAClient(config=OANDAPracticeConfig())


def test_gets():
    api = OANDAClient(config=OANDAPracticeConfig())
    print api.get_account().json()


def test_enum():
    order_type1 = OrderType.buy
    print order_type1
    print order_type1.__class__
    print order_type1 == OrderType.buy
    print order_type1.__class__ == OrderType


def test_order():
    order1 = Order('EUR_USD', OrderType.buy, datetime(2014, 12, 11), 2.2, 200)
    order1.view()
    print order1.cash_flow()
    print order1.export_price_dict()
    print order1.export_time_price()
    print order1.export_to_position()
    order_sell = Order.close('EUR_USD', OrderType.sell,
                             datetime(2014, 12, 11), 2.2)
    order_sell.view()
    order_partial = Order.close_partial('EUR_USD', OrderType.sell,
                                        datetime(2014, 12, 11), 2.2, 50, 8008)
    order_partial.view()


def test_positions():
    order1 = Order('EUR_USD', OrderType.buy, datetime(2014, 12, 11), 2.2, 200)
    order2 = Order('EUR_USD', OrderType.short, datetime(2014, 12, 11), 2.2, 200)
    order3 = Order.close('EUR_USD', OrderType.sell, datetime(2014, 12, 15), 2.0)
    order4 = Order.close('EUR_USD', OrderType.fill, datetime(2014, 12, 13), 1.8)
    # order1.view()
    position1 = Position(order1)
    position1.view(2.4)
    print position1.open_value()
    print position1.unrealized_pnl(2.3)
    print position1.holding_value(2.3)

    position1.close(order3)
    position1.view()
    print position1.close_value()

    position2 = Position(order2)
    position2.view()
    position2.close(order4)
    position2.view(2.3)


def test_account():
    acc = Account.usd_std()
    odr = Order(instrument='EUR_USD',
                direction=OrderType.short,
                time=datetime(2015, 9, 1, 0, 0, 0),
                price=1,
                volume=100000)
    acc.handle_mkt_order(odr)
    acc.view({'EUR_USD': 5})

    odr2 = Order.close(instrument='EUR_USD',
                       direction=OrderType.fill,
                       time=datetime(2015, 9, 2, 0, 0, 0),
                       price=5)
    acc.handle_mkt_order(odr2)
    acc.view({'EUR_USD': 5})

    odr3 = Order(instrument='EUR_USD',
                 direction=OrderType.short,
                 time=datetime(2015, 9, 3, 0, 0, 0),
                 price=5,
                 volume=100000)
    acc.handle_mkt_order(odr3)

    acc.view({'EUR_USD': 3.5})


def test_sma():
    a = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print a[-8:]
    print np.mean([x for x in a[-8:]])

if __name__ == '__main__':
    test_sma()
    # test_order()
    # test_positions()
    # test_enum()
    # test_account()

    # api = test_api()
    # test_gets()
    # print api.retrieve_bars('EUR_USD', 'D').json()
