""" Package exception types """

import abc

__all__ = ["DownloadJsonError", "GenomeConfigFormatError", "MissingAssetError",
           "MissingConfigDataError", "MissingGenomeError",
           "RefgenconfError", "UnboundEnvironmentVariablesError", "ConfigNotCompliantError"]

DOC_URL = "http://refgenie.databio.org/en/latest/genome_config/"


class RefgenconfError(Exception):
    """ Base exception type for this package """
    __metaclass__ = abc.ABCMeta


class DownloadJsonError(RefgenconfError):
    """ Non-OK response from a JSON download attempt """
    def __init__(self, resp):
        super(DownloadJsonError, self).__init__(
            "No response provided" if resp is None else
            "JSON: {}".format(resp.json()))
        self.response = resp


class GenomeConfigFormatError(RefgenconfError):
    """ Exception for invalid genome config file format. """
    def __init__(self, msg):
        spacing = " " if msg[-1] in ["?", ".", "\n"] else "; "
        suggest = "For config format documentation please see " + DOC_URL
        super(GenomeConfigFormatError, self).__init__(msg + spacing + suggest)


class MissingAssetError(RefgenconfError):
    """ Error type for request of an unavailable genome asset. """
    pass


class MissingConfigDataError(RefgenconfError):
    """ Missing required configuration instance items """
    pass


class ConfigNotCompliantError(GenomeConfigFormatError):
    """ The format of the config file does not match required version/standards """
    pass


class MissingGenomeError(RefgenconfError):
    """ Error type for request of unknown genome/assembly. """
    pass


class UnboundEnvironmentVariablesError(RefgenconfError):
    """ Use of environment variable that isn't bound to a value. """
    pass
