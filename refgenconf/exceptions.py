""" Package exception types """

import abc

__all__ = ["MissingAssetError", "MissingConfigDataError", "MissingGenomeError",
           "RefgenconfError", "UnboundEnvironmentVariablesError"]


class RefgenconfError(Exception):
    """ Base exception type for this package """
    __metaclass__ = abc.ABCMeta


class MissingAssetError(RefgenconfError):
    """ Error type for request of an unavailable genome asset. """
    pass


class MissingConfigDataError(RefgenconfError):
    """ Missing required configuration instance items """
    pass



class MissingGenomeError(RefgenconfError):
    """ Error type for request of unknown genome/assembly. """
    pass


class UnboundEnvironmentVariablesError(RefgenconfError):
    """ Use of environment variable that isn't bound to a value. """
    pass
