""" Helper functions """

import yacman
from .const import CFG_ENV_VARS


__all__ = ["select_genome_config"]


def select_genome_config(filename, conf_env_vars=None):
    """
    Get path to genome configuration file.

    :param str filename: name/path of genome configuration file
    :param Iterable[str] conf_env_vars: names of environment variables to
        consider; basically, a prioritized search list
    :return str: path to genome configuration file
    """
    return yacman.select_config(filename, conf_env_vars or CFG_ENV_VARS)
