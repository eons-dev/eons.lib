class MissingArgumentError(Exception):
    pass

class UserFunctorError(Exception):
    pass

class CommandUnsuccessful(UserFunctorError):
    pass