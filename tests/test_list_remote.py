""" Tests for listing remotely available genomes and assets. """

from collections import OrderedDict
from refgenconf import RefGenConf, CFG_FOLDER_KEY, CFG_GENOMES_KEY, \
    CFG_SERVERS_KEY, DEFAULT_SERVER
from refgenconf.refgenconf import _download_json


def test_list_remote(rgc, tmpdir):
    """ Verify expected behavior of remote genome/asset listing. """
    new_rgc = RefGenConf(entries={CFG_FOLDER_KEY: tmpdir.strpath,
                          CFG_SERVERS_KEY: [DEFAULT_SERVER],
                          CFG_GENOMES_KEY: rgc[CFG_GENOMES_KEY]})
    result = new_rgc.listr()
    assert list(result.keys())[0].startswith(DEFAULT_SERVER)
    for server_url, asset_dict in result.items():
        assert isinstance(asset_dict, OrderedDict)
        assert len(asset_dict) == len(_download_json(DEFAULT_SERVER + "/genomes"))
