""" Tests for listing remotely available genomes and assets. """

import mock
from refgenconf import RefGenConf, CFG_FOLDER_KEY, CFG_GENOMES_KEY, CFG_SERVER_KEY

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


def test_list_remote(rgc, tmpdir):
    """ Verify expected behavior of remote genome/asset listing. """
    new_rgc = RefGenConf({CFG_FOLDER_KEY: tmpdir.strpath,
                          CFG_SERVER_KEY: "http://localhost",
                          CFG_GENOMES_KEY: rgc[CFG_GENOMES_KEY]})
    print("NEW RGC KEYS: {}".format(list(new_rgc.keys())))
    with mock.patch("refgenconf.refgenconf._read_remote_data",
                    return_value=rgc.genomes):
        genomes, assets = new_rgc.list_remote(get_url=lambda _: "irrelevant")
    _assert_eq_as_sets(rgc.genomes_str(), genomes)
    _assert_eq_as_sets(rgc.assets_str(), assets)


def _assert_eq_as_sets(a, b):
    assert len(a) == len(b)
    assert set(a) == set(b)
