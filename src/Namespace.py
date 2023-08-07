import logging

# The Eons way of tracking logical & extensible groupings.
class Namespace:

	def __init__(this, namespaces = None):
		this.namespaces = []

		if (isinstance(namespaces, str)):
			this.namespaces = namespaces.split(':')
			this.namespaces = [namespace for namespace in this.namespaces if len(namespace)]
		elif (isinstance(namespaces, list)):
			this.namespaces = namespaces
		elif (isinstance(namespaces, Namespace)):
			this.namespaces = namespaces.namespaces

	# Get a subset from *this.
	def Slice(this, start=0, end=None):
		return Namespace(this.namespaces[start:end])
	
	def __str__(this):
		ret = "::" + ":".join(this.namespaces)
		if (ret == "::"):
			return "::"
		return ret + ":"

	# Get a namespace string as something more reasonable in python.
	def ToName(this):
		if (not len(this.namespaces)):
			return ""
		return "_".join(this.namespaces) + "_"
	
	def __iadd__(this, other):
		this.namespaces.append(Namespace(other).namespaces)
		return this
	
	def __isub__(this, other):
		this.namespaces = this.namespaces[:-len(Namespace(other).namespaces)]
		return this


class NamespaceTracker:
	def __init__(this):
		# Singletons man...
		if "instance" not in NamespaceTracker.__dict__:
			logging.debug(f"Creating new NamespaceTracker: {this}")
			NamespaceTracker.instance = this
		else:
			return None

		this.last = Namespace()

	@staticmethod
	def Instance():
		if "instance" not in NamespaceTracker.__dict__:
			NamespaceTracker()
		return NamespaceTracker.instance

# Decorator to add a namespace to a class.
# Should look like @namespace('foo::bar')
def namespace(ns):
	def DecorateWithNamespace(cls):
		locale = Namespace(ns)
		prepend = locale.ToName()
		NamespaceTracker.Instance().last = locale
		return type(f"{prepend}{cls.__name__}", cls.__bases__, dict(cls.__dict__))
	return DecorateWithNamespace