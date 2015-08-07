#encoding: UTF-8
import json
import requests
import pymongo
import pandas as pd
from threading import Thread

import time
from datetime import datetime, timedelta

from api import Config, PyApi
from api import HeartBeat, Tick, Bar, HistBar
from api import MarketEvent, EventQueue

from errors import (OANDA_RequestError, OANDA_EnvError, 
OANDA_DataConstructorError)
from requests.exceptions import ConnectionError

# global variables.
client = pymongo.MongoClient()
dbs = {
	'M1': client['OANDA_M1'],
	'M3': client['OANDA_M3']
}

#----------------------------------------------------------------------
# Background functions
"""
The following functions begin with _ are not revealed to users.
mongod() function is a wrapper of all these stuffs that initializes
databases. 

function call
-------------
mongod() -> _set_db_index() & _get_all()
	_get_all() -> _get_coll_names & _get_one_instrument
	_set_db_index -> _get_coll_names

functionalities
---------------
* _get_coll_names(): returns a list of all instruments.
* _set_db_index(): call get coll names and initializes collections
  with these names, then set index for each collection as datetime.
* _get_one_instrument(): returns historical data of one instrument,
  also cleans data.
* _get_all(): call _get_one_instrument over all instruments in the list.


"""

def _get_coll_names(oApi):
	"""
	return all names of instruments.

	parameters
	----------
	* oApi: api.PyApi object; request client.
	"""
	try:
		resp = oApi.get_instruments()
		assert 'instruments' in resp
		instrument_list = [d['instrument'] for d in resp['instruments']]
		return instrument_list
	except AssertionError: 
		msg = '[API]: Bad request, unexpected response contest.'
		raise OANDA_RequestError(msg)

def _set_db_index(oApi):
	"""
	set mongodb indices to datetime.
	"""
	instrument_list = _get_coll_names(oApi)
	for name in dbs:
		db = dbs[name]
		for instrument in instrument_list:
			coll = db[instrument]
			coll.ensure_index([('datetime',
								pymongo.DESCENDING)], unique=True)
	print '[MONGOD]: MongoDB index set.'
	return 1


def _get_one_instrument(oApi, granularity='M1', instrument='EUR_USD'):
	"""
	Get historical data for one instrument.

	parameters
	----------
	* oApi: api.PyApi object; request client.
	* granularity: string
	* instrument: string
	"""
	todt = lambda time: datetime.fromtimestamp(
						int(time)/1000000)
	update_dt = lambda d: d.update({'datetime': todt(d['time'])})

	try:
		resp = oApi.get_history(instrument = instrument,
								granularity = granularity,
								count = 5000)
		data = resp['candles']
		map(update_dt, data)

		# insert to mongodb
		db = dbs[granularity]
		coll = db[instrument]
		coll.insert_many(data)
		return coll
	except ConnectionError,e:
		# If choke connection, standby for 1sec an invoke again.
		time.sleep(1)
		_get_one_instrument(oApi, granularity, instrument)


def _get_all(oApi, granularity='M1'):
	"""
	"""
	instruments = _get_coll_names(oApi)
	k = 1
	for instrument in instruments:
		try:
			# time.sleep(1)
			_get_one_instrument(oApi, granularity, instrument)
		except Exception, e:
			print str(e)
			pass
		print k
		k += 1

#----------------------------------------------------------------------
# Front function

def mongod():
	"""
	Initialize MongoDB.
	"""
	client = pymongo.MongoClient()

	q1 = EventQueue()
	q2 = EventQueue()
	q = {'mkt':q1, 'bar':q2}
	oApi = PyApi(Config(),q)

	_set_db_index(oApi)
	_get_all(oApi)


if __name__ == '__main__':
	mongod()