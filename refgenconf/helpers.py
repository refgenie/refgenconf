""" Helper functions """

import os
from yacman import select_config
from .const import CFG_ENV_VARS, BUILD_STATS_DIR
from re import sub
from ubiquerg import is_command_callable


__all__ = ["select_genome_config", "get_dir_digest"]


def select_genome_config(filename=None, conf_env_vars=CFG_ENV_VARS, **kwargs):
    """
    Get path to genome configuration file.

    :param str filename: name/path of genome configuration file
    :param Iterable[str] conf_env_vars: names of environment variables to
        consider; basically, a prioritized search list
    :return str: path to genome configuration file
    """
    return select_config(filename, conf_env_vars, **kwargs)


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


def get_dir_digest(path, pm=None):
    """
    Generate a MD5 digest that reflects just the contents of the
    files in the selected directory.

    :param str path: path to the directory to digest
    :param pypiper.PipelineManager pm: a pipeline object, optional.
    The subprocess module will be used if not provided
    :return str: a digest, e.g. a3c46f201a3ce7831d85cf4a125aa334
    """
    if not is_command_callable("md5sum"):
        raise OSError("md5sum command line tool is required for asset digest "
                      "calculation. \n"
                      "Install and try again, e.g on macOS: 'brew install "
                      "md5sha1sum'")
    cmd = "cd {}; find . -type f -not -path './" + BUILD_STATS_DIR + \
          "*' -exec md5sum {{}} \; | sort -k 2 | awk '{{print $1}}' | md5sum"
    try:
        x = pm.checkprint(cmd.format(path))
    except AttributeError:
        try:
            from subprocess import check_output
            x = check_output(cmd.format(path), shell=True).decode("utf-8")
        except Exception as e:

            return
    return str(sub(r'\W+', '', x))  # strips non-alphanumeric
