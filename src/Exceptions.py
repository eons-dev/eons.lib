class ActualType(type):
    def __repr__(self):
        return self.__name__

class MissingArgumentError(Exception, metaclass=ActualType):
    pass

class UserFunctorError(Exception, metaclass=ActualType):
    pass
    
class CommandUnsuccessful(UserFunctorError, metaclass=ActualType):
    pass

class FailedDependencyResolution(Exception, metaclass=ActualType):
    pass

class SelfRegisteringError(Exception, metaclass=ActualType):
    pass

class ClassNotFound(SelfRegisteringError, metaclass=ActualType):
    pass
