""" Helper functions """

import os
import yacman
from .const import CFG_ENV_VARS


__all__ = ["select_genome_config"]


def select_genome_config(filename, conf_env_vars=None, **kwargs):
    """
    Get path to genome configuration file.

    :param str filename: name/path of genome configuration file
    :param Iterable[str] conf_env_vars: names of environment variables to
        consider; basically, a prioritized search list
    :return str: path to genome configuration file
    """
    return yacman.select_config(filename, conf_env_vars or CFG_ENV_VARS, **kwargs)


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


def _asciify_list(data):
    """ https://gist.github.com/chris-hailstorm/4989643 """
    ret = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _asciify_list(item)
        elif isinstance(item, dict):
            item = asciify_dict(item)
        ret.append(item)
    return ret


def asciify_dict(data):
    """ https://gist.github.com/chris-hailstorm/4989643 """
    ret = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _asciify_list(value)
        elif isinstance(value, dict):
            value = asciify_dict(value)
        ret[key] = value
    return ret
