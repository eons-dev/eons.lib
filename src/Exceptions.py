class ActualType(type):
    def __repr__(self):
        return self.__name__



class MissingArgumentError(Exception, metaclass=ActualType):
    pass



class UserFunctorError(Exception, metaclass=ActualType):
    pass
    
class CommandUnsuccessful(UserFunctorError, metaclass=ActualType):
    pass



class ErrorResolutionError(Exception, metaclass=ActualType):
    pass

class FailedErrorResolution(ErrorResolutionError, metaclass=ActualType):
    pass



class SelfRegisteringError(Exception, metaclass=ActualType):
    pass

class ClassNotFound(SelfRegisteringError, metaclass=ActualType):
    pass



class HelpWanted(Exception, metaclass=ActualType):
    pass

class HelpWantedWithRegistering(HelpWanted, metaclass=ActualType):
    pass



class Fatal(Exception, metaclass=ActualType):
    pass

class FatalCannotExecute(Fatal, metaclass=ActualType):
    pass