#encoding: UTF-8
import json
import requests
import pymongo

import time
from datetime import datetime, timedelta

from Queue import Queue, Empty, PriorityQueue
from threading import Thread, Timer
from errors import OANDA_RequestError, OANDA_EnvError

class Config(object):
	"""
	Json-like config.

	Environments reference		Domain
    * Real Money              	stream-fxtrade.oanda.com
    * Practice      			stream-fxpractice.oanda.com
    * sandbox               	stream-sandbox.oanda.com

	"""

	head = "my token"

	token = '4c56cbf8105642050bbfdb36aad29c6a-' + \
			'77dfc84d1fc6a2ced8e1b15641d0d69e'

	body = {
		'username': 'geonaroben',
		'password': 'DequejHid&',
		'account_id': 2804581,
		'domain': 'api-sandbox.oanda.com', # sandbox environment
		'domain_stream': 'stream-sandbox.oanda.com',
		'ssl': False, # http or https.
		'version': 'v1',
		'header': {
			'Connection' : 'keep-alive',
			'Authorization' : 'Bearer ' + token,
			'X-Accept-Datetime-Format' : 'unix'
		}
	}
	
	def __init__(self, head=0, token=0, body=0, env='sandbox'):
		""" Reload constructor. """
		if head:
			self.head = head
		if token: 
			self.token = token
		if body:
			self.body = body

		# environment settings.
		if env == 'sandbox':
			self.body['ssl'] = False
		elif env == 'practice':
			self.body['ssl'] = True

	def view(self):
		""" Prettify printing method. """
		config_view = {
			'config_head' : self.head,
			'config_body' : self.body,
			'user_token' : self.token
		}
		print json.dumps(config_view, 
						 indent=4, 
						 sort_keys=True)

#----------------------------------------------------------------------
# Event containers.

class BaseEvent(object):
	"""
	Base level event object.

	"""
	head = 'ETYPE_NONE'
	body = dict()

	def view(self):
		""" print method. """
		print '[{}]: {}'.format(self.head, self.body)


class MarketEvent(BaseEvent):
	"""
	Market impulse event.

	parameters
	----------
	* is_empty: boolean, False as default; 
	specify whether this is mere a heartbeat event.
	* data: dict; the market data.

	"""

	head = 'ETYPE_MKT'
	is_heartbeat = False

	def __init__(self, data=dict(), is_heartbeat=False):

		self.body = data
		self.is_heartbeat = is_heartbeat


class SignalEvent(BaseEvent):
	"""

	"""

	head = 'ETYPE_SGNL'
	pass
	

class OrderEvent(BaseEvent):
	"""

	"""

	head = 'ETYPE_ODR'
	pass
	

class FillEvent(BaseEvent):
	"""

	"""

	head = 'ETYPE_FLL'
	pass
	

class EventQueue(object):
	"""
	Generic EventQueue implementation, maintains main event
	queue of the system; register functions to speecific events;
	push events and distribute em to listeners.

	privates
	--------
	* _queue: Queue.Queue object; the main event queue.
	* _active_flag: boolean; whether active or not.
	* _thrd: threading.Thread object; event engine thread.
	* _listeners: dictionary;
				mapping from event type to handlers' list,
				shaped like: {'ETYPE_ODR': [<func1>, <func2],
					   		  'ETYPE_SGNL': [<func_handle_sign>]}

	constructing parameters
	-----------------------
	None

	"""

	# event queue and timer instances.
	_queue = Queue()

	# empty place holders.
	_active_flag = False
	_thrd = None
	_listeners = dict()

	def __init__(self):
		""" Constructor """

		self._thrd = Thread(target=self.distribute, name='_THRD_EVENT')

	def put(self, event):
		""" 
		put an event into queue 

		parameters
		----------
		* event: a BaseEvent or its subclass instance.
		"""
		self._queue.put(event)

	def open(self):
		""" open the queue. """
		self._active_flag = True
		self._thrd.start()

	def kill(self):
		""" suspend engine. """
		if self._active_flag:
			self._active_flag = False
			self._thrd.join()

	def register(self, event_head, func):
		""" 
		Register a speecific function as a listener to some
		type of events, events of this type will be distributed
		to function when get() from queue.

		parameters
		----------
		* event_head: string; an 'ETYPE_###' declaration.
		* func: function; noticing that **kwargs has only event. 
		i.e. f(event).

		"""
		if event_head not in self._listeners:
			self._listeners[event_head] = []

		if func not in self._listeners[event_head]:
			self._listeners[event_head].append(func)

		return self._listeners

	def distribute(self):
		""" distribute events by listeners mapping. """
		while self._active_flag:
			try:
				event = self._queue.get()
				if event.head in self._listeners:
					[f(event) for f in self._listeners[event.head]]
			except Empty:
				pass

#----------------------------------------------------------------------
# OANDA Api class

class PyApi(object):
	"""
	Data source maintainer, requests maker;
	a lower lever wrapper on the top of event queue.

	privates & parameters
	--------   ----------
	* config: Config object; specifies user and connection configs.
	* queue: Event Queue object; container of the events loaded from
	the stream. 

	"""
	_config = Config()
	_event_queue = None

	# request stuffs
	_ssl = False
	_domain = ''
	_domain_stream = ''
	_version = 'v1'
	_header = dict()
	_account_id = None

	_session = requests.session()

	def __init__(self, config, queue):
		""" Reload constructor. """
		self._event_queue = queue
		if config.body:
			self._config = config
			self._ssl = config.body['ssl']
			self._domain = config.body['domain']
			self._domain_stream = config.body['domain_stream']
			self._version = config.body['version']
			self._header = config.body['header']
			self._account_id = config.body['account_id']

		# configure protocol
		if self._ssl:
			self._domain = 'https://' + self._domain
			self._domain_stream = 'https://' + self._domain_stream
		else:
			self._domain = 'http://' + self._domain
			self._domain_stream = 'http://' + self._domain_stream

	def _access(self, url, params, method='GET'):
		"""
		request specific data at given url with parameters.

		parameters
		----------
		* url: string.
		* params: dictionary.
		* method: string; 'GET' or 'POST', request method.

		"""
		try:
			assert type(url) == str
			assert type(params) == dict
		except AssertionError,e:
			raise e('[API]: Unvalid url or parameter input.')
		if not self._session:
			s = requests.session()
		else: s = self._session

		# prepare and send the request.
		try:
			req = requests.Request(method,
								   url = url,
								   headers = self._header,
								   params = params)
			prepped = s.prepare_request(req) # prepare the request
			resp = s.send(prepped, stream=False, verify=True)
			if method == 'GET':
				assert resp.status_code == 200
			elif method == 'POST':
				assert resp.status_code == 201
			return resp
		except AssertionError:
			msg = '[API]: Bad request, unexpected response status: ' + \
				  str(resp.status_code)
			raise OANDA_RequestError(msg)
		except Exception,e:
			msg = '[API]: Bad request.' + str(e)
			raise OANDA_RequestError(msg)

	#----------------------------------------------------------------------
	# make market data stream.

	def make_stream(self, instruments):
		"""
		subscribe market impulses and make stream.

		parameters
		----------
		* instruments: string; the ticker(s) of instrument(s), connected by 
		  coma. Example: 'EUR_USD, USD_CAD'
		"""
		try:
			assert type(instruments) == str
		except AssertionError,e:
			raise e('[API]: Unvalid instruments input.')
		
		s = requests.session()
		url = '{}/{}/prices'.format(self._domain_stream, self._version)
		params = {
			'accountId': self._account_id,
			'instruments': instruments
		}

		# prepare and send the request.
		try:
			req = requests.Request('GET',
								   url = url,
								   headers = self._header,
								   params = params)
			prepped = s.prepare_request(req) # prepare the request
			resp = s.send(prepped, stream=True, verify=True)
			assert resp.status_code == 200
			print '[API]: Stream established.'
		except AssertionError:
			msg = '[API]: Bad request, unexpected response status: ' + \
				  str(resp.status_code)
			raise OANDA_RequestError(msg)
		except Exception,e:
			msg = '[API]: Bad request.' + str(e)
			raise OANDA_RequestError(msg)

		# Iter-lines in resp.
		for line in resp.iter_lines(90):
			if line:
				try:
					data = json.loads(line)
					print data
				except Exception,e:
					print '[API]: Stream iterLine Error, ' + str(e)
					pass

	#----------------------------------------------------------------------
	# get methods.

	#----------------------------------------------------------------------
	# Market side

	def get_instruments(self):
		"""
		get list of instruments.
		"""
		
		url = '{}/{}/instruments'.format(self._domain, self._version)
		params = {
			'accountId': self._account_id
		}
		try:
			resp = self._access(url=url, params=params)
			assert len(resp.json()) > 0
			return resp.json()
		except AssertionError: return 0

	def get_history(self, instrument, granularity, candle_format='bidask',
				    count=500, daily_alignment=None, 
				    alignment_timezone=None, weekly_alignment="Monday",
				    start = None, end = None):
		"""
		retrieve historical bar data of certain instrument.

		parameters
		----------
		* instrument: string; the ticker of instrument.

		* granularity: string; sample rate of bar data. Examples:
			- 'S10' 10-seconds bar.
			- 'M1' 1-minute bar.
			- 'H3' 3-hours bar.
			- 'D'/'W'/'M' day/week/month(one).

		* candle_format: string; candlestick representation, either:
			- 'bidask' (default), the Bid/Ask based candlestick.
			- 'midpoint', the midpoint based candlestick.

		* count: integer; the number of bars to be retrieved, maximum is
		  5000, should not be specified if both start and end are specified.

		* daily_alignment: integer; the hour of day used to align candles 
		  with hourly, daily, weekly, or monthly granularity. Note that
		  The value specified here is interpretted as an hour in the timezone 
		  set through the alignment_timezone parameter.

		* alignment_timezone: string; timezone used for the dailyAlignment.

		* weekly_alignment: string; the day of the week used to align candles 
		  with weekly granularity.

		* start, end: string; timestamp for the range of candles requested.

		"""
		url = '{}/{}/candles'.format(self._domain, self._version)
		params = {
			'accountId': self._account_id,
			'instrument': instrument,
			'granularity': granularity,
			'candleFormat': candle_format,
			'count': count,
			'dailyAlignment': daily_alignment,
			'alignmentTimezone': alignment_timezone,
			'weeklyAlignment': weekly_alignment,
			'start': start,
			'end': end
		}
		try:
			resp = self._access(url=url, params=params)
			assert len(resp.json()) > 0
			return resp.json()
		except AssertionError: return 0

	def get_prices(self, instruments):
		"""
		get a prices glance (not using stream api)

		parameters
		----------
		* instruments: string.

		"""
		url = '{}/{}/prices'.format(self._domain, self._version)
		params = {
			'accountId': self._account_id,
			'instruments': instruments
		}
		try:
			resp = self._access(url=url, params=params)
			assert len(resp.json()) > 0
			return resp.json()
		except AssertionError: return 0

	#----------------------------------------------------------------------
	# Trader side

	def create_sandbox_acc(self):
		"""
		Create a sandbox test account.

		"""
		if self._ssl == False:
			url = '{}/{}/accounts'.format(self._domain, self._version)
			try:
				resp = self._access(url=url, params=dict(), method='POST')
				assert len(resp.json()) > 0
				return resp.json()
			except AssertionError: return 0
		else:
			msg = '[API]: create_sandbox_acc() method cannot be invoked ' + \
				  'within other than sandbox environment.'
			raise OANDA_EnvError(msg)

	def get_account_info(self, account_id=-1):
		"""
		Get infomation of specific account.

		parameters
		----------
		* account_id: string or integer; default is -1
		(use account_id in config)
		"""
		if account_id == -1:
			account_id = self._config.body['account_id']

		url = '{}/{}/accounts/{}'.format(self._domain, 
				self._version, account_id)
		try:
			resp = self._access(url=url, params=dict(), method='GET')
			assert len(resp.json()) > 0
			return resp.json()
		except AssertionError: return 0

	def get_positions(self):
		"""
		Get a list of all positions.
		"""
		url = '{}/{}/accounts/{}/positions'.format(self._domain, 
			   self._version, self._account_id)
		params = {
			'accountId': self._account_id,
		}
		try:
			resp = self._access(url=url, params=params)
			assert len(resp.json()) > 0
			return resp.json()
		except AssertionError: return 0

	def get_orders(self, instrument=None, count=50):
		"""
		Get all PENDING orders for an account. 
		Note that pending take-profit or stop-loss orders are recorded
		in the open trade object.

		parameters
		----------
		* instruments: string; default is all.
		* count: integer; maximum number of open orders to return.

		"""
		url = '{}/{}/accounts/{}/orders'.format(self._domain, 
			   self._version, self._account_id)
		params = {
			'instrument': instrument,
			'count': count
		}
		try:
			resp = self._access(url=url, params=params)
			assert len(resp.json()) > 0
			return resp.json()
		except AssertionError: return 0

	def get_trades(self, instrument=None, count=50):
		"""
		Get list of open trades.

		parameters
		----------
		* instruments: string; default is all.
		* count: integer; maximum number of open orders to return.

		"""
		url = '{}/{}/accounts/{}/trades'.format(self._domain, 
			   self._version, self._account_id)
		params = {
			'instrument': instrument,
			'count': count
		}
		try:
			resp = self._access(url=url, params=params)
			assert len(resp.json()) > 0
			return resp.json()
		except AssertionError: return 0

def test_stream():

	q = EventQueue()

	smaker = PyApi(Config(),q)
	#smaker.make_stream('EUR_USD')
	doc2 = smaker.get_account_info()
	print doc2
	doc3 = smaker.get_positions()
	print doc3
	doc4 = smaker.get_orders()
	print doc4
	doc5 = smaker.get_trades()
	print doc5

if __name__ == '__main__':
    

    test_stream()