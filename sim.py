from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
import scipy.io
from kernel import *
from oanda import *
from plotting import *

class DMA(StrategyTemplate):
    """
    DMA

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


if __name__ == '__main__':

    api = OANDAClient(OANDAPracticeConfig())
    Z_size = 10
    Z = np.zeros(shape=(Z_size,Z_size))

    df = api.get_bars('EUR_USD', 'H1', 2000)
    slow = 10
    delta_fast = 6
    for i in range(0, Z_size):
        delta_fast = 6
        slow = slow + 1
        for j in range(0,Z_size):
            delta_fast += 2
            fast = slow + delta_fast
            s2 = DMA(slow,slow+delta_fast)
            k = Kernel.naive(df)
            pnl = k.run_naive(s2)[-1]
            Z[i][j] = pnl
            print "[SIM::Kernel] Finished Simulation: Slow_Index::{}; Delta_Index::{}; [Cumulated PNL: {}]".format(i,j,pnl)
        print '---------------------------------------------------'
        print '---------------------------------------------------'
        print '[SIM::Check Point||Do NoT Interrupt!!]: {}/{} rows Finished'.format(i+1, Z_size)
        print '---------------------------------------------------'
        print '---------------------------------------------------'
        scipy.io.savemat('Z_nav_cache{}.mat'.format(i+1), mdict={'Z': Z})