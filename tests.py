from api import *
from kernel import *
from utils import *

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
	print json.dumps(s, sort_keys=True, indent=4)

def test_odr():
	odr1 = Order(instrument = 'EUR_USD', 
		direction = ORDER_TYPE_BUY, 
		time = datetime(2013,10,10),
		price =9.82,
		volume = 100)
	odr1.view()
	print odr1.cashflow()
	return odr1

def test_pos():
	odr1 = Order(instrument = 'EUR_USD', 
		direction = ORDER_TYPE_BUY, 
		time = datetime(2013,10,10),
		price =9.82,
		volume = 100)
	pos = Position(odr1,0.0001)
	pos.view()
	print pos.calc_opening_value()
	print pos.calc_opening_cost_rev()
	print pos.calc_holding_value(2)

	odr2 = Order(instrument = 'EUR_USD', 
		direction = ORDER_TYPE_SHORT, 
		time = datetime(2013,10,10),
		price =9.00,
		volume = 100)

	pos2 = Position(odr2,0.0001)
	pos2.view()
	print pos2.calc_opening_value()
	print pos2.calc_opening_cost_rev()
	print pos2.calc_holding_value(2)

def test_pos_err():
	odr3 = Order(instrument = 'EUR_USD', 
		direction = ORDER_TYPE_SELL, 
		time = datetime(2013,10,10),
		price =9.00,
		volume = 100)
	pos3 = Position(odr3,0.0001)

def test_pos_close():
	odr = Order(instrument = 'EUR_USD', 
		direction = ORDER_TYPE_BUY, 
		time = datetime(2013,10,10),
		price =9.00,
		volume = 100)
	print odr.direction
	
	pos2 = Position(odr, 0.0001)

	pos2.view()
	print pos2.calc_opening_value()
	print pos2.calc_opening_cost_rev()
	print pos2.calc_holding_value(2)

	odr3 = Order(instrument = 'EUR_USD', 
		direction = ORDER_TYPE_SELL, 
		time = datetime(2013,10,11),
		price =8.00,
		volume = 100)

	pos2.close(odr3, 0.0001)
	pos2.view()
	




if __name__ == '__main__':
	#print ORDER_TYPE_SHORT
	test_pos_close()
	#test_pos_err()
	#test_info()
	#test_config()