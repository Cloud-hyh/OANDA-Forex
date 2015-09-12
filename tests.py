from api import *

#----------------------------------------------------------------------
# Generic tests.

def test_events():

	event = BaseEvent()
	m_event = MarketEvent(data={'price':1.5})
	event.view()
	m_event.view()
	print m_event, m_event.body, m_event.head
	print event

def test_config():
	cfig = Config()
	print cfig.body, cfig.head, cfig.token
	cfig.view()

def test_info():
	
	q1 = EventQueue()
	q2 = EventQueue()
	q = {'mkt': q1, 'bar': q2}

	myapi = PyApi(Config(), q)
	#q1.bind('ETYPE_MKT', myapi.on_market_impulse)

	#q1.open()
	s = myapi.get_instruments()
	print s




if __name__ == '__main__':
	
	test_info()
	#test_config()