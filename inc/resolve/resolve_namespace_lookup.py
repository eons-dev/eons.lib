import eons
import sys
import builtins
import logging

# Try resolving a NameError by going up the namespace tree and looking for the object.
class namespace_lookup(eons.ErrorResolution):
	def __init__(this, name="namespace_lookup"):
		super().__init__(name)

		this.ApplyTo('NameError', "name 'SUBJECT' is not defined")
		this.ApplyTo('AttributeError', "'NameError' object has no attribute 'SUBJECT'")

	def Resolve(this):
		requested = None
		
		for i in range(eons.FunctorTracker.GetCount()):
			ns = eons.FunctorTracker.GetCurrentNamespace(i)
			namespacedObjectName = ns.ToName() + this.error.subject

			# Module was already registered, just inject it.
			if (namespacedObjectName in sys.modules.keys()):
				eons.util.BlackMagick.InjectIntoModule(
					this.function,
					namespacedObjectName,
					sys.modules[namespacedObjectName]
				)
				# Create the symbol as an instance of the namespaced module's class.
				this.executor.SetGlobal(this.error.subject, getattr(sys.modules[namespacedObjectName], this.error.subject)())
				this.error.resolution.successful = True
				return
			
			# Maybe we can download it???
			try:
				requested = this.GetExecutor().GetRegistered(
					this.error.subject,
					packageType = this.executor.default.package.type,
					namespace = ns)
			except:
				continue
		
		if (not requested):
			this.error.resolution.successful = False
			return
		
		# We don't know the module, but we have the object.
		this.executor.SetGlobal(this.error.subject, requested)
		this.error.resolution.successful = eons.util.HasAttr(builtins, this.error.subject)

