""" Package exception types """

import abc

__all__ = ["DownloadJsonError", "GenomeConfigFormatError", "MissingAssetError",
           "MissingConfigDataError", "MissingGenomeError",
           "RefgenconfError", "UnboundEnvironmentVariablesError"]


class RefgenconfError(Exception):
    """ Base exception type for this package """
    __metaclass__ = abc.ABCMeta


class DownloadJsonError(RefgenconfError):
    """ Non-OK response from a JSON download attempt """
    pass


class GenomeConfigFormatError(RefgenconfError):
    """ Exception for invalid genome config file format. """
    def __init__(self, msg):
        spacing = " " if msg[-1] in ["?", "."] else "; "
        suggest = "For config format documentation please see " \
                  "http://refgenie.databio.org/en/dev/genome_config/"
        super(GenomeConfigFormatError, self).__init__(msg + spacing + suggest)


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
