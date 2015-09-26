import numpy as np
import pandas as pd
import time, json, os
from datetime import datetime, timedelta

#----------------------------------------------------------------------
# Type Def

ORDER_TYPE_BUY = 'ORD_BUY'
ORDER_TYPE_SHORT = 'ORD_SHORT'
ORDER_TYPE_FILL = 'ORD_FILL'
ORDER_TYPE_SELL = 'ORD_SELL'
ORDER_TYPE_NONE = 'ORD_NONE'

POSITION_TYPE_LONG = 'POS_LONG'
POSITION_TYPE_SHORT = 'POS_SHORT'
POSITION_TYPE_NONE = 'POS_NONE'

POSITION_STATUS_OPEN = 'POS_OPENING'
POSITION_STATUS_CLOSED = 'POS_CLOSED'

ORD_POS_MAPPING = {
	ORDER_TYPE_BUY: POSITION_TYPE_LONG,
	ORDER_TYPE_SHORT: POSITION_TYPE_SHORT
}

POS_INT_MAPPING = {
	POSITION_TYPE_LONG: 1,
	POSITION_TYPE_SHORT: -1,
	POSITION_TYPE_NONE: 0
}

ORD_INT_MAPPING = {
	ORDER_TYPE_BUY: 1,
	ORDER_TYPE_SHORT: -1,
	ORDER_TYPE_NONE: 0
}

#----------------------------------------------------------------------
# Datetime and JSON methods

def dt_to_str(dt):
	return str(dt)

def serialize_dict(dic):
	""" 
	Serialize and copy a dictionary to one with string vals.
	WITHOUT changing its values.
	"""
	serialized_dic = dict()
	for d in dic:
		serialized_dic[d] = str(dic[d])
	return serialized_dic

def map_to_body(to):
	pass