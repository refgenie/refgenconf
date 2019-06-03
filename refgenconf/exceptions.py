""" Package exception types """

import abc
from collections import Iterable

__all__ = ["MissingAssetError", "MissingGenomeError", "RefgenconfError",
           "UnboundEnvironmentVariablesError"]


class RefgenconfError(Exception):
    """ Base exception type for this package """
    __metaclass__ = abc.ABCMeta


class MissingAssetError(RefgenconfError):
    """ Error type for request of an unavailable genome asset. """
    pass


class MissingGenomeError(RefgenconfError):
    """ Error type for request of unknown genome/assembly. """
    pass


class UnboundEnvironmentVariablesError(RefgenconfError):

    def __init__(self, env_vars):
        """
        Create the exception message by using the missing variable names.

        :param str | Iterable[str] env_vars: missing environment variables
        """
        if isinstance(env_vars, str):
            env_vars = [env_vars]
        if not isinstance(env_vars, Iterable):
            raise TypeError("Invalid env var names type: {}".
                            format(type(env_vars)))
        super(UnboundEnvironmentVariablesError, self).__init__(", ".join(env_vars))
