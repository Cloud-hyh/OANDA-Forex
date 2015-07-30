import json
import requests

class BaseApi(object):
	"""

	"""

	_domain = 'stream-fxpractice.oanda.com'
	_token = '######################' + \
			 '######################'
	_account_id = '#######'

	def __init__(self):
		"""

		"""
		super(BaseApi, self).__init__()
		

	def make_stream(self):
		instruments = "EUR_USD,USD_CAD"
		header = {
					'Connection' : 'keep-alive',
					'Authorization' : 'Bearer ' + self._token
				 }
		params = {
					'instruments' : instruments,
					'accountId' : self._account_id
				 }
		s = requests.session()
		url = 'https://'+ self._domain +'/v1/prices'
		req = requests.Request('GET', 
								url=url, 
								headers = header, 
								params = params)
		
		pre = req.prepare()
		response = s.send(pre, stream = True, verify = False)
		
		for line in response.iter_lines(1):
			if line:
				try:
					msg = json.loads(line)
				except Exception as e:
					print "[Stream]Failed to convert message into json\n" + str(e)
					return
				if True:
					print line
				else:
					if msg.has_key("instrument") or msg.has_key("tick"):
						print line

		


if __name__ == '__main__':
	api = BaseApi()
	api.make_stream()



		