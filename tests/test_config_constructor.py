""" Tests for basic functionality of the RefGenConf constructor """

import os
import pytest
from attmap import PathExAttMap
from refgenconf import RefGenConf, MissingConfigDataError
from refgenconf.const import CFG_FOLDER_KEY, CFG_SERVER_KEY

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


@pytest.mark.parametrize("present", [[], [(CFG_FOLDER_KEY, lambda d: d.strpath)]])
def test_missing_server_key(tmpdir, present):
    """ Omission of required config items causes expected exception """
    data = {k: f(tmpdir) for k, f in present}
    with pytest.raises(MissingConfigDataError):
        RefGenConf(data)


def test_genome_folder_is_pwd_if_no_folder_key_and_raw_entries_passed(rgc):
    data = PathExAttMap({k: v for k, v in rgc.items() if k != CFG_FOLDER_KEY})
    new_rgc = RefGenConf(data)
    assert os.getcwd() == new_rgc[CFG_FOLDER_KEY]


def test_genome_folder_is_config_file_folder_if_no_key_present(
        tmpdir, made_genome_config_file):
    conf_file = tmpdir.join("newconf.yaml").strpath
    assert not os.path.exists(conf_file)
    with open(conf_file, 'w') as fout, open(made_genome_config_file, 'r') as fin:
        for l in fin:
            if not l.startswith(CFG_FOLDER_KEY):
                fout.write(l)
    new_rgc = RefGenConf(conf_file)
    assert os.path.dirname(conf_file) == new_rgc[CFG_FOLDER_KEY]


def test_genome_folder_is_value_from_config_file_if_key_present(
        tmpdir_factory, tmpdir, made_genome_config_file):
    conf_file = tmpdir_factory.mktemp("data2").join("refgenie.yaml").strpath
    expected = tmpdir.strpath
    with open(made_genome_config_file, 'r') as fin, open(conf_file, 'w') as fout:
        found = False
        for l in fin:
            if l.startswith(CFG_FOLDER_KEY):
                fout.write("{}: {}\n".format(CFG_FOLDER_KEY, expected))
            else:
                fout.write(l)
                if l.startswith(CFG_SERVER_KEY):
                    found = True
        if not found:
            fout.write("{}: http://localhost".format(CFG_SERVER_KEY))
    rgc = RefGenConf(conf_file)
    assert expected != os.path.dirname(conf_file)
    assert expected == rgc[CFG_FOLDER_KEY]


def test_empty_rgc_is_false():
    assert bool(RefGenConf({CFG_SERVER_KEY: "http://localhost"})) is False


def test_nonempty_rgc_is_true(rgc):
    assert bool(rgc) is True
