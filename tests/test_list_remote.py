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
    _assert_eq_as_sets(rgc.genomes_str(), genomes)
    _assert_eq_as_sets(rgc.assets_str(), assets)


def _assert_eq_as_sets(a, b):
    assert len(a) == len(b)
    assert set(a) == set(b)
