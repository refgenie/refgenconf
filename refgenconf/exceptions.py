""" Package exception types """

import abc

__all__ = ["MissingAssetError", "MissingGenomeError", "RefgenconfError"]


class RefgenconfError(Exception):
    """ Base exception type for this package """
    __metaclass__ = abc.ABCMeta


class MissingAssetError(RefgenconfError):
    """ Error type for request of an unavailable genome asset. """
    pass


class MissingGenomeError(RefgenconfError):
    """ Error type for request of unknown genome/assembly. """
    pass
