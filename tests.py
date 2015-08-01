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



if __name__ == '__main__':
	
	test_events()
	#test_config()