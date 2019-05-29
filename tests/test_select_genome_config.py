""" Tests for selection of genome configuration file """

import os
import pytest
from refgenconf import select_genome_config
from refgenconf.const import CFG_ENV_VARS
from ubiquerg import TmpEnv
from veracitools import ExpectContext

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


def _touch(p):
    if os.path.splitext(p)[1]:
        with open(p, 'w'):
            pass
    else:
        os.makedirs(p)
    return p


def _check_no_env_vars():
    """ Verify that none of the relevant env. var.'s are set. """
    assert all(os.getenv(v) is None for v in CFG_ENV_VARS)


def test_select_null():
    """ Test prioritized selection of genome configuration file. """
    _check_no_env_vars()
    assert select_genome_config(None) is None


@pytest.mark.parametrize(["setup", "expect"], [
    (lambda d: d.join("test-conf.yaml").strpath, lambda _: Exception),
    (lambda d: _touch(os.path.join(d.strpath, "test-conf")), lambda _: Exception),
    (lambda d: _touch(d.join("test-conf.yaml").strpath), lambda fp: fp)
])
def test_select_local_config_file(tmpdir, setup, expect):
    """ Selection of local filepath hinges on its existence as a file """
    _check_no_env_vars()
    path = setup(tmpdir)
    print("Path: {}".format(path))
    with ExpectContext(expect(path), select_genome_config) as ctx:
        ctx(path)


@pytest.mark.parametrize("env_var", CFG_ENV_VARS)
def test_select_via_env_var_implicit(env_var, tmpdir):
    """ Config file selection can leverage default environmanent variables. """
    conf_file = tmpdir.join("test-refgenconf-conf.yaml").strpath
    assert not os.path.exists(conf_file)
    with open(conf_file, 'w'):
        pass
    assert os.path.isfile(conf_file)
    with TmpEnv(overwrite=True, **{env_var: conf_file}):
        assert conf_file == select_genome_config(None)
