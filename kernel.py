import numpy as np
import pandas as pd
import time, json, os
from datetime import datetime, timedelta

from api import Config, PyApi, EventQueue
from errors import (KERNEL_BacktestError, KERNEL_OrderError, 
	KERNEL_TradingError)
from timeseries import ResearchConfig, get_data
from utils import dt_to_str, serialize_dict
# Import type definitions.
from utils import (ORDER_TYPE_BUY, ORDER_TYPE_SHORT, ORDER_TYPE_FILL,
	ORDER_TYPE_SELL, ORDER_TYPE_NONE)
from utils import (POSITION_TYPE_LONG, POSITION_TYPE_SHORT,
	POSITION_TYPE_NONE, POSITION_STATUS_OPEN, POSITION_STATUS_CLOSED)
from utils import ORD_POS_MAPPING, POS_INT_MAPPING, ORD_INT_MAPPING


#----------------------------------------------------------------------
# Order object.

class Order:
	"""
	Json-like trading order profile object.

	example
	-------
	body = {
		'instrument': 'EUR_USD',
		'direction': 'ORD_SHORT',
		'time': datetime(2015,10,08,12,0,0),
		'price': 2.588,
		'volume': 100,
	}
	"""
	id = None
	head = 'Order'
	body = dict()
	direction = ''
	instrument = ''
	# The order matters!
	__keys = ['instrument','direction','volume','time','price']

	def __init__(self, instrument, direction, time, price, volume):
		"""
		Constructor, place an order object; open a posision.

		parameters
		----------
		* instrument: string
		* direction: Defined ORDER_TYPE, string
			- ORDER_TYPE_BUY = 'ORD_BUY'
			- ORDER_TYPE_SHORT = 'ORD_SHORT'
			- ORDER_TYPE_FILL = 'ORD_FILL'
			- ORDER_TYPE_SELL = 'ORD_SELL'
			- ORDER_TYPE_NONE = 'ORD_NONE'
		* time: datetime.datetime object; placement time.
		* price: double.
		* volume: double/int

		"""
		# The order matters!
		vals = [instrument, direction, volume, time, price]
		self.body = dict(zip(self.__keys, vals))
		self.instrument = vals[0]
		self.direction = vals[1]

	def cashflow(self):
		""" Cash flow NET of spreadCost. """
		return self.body['volume'] * self.body['price']

	def export_to_position(self):
		""" Export data in order <to CONSTRUCT Position>. """
		return [self.body['instrument'],
				ORD_POS_MAPPING[self.direction],
				self.body['volume'], self.body['time'], self.body['price']]

	def export_time_price(self):
		""" Export [time,price] in order <to CLOSE Position>. """
		return [self.body['time'], self.body['price']]

	def view(self):
		""" Prettified printing method. """
		print json.dumps(serialize_dict(self.body), 
						 indent=4, 
						 sort_keys=True)

#----------------------------------------------------------------------
# Position object.

class Position:
	"""
	Json-like position log object.

	example
	-------
	body = {
		'instrument': 'EUR_USD',
		'direction': 'POS_LONG',
		'volume': 10000,
		'openTime': datetime(2015,9,12,0,0,0),
		'openPrice': 1.8502,
		'closeTime': datetime(2015,9,15,0,0,0),
		'closePrice': 1.8507,
		'PnL': 5,
		'spreadCostOpen': 0.4,
		'spreadCostClose': 0.2
	}

	"""
	head = 'Position'
	status = POSITION_STATUS_OPEN
	id = None
	body = dict()
	# The order matters!
	__keys = ['instrument', 'direction', 'volume', 
			'openTime', 'openPrice', 'closeTime', 'closePrice', 
			'PnL', 'spreadCostOpen', 'spreadCostClose']
	__keys_open = ['instrument', 'direction', 'volume', 
				'openTime', 'openPrice']
	__keys_close = ['closeTime', 'closePrice']

	def __init__(self, order, spread_rate):
		"""
		Constructor, open the position.

		parameters
		----------
		* order: Order object; indicating order profile.
		* spread_rate: double.

		"""
		# Invoke different constructor according to orders.
		try:
			assert order.direction in [ORDER_TYPE_SHORT, ORDER_TYPE_BUY]
			vals = order.export_to_position()
			self.body = dict(zip(self.__keys_open, vals))
			self.body['spreadCostOpen'] = order.body['price'] * \
							order.body['volume'] * spread_rate
		except AssertionError:
			msg = '[KERNEL_TradingError]: Invalid order type to ' + \
			'open a position.'
			raise KERNEL_TradingError(msg)

	def view(self):
		""" Prettified printing method. """
		print json.dumps(serialize_dict(self.body), 
						 indent=4, 
						 sort_keys=True)

	def calc_opening_value(self):
		""" Calculate position's opening value, net of spread. """
		return self.body['openPrice'] * self.body['volume']

	def calc_holding_value(self, price):
		""" Calculate holding value. """
		return price * self.body['volume']

	def calc_closing_value(self):
		""" Calculate holding value. """
		return self.body['closePrice'] * self.body['volume']

	def calc_opening_cost_rev(self):
		""" Calculate position's opening cost/revenue, include spread. """
		try:
			assert self.status == POSITION_STATUS_OPEN
			if self.body['direction'] == POSITION_TYPE_LONG:
				# Opening cost = value + spreadCost
				return self.calc_opening_value() + self.body['spreadCostOpen']
			elif self.body['direction'] == POSITION_TYPE_SHORT:
				# Opening rev = value - spreadCost
				return self.calc_opening_value() - self.body['spreadCostOpen']
			# Note: all returns here are the absolute value.
		except AssertionError:
			raise KERNEL_TradingError

	def __calc_pnl(self):
		""" Calculate realized profit/loss. """
		# Must be invoked when posiiton is finished.
		if self.body['direction'] == POSITION_TYPE_LONG:
			return self.body['volume'] * \
				(self.body['closePrice'] - self.body['openPrice']) - \
				(self.body['spreadCostClose'] + self.body['spreadCostOpen'])
		elif self.body['direction'] == POSITION_TYPE_SHORT:
			return self.body['volume'] * \
				(self.body['openPrice'] - self.body['closePrice']) - \
				(self.body['spreadCostClose'] + self.body['spreadCostOpen'])
		

	def close(self, order, spread_rate):
		"""
		Close the position.

		parameters
		----------
		* order: Order object; indicating order profile.
		* spread_rate: double.
		"""
		if self.status == POSITION_STATUS_CLOSED:
			return
		try:
			assert order.direction in [ORDER_TYPE_SELL, ORDER_TYPE_FILL]

			volume = self.body['volume']
			vals = order.export_time_price() # [time, price]
			self.body.update(dict(zip(self.__keys_close, vals)))
			self.body['spreadCostClose'] = vals[1] * volume * spread_rate

			# Realize PnL:
			self.body['PnL'] = self.__calc_pnl()

			# Close position.
			self.status = POSITION_STATUS_CLOSED
		except AssertionError:
			msg = '[KERNEL_TradingError]: Invalid order type to ' + \
			'close a position.'
			raise KERNEL_TradingError(msg)
