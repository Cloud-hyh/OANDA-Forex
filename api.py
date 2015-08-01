import json
import requests

import time
from datetime import datetime, timedelta

from Queue import Queue, Empty
from threading import Thread, Timer


class Config(object):
	"""
	Json-like config.
	"""

	head = "my token"

	token = '###' + \
			'###'

	body = {
		'account_id': '######',
		'domain': 'stream-fxpractice.oanda.com',
		'header': {
			'Connection' : 'keep-alive',
			'Authorization' : 'Bearer ' + token
		}
	}
	def __init__(self, head=0, token=0, body=0):
		""" Reload constructor. """
		if head:
			self.head = head
		if token: 
			self.token = token
		if body:
			self.body = body

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

	def __init__(self, data=dict(), is_empty=False):

		self.body = data

		# do something with heartbeat.
		if is_empty or not data:
			self.is_heartbeat = True
			pass


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

	prives
	------
	* _queue: Queue.Queue object; the main event queue.
	* _timer: threading.Timer object;
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

	def close(self):
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
# Datastream maker class

class StreamMaker(object):
	"""
	Generic data source maintainer.

	parameters
	----------
	* config: Config object; specifies user and connection configs.

	"""
	_config = Config()

	def __init__(self, config):
		""" Reload constructor. """

		if config.body:
			self._config = config

	def subscribe(self, instruments):
		"""
		subscribe market impulses

		parameters
		----------
		* instruments: List of strings; the list of instruments
		"""
		if type(instruments) != list:
			raise TypeError('[Strem]: Instruments must be a list.')
		if not instruments:
			raise ValueError('[Strem]: Empty instrument list.')
		instruments_str = ','.join(instruments)

		# initialize requests parameters from config.
		try:
			domain = self._config.body['domain']
			account_id = self._config.body['account_id']
			header = self._config.body['header']
			params = {
				'accountId': account_id,
				'instruments' : instruments_str
			}
		except KeyError, e:
			raise e('[Strem]: Config file is incomplete.')

		# GET request.
		s = requests.session()
		url = 'https://'+ domain +'/v1/prices'
		req = requests.Request('GET', 
								url = url, 
								headers = header, 
								params = params)
		prepped = s.prepare_request(req) # prepare the request.
		resp = s.send(prepped, stream=True, verify=False)

		# If success iterate over response.
		if resp.status_code == 200:
			for line in resp.iter_lines(1):
				try:
					#pass
					message = json.loads(line)
				except Exception, e:
					print '[Stream]: IterLine Error, ' + str(e)
					pass
				print line
		else:
			print '[Strem]: Unsuccessful Connection.'
			return -1
		





		