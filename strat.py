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

	def on_bar(self, event):
		print 'goood!'
		event.body.view()
		now = datetime.now()
		web = event.body.end
		print now, web


def test_stream():

	pass
	#q1.bind('ETYPE_MKT', smaker.on_market_impulse)
	#q2.bind('ETYPE_BAR', strat.on_bar)
	#q1.open()
	#q2.open()
	#smaker.make_stream('EUR_USD')


if __name__ == '__main__':
    

    test_stream()