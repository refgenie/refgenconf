""" Helper functions """

import os
import yacman
from .const import CFG_ENV_VARS


__all__ = ["select_genome_config"]


def select_genome_config(filename=None, conf_env_vars=CFG_ENV_VARS, **kwargs):
    """
    Get path to genome configuration file.

    :param str filename: name/path of genome configuration file
    :param Iterable[str] conf_env_vars: names of environment variables to
        consider; basically, a prioritized search list
    :return str: path to genome configuration file
    """
    return yacman.select_config(filename, conf_env_vars, **kwargs)


def unbound_env_vars(path):
    """
    Return collection of path parts that appear to be unbound env. vars.

    The given path is split on the active operating system's path delimiter;
    each resulting chunk is then deemed env.-var.-like if it begins with a
    dollar sign, and then os.getenv is queried to determine if it's bound.

    :param str path: Path to examine for unbound environment variables
    :return Iterable[str]: collection of path parts that appear to be unbound env. vars.
    """
    parts = path.split(os.path.sep)
    return [p for p in parts if p.startswith("$") and not os.getenv(p)]


def asciify_json_dict(json_dict):
    from ubiquerg.collection import asciify_dict
    return asciify_dict(json_dict)
