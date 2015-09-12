#encoding: UTF-8
import json
import time
from datetime import datetime, timedelta

from api import Config, PyApi
from api import HeartBeat, Tick, Bar
from api import MarketEvent, SignalEvent, EventQueue

from errors import (OANDA_RequestError, OANDA_EnvError, 
OANDA_DataConstructorError)

#----------------------------------------------------------------------
# Strategy classes

class BaseStrategy(object):
	"""
	Basic Strategy class.

	"""

	name = 'Abstract'
	api = None
	instrument = None

	def __init__(self, api):
		"""

		"""

		self.api = api

	def on_bar(self, event):
		"""

		"""
		pass

	def limit_buy(self, price, units):
		"""

		"""
		resp = self.api.place_order(
			instrument = self.instrument,
			side = 'buy',
			units = units,
			price = price,
			type = 'limit')
		print resp

	def limit_sell(self, price, units):
		"""

		"""
		resp = self.api.place_order(
			instrument = self.instrument,
			side = 'sell',
			units = units,
			price = price,
			type =' limit')
		print resp

	def market_buy(self, units):
		"""

		"""
		resp = self.api.place_order(
			instrument = self.instrument,
			side = 'buy',
			units = units,
			price = None,
			type = 'market')
		print resp

	def market_sell(self, units):
		"""

		"""
		resp = self.api.place_order(
			instrument = self.instrument,
			side = 'sell',
			units = units,
			price = None,
			type = 'market')
		print resp

#----------------------------------------------------------------------
# Toy Strategy.

class BuyAndHold(BaseStrategy):
	"""

	"""
	instrument = 'USD_CAD'
	BHFlag = True

	def __init__(self, api):
		"""

		"""

		self.api = api

	def on_bar(self, event):
		"""

		"""
		if self.BHFlag:
			self.market_buy(100)
			self.BHFlag = 0

		print self.api.get_positions()
		event.body.view()



def test_stream():
	"""
	
	"""

	q1 = EventQueue()
	q2 = EventQueue()
	q = {'mkt': q1, 'bar': q2}
	api = PyApi(Config(), q)

	mystrat = BuyAndHold(api)
	
	q1.bind('ETYPE_MKT', api.on_market_impulse)
	q2.bind('ETYPE_BAR', mystrat.on_bar)

	q1.open()
	q2.open()
	api.make_stream('EUR_USD')



if __name__ == '__main__':
    
    test_stream()