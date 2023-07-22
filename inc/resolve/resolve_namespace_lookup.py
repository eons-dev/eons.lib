import eons
import sys
import builtins
import logging

# Try resolving a NameError by going up the namespace tree and looking for the object.
class namespace_lookup(eons.ErrorResolution):
	def __init__(this, name="namespace_lookup"):
		super().__init__(name)

		this.ApplyTo('NameError', "name 'OBJECT' is not defined")

	def Resolve(this):
		requested = None
		
		for i in range(eons.FunctorTracker.GetCount()):
			ns = eons.FunctorTracker.GetCurrentNamespace(i)
			namespacedObjectName = ns.ToName() + this.errorObject

			# Module was already registered, just inject it.
			if (namespacedObjectName in sys.modules.keys()):
				eons.util.BlackMagick.InjectIntoModule(
					this.function,
					this.errorObject,
					sys.modules[namespacedObjectName]
				)
				this.errorShouldBeResolved = True
				return
			
			# Maybe we can download it???
			try:
				requested = this.GetExecutor().GetRegistered(
					this.errorObject,
					packageType = this.executor.defaultPackageType,
					namespace = ns)
			except:
				continue
		
		if (not requested):
			this.errorShouldBeResolved = False
			return
		
		# We don't know the module, but we have the object.
		this.executor.SetGlobal(this.errorObject, requested)
		this.errorShouldBeResolved = eons.util.HasAttr(builtins, this.errorObject)

