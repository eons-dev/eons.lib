class ActualType(type):
	def __repr__(self):
		return self.__name__

class GlobalError(Exception, metaclass=ActualType): pass

class NotInstantiableError(Exception, metaclass=ActualType): pass

class MissingArgumentError(Exception, metaclass=ActualType): pass

class FunctorError(Exception, metaclass=ActualType): pass
class MissingMethodError(FunctorError, metaclass=ActualType): pass
class CommandUnsuccessful(FunctorError, metaclass=ActualType): pass
class InvalidNext(FunctorError, metaclass=ActualType): pass

class ExecutorError(FunctorError, metaclass=ActualType): pass
class ExecutorSetupError(ExecutorError, metaclass=ActualType): pass

class ErrorResolutionError(Exception, metaclass=ActualType): pass
class FailedErrorResolution(ErrorResolutionError, metaclass=ActualType): pass

class SelfRegisteringError(Exception, metaclass=ActualType): pass
class ClassNotFound(SelfRegisteringError, metaclass=ActualType): pass

class HelpWanted(Exception, metaclass=ActualType): pass
class HelpWantedWithRegistering(HelpWanted, metaclass=ActualType): pass

class Fatal(Exception, metaclass=ActualType): pass
class FatalCannotExecute(Fatal, metaclass=ActualType): pass

class PackageError(Exception, metaclass=ActualType): pass

class MethodPendingPopulation(Exception, metaclass=ActualType): pass
