
class OANDA_RequestError(Exception):
	"""
	HTTP Request Error, raised when response is not properly gotten:
	* GET response.status code != 200.
	* POST response.status code != 201.
	* Connection timed out.
	* ...


	"""
	pass

class OANDA_EnvError(Exception):
	"""
	Environment Error, raised when requests are made under an
	improper Environment, for example:
	* create_sanbox_acc in practice/real
	* ...


	"""
	pass

class OANDA_DataConstructorError(Exception):
	"""
	Data Constructor Error, raised when required data object is not able
	to be constructed.
	* tick/bar data object construction error.
	* ...


	"""
	pass