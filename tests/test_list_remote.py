""" Tests for listing remotely available genomes and assets. """

import mock
from refgenconf import RefGenConf

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


def test_list_remote(rgc):
    """ Verify expected behavior of remote genome/asset listing. """
    new_rgc = RefGenConf()
    with mock.patch("refgenconf.refgenconf._read_remote_data",
                    return_value=rgc.genomes):
        genomes, assets = new_rgc.list_remote(get_url=lambda _: "irrelevant")
    exp_genomes = rgc.genomes_str()
    exp_assets = rgc.assets_str()
    _assert_eq_as_sets(exp_genomes, genomes)
    _assert_eq_as_sets(exp_assets, assets)


def _assert_eq_as_sets(a, b):
    assert len(a) == len(b)
    assert set(a) == set(b)
