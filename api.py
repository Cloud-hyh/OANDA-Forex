#encoding: UTF-8
import json
import requests
import pandas as pd

import time
from datetime import datetime, timedelta

from Queue import Queue, Empty, PriorityQueue
from threading import Thread, Timer
from errors import (OANDA_RequestError, OANDA_EnvError, 
OANDA_DataConstructorError)

class Config(object):
	"""
	Json-like config object.

	The Config() contains all kinds of settings and user info that 
	could be useful in the implementation of Api wrapper.

	privates
	--------
	* head: string; the name of config file.
	* token: string; user's token.
	* body: dictionary; the main content of config
			- username
			- password
			- account_id: integer; account ID used for requests.
			- domain: api domain.
			- domain_stream: stream domain.
			- ssl: boolean, specifes http or https usage.
			- version: ='v1'
			- header: dict; request header.
	* env: string; 'sandbox' or 'practice' or 'real',
	  specifies environment of the api.

	 Environments reference		Domain/Domain_stream
	* Real Money				api/stream-fxtrade.oanda.com
	* practices					api/stream-fxpractice.oanda.com
	* sandbox					api/stream-sandbox.oanda.com
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
			"Content-Type" : "application/x-www-form-urlencoded",
			'Connection' : 'keep-alive',
			'Authorization' : 'Bearer ' + token,
			'X-Accept-Datetime-Format' : 'unix'
		}
	}
	
	def __init__(self, head=0, token=0, body=0, env='sandbox'):
		""" 
		Reload constructor. 

		parameters
		----------
		* head: string; the name of config file.
		* token: string; user's token.
		* body: dictionary; the main content of config
		* env: string; 'sandbox' or 'practice' or 'real',
		  specifies environment of the api.
		"""
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
# Data containers.

class BaseDataContainer(object):
	"""
	Basic data container.

	privates
	--------
	* head: string; the head(type) of data container.
	* body: dictionary; data content. Among all sub-classes that inherit 
	BaseDataContainer, type(body) varies according to the financial meaning
	that the child data container stands for. 
		- Tick: 
		- Bar:
		- HistBar:

	"""
	head = 'ABSTRACT_DATA'
	body = dict()
	pass


class HeartBeat(BaseDataContainer):
	"""
	HeartBeat is almost an empty container, carries nothing but a timestamp.

	privates
	--------
	* head: string, inherited from BaseDataContainer, equals 'TIME'.
	* time: integer, a Unix timestamp.
	* dt: datetime.datetime() object.
	"""
	head = 'TIME'
	time = -1
	dt = -1

	def __init__(self, data):
		"""
		"""
		try:
			assert 'heartbeat' in data
			self.body = data['heartbeat']
			self.time = data['heartbeat']['time']
			self.dt = datetime.fromtimestamp(int(self.time)/1000000)
		except AssertionError:
			msg = '[HEARTBEAT]: Unable to construct empty heartbeat; ' + \
					'input is not heartbeat.'
			raise OANDA_DataConstructorError(msg)
		except Exception,e:
			msg = '[HEARTBEAT]: Unable to construct heartbeat; ' + str(e)
			raise OANDA_DataConstructorError(msg)


class Tick(BaseDataContainer):
	"""
	Tick data container. 
	Usually, tick containers are initialzed from a market impulse,
	i.e. the MarketEvent() object, which takes two forms, real 'tick' and
	empty heartbeat. The stream maker will automatically filter empty 
	heartbeat apart (and construct a HeartBeat(BaseDataContainer) for them)
	Therefore at the level of this class, there is no need for screening 
	the content of data when constructing.

	when tick is constructed, all privates except Tick.dt take values 
	from Json-like data, dt is converted from time, 
	using datetime.fromtimestamp()

	privates
	--------
	* head: string; inherited from BaseDataContainer, equals 'TICK'.
	* bid: float; bid price for this tick.
	* ask: float; ask price for this tick.
	* instrument: string; instrument ID.
	* time: integer; Unix timestamp.
	* dt: datetime.datetime() object.

	"""
	# place holders.
	head = 'TICK'
	bid = -1.0
	ask = -1.0
	instrument = ''
	time = -1
	dt = -1

	def __init__(self, data):
		"""
		Constructor

		parameters
		----------
		* data: dict; the market data.
		it ##should## be like: 
		{u'tick': {
			u'ask': 1.2408, 
			u'instrument': u'EUR_USD', 
			u'bid': 1.24065, 
			u'time': u'1438665311084691'
		}}
		"""
		try:
			assert 'tick' in data
			self.body = data['tick']
			self.bid = data['tick']['bid']
			self.ask = data['tick']['ask']
			self.instrument = data['tick']['instrument']
			self.time = data['tick']['time']
			self.dt = datetime.fromtimestamp(int(self.time)/1000000)
		except AssertionError:
			msg = '[TICK]: Unable to construct tick; ' + \
					'input is not a tick.'
			raise OANDA_DataConstructorError(msg)
		except Exception,e:
			msg = '[TICK]: Unable to construct tick; ' + str(e)
			raise OANDA_DataConstructorError(msg)

	def view(self):
		"""
		view data method.
		"""
		tick_view = {
			'datetime': str(self.dt),
			'time': self.time,
			'instrument': self.instrument,
			'bid': self.bid,
			'ask': self.ask
		}
		print json.dumps(tick_view, 
						 indent=4, 
						 sort_keys=True)


class Bar(BaseDataContainer):
	"""
	Bar data container.
	Bar inherently carries two ohlc bars, one is construct from bid price
	in the ticks, the other using ask price.
	It maintains these two bars for a predefined time span, and
	dynamcially stack received Tick data object to update the bars amid 
	that time span by calling self.push(tick).

	At tick level, all empty heartbeat impulses have already been filtered out.
	So there is no need to assert tick!=heartbeat when constructing bar.

	when Bar is constructed, the start time, time span(thus the end time) 
	are exogenously given. So the timestamp in the initial tick is not 
	referred to. 

	privates
	--------
	* head: string; inherited from BaseDataContainer, equals 'BAR'.
	* bid_open, bid_high, bid_low, bid_close: floats; an ohlc bar 
	  for the bid side. 
	* ask_open, ask_high, ask_low, ask_close: floats; an ohlc bar 
	  for the ask side. 
	* instrument: string; instrument ID.
	* start, end: datetime.datetime() object; defines the start and end
	  for the maintainance. These are calculated when constucted, and remain
	  constant during the lifespan of self.
	* span: datetime.timedelta() object; marks the time range of bar,
	  exogenously given in the constructor, default is 1 minute. It's also a
	  constant during the Bar instances' lifespan.
	"""
	head = 'BAR'
	span = timedelta(minutes=1)
	start = -1
	end = -1

	bid_open = -1
	bid_high = -1
	bid_low = -1
	bid_close = -1

	ask_open = -1
	ask_high = -1
	ask_low = -1
	ask_close = -1

	instrument = ''

	def __init__(self, tick, start, span=timedelta(minutes=1)):
		"""
		constructor.

		parameters
		----------
		* tick: Tick(BaseDataContainer) object; the first tick used to
		  initialze the bar object.
		* start: datetime.datetime() object; the starting mark.
		* span: datetime.timedelta() object; specifies time span of this bar,
		  default value is 1 minute.
		"""
		self.span = span
		self.start = start
		self.end = start + span
		try:
			# !only uses bid ask in tick, start was transferred separately.
			assert type(tick) == Tick
			bid, ask = tick.bid, tick.ask
			self.bid_open, self.bid_high, self.bid_low, self.bid_close = \
				bid, bid, bid, bid
			self.ask_open, self.ask_high, self.ask_low, self.ask_close = \
				ask, ask, ask, ask
		except AssertionError:
			msg = '[BAR]: Unable to construct bar; ' + \
					'bar must be initialized with a tick.'
			raise OANDA_DataConstructorError(msg)
		except Exception,e:
			msg = '[BAR]: Unable to construct bar; ' + str(e)
			raise OANDA_DataConstructorError(msg)

	def view(self):
		"""
		view data method.
		"""
		bar_view = {
			'start': str(self.start),
			'end': str(self.end),
			'bid_ohlc': [self.bid_open, self.bid_high, 
						self.bid_low, self.bid_close],
			'ask_ohlc': [self.ask_open, self.ask_high, 
						self.ask_low, self.ask_close]
		}
		print json.dumps(bar_view, 
						 indent=4, 
						 sort_keys=True)

	def push(self, tick):
		"""
		push new tick into bar, update bar data.

		parameters
		----------
		* tick: Tick(BaseDataContainer) object; the tick to be updated.

		returnCode
		----------
		* 1: tick was updated.
		* 0: tick was not updated, since tick.time not in bar time range.
		"""
		tick_time = tick.dt
		if tick_time < self.end and tick_time >= self.start:
			bid, ask = tick.bid, tick.ask

			self.bid_high, self.bid_low, self.bid_close = \
			max(self.bid_high, bid), min(self.bid_low, bid), bid

			self.ask_high, self.ask_low, self.ask_close = \
			max(self.ask_high, ask), min(self.ask_low, ask), ask
			return 1
		else:
			return 0


class HistBar(BaseDataContainer):
	"""

	"""	
	head = 'HISTBAR'
	body = pd.DataFrame()
	pass

		
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


class BarEvent(BaseEvent):
	"""
	Bar data event, body is a Bar() object.

	parameters
	----------
	* data: Bar() object.
	"""

	head = 'ETYPE_BAR'
	instrument = ''

	def __init__(self, data):

		try: # examine the type of input data.
			assert type(data) == Bar
			self.body = data
			self.instrument = data.instrument
		except AssertionError:
			msg = '[BAREVENT]: Unable to construct bar event; ' + \
					'input data must be a Bar object.'
			raise OANDA_DataConstructorError(msg)


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

	def bind(self, event_head, func):
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
	Python based OANDA Api object.
	The main bridge that connects local scripts & logics with OANDA server. 
	It acts as a comprehensive data generator, cleaner and distributer; 
	and also includes trading methods.
	Wraps 
		- OANDA Get data requests, returns the response.
		- Make stream requests, iterate data lines in stream resp.
		- Trading requests.
		- Clean data functionalities.
		- EventQueue that distribtes data, received and cleaned, to listening
		  handlers/strategies.

	PyApi is initialzed with a dict of {event type |-> event queue} mapping
	and a Config json. Note that the config file must be complete. In that 
	once constructed, the private variables like request headers, tokens, etc 
	become constant values (inherited from Config). These privates will be 
	consistantly called whenever talk to OANDA server. 

	The names(keys) of EventQueue in construction parameter queues should be 
	lower case string '###', taken from 'ETYPE_###'. Because these keys are
	directly referred to in this manner in the scripts.

	privates
	--------
	* _config: Config() object; a container of all useful settings when making 
	  requests.
	* _event_queues: dictionary; a mapping from event type abbreivation to 
	  coresponing event queue that stores these events.
	  	- example: 	_event_queues = {
						'mkt': None, # ETYPE_MKT
						'bar': None  # ETYPE_BAR
					}
	* _ssl, _domain, _domain_stream, _version, _header, _account_id: 
	  boolean, string, string, string, dictionary, integer;
	  just private references to the items in Config. See the docs of Config().
	* _session: requests.session() object.
	* _curr_bar: Bar() object; the current bar data maintained when requests
	  stream data. It is dynamically updated and reset on new market impulses.

	examples
	--------
	>> q1 = EventQueue()
	>> q2 = EventQueue()
	>> q = {'mkt': q1, 'bar': q2}
	>> mystrat = BaseStrategy()
	>> myapi = PyApi(Config(), q)
	>> q1.bind('ETYPE_MKT', myapi.on_market_impulse)
	>> q2.bind('ETYPE_BAR', mystrat.on_bar)
	>> ... # more binding to handlers.
	>> q1.open()
	>> q2.open()
	>> myapi.make_stream('EUR_USD')
	>> ...

	"""
	_config = Config()
	_event_queues = {
		'mkt': None, # ETYPE_MKT
		'bar': None  # ETYPE_BAR
	}

	# request stuffs
	_ssl = False
	_domain = ''
	_domain_stream = ''
	_version = 'v1'
	_header = dict()
	_account_id = None

	_session = requests.session()

	# pointer to the bar that was currently maintained.
	_curr_bar = None

	def __init__(self, config, queues):
		"""
		Constructor. 

		parameters
		----------
		* config: Config object; specifies user and connection configs.
		* queues: A dictionary of Event Queue objects; shaped like
		{
			'mkt': q1, # ETYPE_MKT
			'bar': q2  # ETYPE_BAR
		}
		as containers of the events loaded from the stream. 

		"""
		self._event_queues = queues
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
			if method == 'GET':
				req = requests.Request(method,
								   	   url = url,
								   	   headers = self._header,
								   	   params = params)
			elif method == 'POST':
				req = requests.Request(method,
								   	   url = url,
								   	   headers = self._header,
								   	   data = params)
				# for POST, params should be included in request body.
			prepped = s.prepare_request(req) # prepare the request
			resp = s.send(prepped, stream=False, verify=True)
			if method == 'GET':
				assert resp.status_code == 200
			elif method == 'POST': 
			# note that respcode for POST is still 200!
				assert resp.status_code == 200
			return resp
		except AssertionError:
			msg = '[API]: Bad request, unexpected response status: ' + \
				  str(resp.status_code)
			raise OANDA_RequestError(msg)
			pass
		except Exception,e:
			msg = '[API]: Bad request.' + str(e)
			raise OANDA_RequestError(msg)

	def _put_market_event(self, data):
		"""	
		put the market impulse into the event queue.

		parameters:
		----------
		* data: dictionary; resp.json() object.
		"""
		# create event.
		try:
			if 'heartbeat' in data:
				event = MarketEvent(data, is_heartbeat=True)
			elif 'tick' in data:
				event = MarketEvent(data, is_heartbeat=False)

			self._event_queues['mkt'].put(event)
			return 1
		except Exception,e:
			msg = '[API]: Failed to put market event; ' + str(e)
			return -1

	def _put_bar_event(self, bar=-1):
		"""
		put currently maintained bar into event queue.

		parameters:
		----------
		* bar: Bar() object; the data that is to be put into BarEvent()
		event object. -1 as Default: point to the currently maintained bar,
		i.e. self._curr_bar.
		"""
		try:
			if bar == -1:
				if self._curr_bar:
					event = BarEvent(data = self._curr_bar)
			else:
				event = BarEvent(data = bar)

			self._event_queues['bar'].put(event)
			return 1
		except Exception,e:
			msg = '[API]: Failed to put bar event; ' + str(e)
			return -1


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
					#!! put market impulse into the event queue.
					self._put_market_event(data)
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

	def place_order(self, instrument, side, units, price, type):
		"""
		place an order through OANDA API.

		parameters
		----------
		* instrument: string; the name of instrument.
		* side: string; 'buy'/'sell'
		* units: integer; the amount to be traded.
		* type: string; 
			- 'market': market order, trade by current market price.
			- 'limit': limit order, trade when crossing specified price.
		* price: float; price to excute limit order.
		"""
		url = '{}/{}/accounts/{}/orders'.format(self._domain, 
			   self._version, self._account_id)
		params = {
			'instrument': instrument,
			'side': side,
			'units': units,
			'price': price,
			'type': type,
			'expiry' : None
		}
		try:
			resp = self._access(url=url, params=params, method='POST')
			assert len(resp.json()) > 0
			return resp.json()
		except AssertionError: return 0

	#----------------------------------------------------------------------
	# on market event

	def on_market_impulse(self, event):
		"""
		call back function on market impulses.
		filter/clean tick data 

		parameters
		----------
		* event: MarketEvent() object.

		returnCode
		----------
		* 0: a tick was appended to current bar.
		* 1: pop current bar, start a new bar.
		"""
		if event.is_heartbeat == False: # Not an empty heartbeat.
			tick = Tick(event.body)
			if not self._curr_bar: # create a new bar.
				bar = Bar(tick, tick.dt)
				self._curr_bar = bar
			else: 
				bar = self._curr_bar

			if tick.dt < bar.end and tick.dt >= bar.start:
				bar.push(tick)
				return 0
			else:
				self._put_bar_event() 
				#!!! this line should be excuted before 
				#!!! the reset of self._curr_bar pointer.
				new_start = bar.end
				self._curr_bar = Bar(tick, new_start) # create a new bar.
				return 1

		else: # empty heartbeat.
			hb = HeartBeat(event.body)
			if not self._curr_bar:
				pass
			else:
				bar = self._curr_bar

			if hb.dt < bar.end and hb.dt >= bar.start:
				pass # this is only an empty heartbeat.
				return -1
			else:
				if bar:
					self._put_bar_event() 
					#!!! this line should be excuted before 
					#!!! the reset of self._curr_bar pointer.
					new_start = bar.end
					tick = Tick({'tick':
						{
							'ask': bar.ask_close,
							'bid': bar.bid_close,
							'instrument': bar.instrument,
							'time': 0 # only a place holder.
						}})
					self._curr_bar = Bar(tick, new_start)
					return 1
