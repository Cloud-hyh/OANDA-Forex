import pandas as pd
import time
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates

from api import Config, PyApi, EventQueue
from datetime import datetime, timedelta


#----------------------------------------------------------------------
# Config for Research

class ResearchConfig(Config):
	"""
	Json-like config object.

	The Config() contains all kinds of settings and user info that 
	could be useful in the implementation of Api wrapper.

	ResearchConfig inherits from Config, set environment specifically
	for backtesting Research.
	"""

	head = "Research"

	token = 'af755ad66f0c3db4da0b886c93c114f2-799e7d60d85fb3b3c58cfe3ba9d8fe25'

	body = {
			'username': 'zedyang',
			'password': 'cmbjx1008',
			'account_id': 8878848,
			'domain': 'api-fxpractice.oanda.com', # sandbox environment
			'domain_stream': 'stream-fxpractice.oanda.com',
			'ssl': True, # http or https.
			'version': 'v1',
			'header': {
			"Content-Type" : "application/x-www-form-urlencoded",
			'Connection' : 'keep-alive',
			'Authorization' : 'Bearer ' + token,
			'X-Accept-Datetime-Format' : 'unix'
		}
	}
	
	def __init__(self, head=0, token=0, body=0, env='practice'):
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
		self.body['ssl'] = True

#----------------------------------------------------------------------
# Historical data generator.

def get_data(oApi, count=500, granularity='M30', instrument='EUR_USD'):
	"""
	Get historical data for one instrument.

	parameters
	----------
	* instrument: string; the ticker of instrument.

	* granularity: string; sample rate of bar data. Examples:
		- 'S10' 10-seconds bar.
		- 'M1' 1-minute bar.
		- 'H3' 3-hours bar.
		- 'D'/'W'/'M' day/week/month(one).

	* count: integer; the number of bars to be retrieved, maximum is
	  5000, should not be specified if both start and end are specified.
	"""
	tots = lambda dt: int(dt.strftime('%s'))*1000000
	todt = lambda time: datetime.fromtimestamp(
						int(time)/1000000)
	update_dt = lambda d: d.update({'datetime': todt(d['time'])})
	
	resp = oApi.get_history(instrument = instrument,
							granularity = granularity,
							count = count,
							candle_format='midpoint')
	data = resp['candles']
	map(update_dt, data)
	df = pd.DataFrame(data)
	return df

#----------------------------------------------------------------------
# Statistical Methods; Algorithms.

def sma(series, window):
	"""
	Simple moving average.

	/LaTex
	SMA_t^{[n]}=\frac{\sum_{i=0}^{n-1} S_{t-i}}\{n}
	/LaTex

	parameters
	----------
	* series: list-like object.
	* window: SMA window.
	"""
	return pd.rolling_mean(pd.Series(series),window)

def ewma(series, com, span, halflife):
	"""
	Exponentially weighted moving average.

	"""
	pass

def macd(series, fast, slow):
	"""
	Moving Average Convergence-Divergence.

	"""
	pass

#----------------------------------------------------------------------
# Plot.

# Global settings:

matplotlib.rcParams.update({'font.size':8})

#----------------------------------------------------------------------
# Plot Methods.

def tsplot(data, ma1=12, ma2=26, save=True, name=None, hf=False):
	"""
	Plot/save Forex rate/volume time series 
	with two specified moving avg.

	parameters
	----------
	* data: pd.DataFrame data.
	* ma1, ma2: int, sma windows.
	* save: boolean, whether to save figure as pdf.
	* name: string, file name; if not save: ignore.
	* hf: boolean, enable high frequency plot setting or not.
	""" 
	# Data.
	volumeMin = 0
	smaSeries1 = sma(data.closeMid, ma1)
	smaSeries2 = sma(data.closeMid, ma2)

	fig = plt.figure(figsize=(15,5))
	if hf:
		timeFormat = '%Y-%m-%d %H:%M:%S'
	else:
		timeFormat = '%Y-%m-%d'
	# ===== Fig: Settings ===== .
	plt.gca().yaxis.set_major_locator(
		mticker.MaxNLocator(prune='lower'))
	plt.subplots_adjust(left=.07, bottom=.10, 
						right=.94, top=.95,
                        wspace=.20, hspace=.0)
	plt.ylabel('Forex Rate & Volume')

	# ----- AX1: Trend, SMAs ----- .
	# Construct axis object.
	ax1 = plt.subplot2grid((4,4), (0,0), 
						   rowspan=4, colspan=4)
	# Plot main series.
	ax1.plot(data.index, data.closeMid, label="rate", linewidth=1.5)
	ax1.plot(data.index, smaSeries1, label="ma1", linewidth=0.5)
	ax1.plot(data.index, smaSeries2, label="ma2", linewidth=0.5)
	# Settings.
	# 	Set x-labels, rotate.
	ax1.set_xticklabels([dt.strftime(timeFormat) for dt in list(
		data.datetime)[0::len(data)/11]]) 
	[label.set_rotation(30) for label in ax1.xaxis.get_ticklabels()]
	# 	Number of x-tickers.
	ax1.xaxis.set_major_locator(mticker.MaxNLocator(10)) 
	# 	Grid on.
	ax1.grid(True) 

	# ----- AX1v: Volumes ----- .
	ax1v = ax1.twinx()
	# Plot.
	ax1v.fill_between(data.index,volumeMin,data.volume,
	                  facecolor='black',alpha=.12)
	# Settings.
	ax1v.grid(False)
	ax1v.axes.yaxis.set_ticklabels([])
	ax1v.set_ylim(0,1.4*data.volume.max())

	if name==None:
		name = time.time()
	if save:
		fig.savefig('chart/{}.pdf'.format(name),
		facecolor=fig.get_facecolor())


	

