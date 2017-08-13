_registered_classes = {}

def register_class(target_class, alias):
	""" Registers a class with the factory and allows later retrieval without
		the need to include the package where it originates. This allows
		intantiators to constract instances of classes withot knowing anything
		about them.
		You should call factory_register_class in the package where you define
		the classs that you want to make instantiable dynamically imediately after
		the end of the declaration of the class.
		The program that needs to intantiate the classes will only need to include
		the retrieve_class (see later) and recover the class reference from
		the factory registry.
	"""
	# simply add the class to the registry
	_registered_classes[alias] = target_class
	
def retrieve_class(alias):
	""" Tries to find a class in the registry by alias. If found it will return
		a reference to that class. If the alias is not in the registry it will raise
		an exception.
	"""
	try:
		return _registered_classes[alias]
	except KeyError:
		raise KeyError("class with alias %s not registred; use register_class" % alias)
		