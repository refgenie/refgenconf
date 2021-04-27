""" Tests for listing remotely available genomes and assets. """

from collections import OrderedDict

import pytest

from refgenconf import (
    API_VERSION,
    CFG_FOLDER_KEY,
    CFG_GENOMES_KEY,
    CFG_SERVERS_KEY,
    RefGenConf,
)
from refgenconf.helpers import send_data_request


@pytest.mark.parametrize(
    "genome", [["human_repeats"], ["human_repeats", "rCRSd"], None]
)
def test_list_remote(my_rgc, genome):
    """Verify expected behavior of remote genome/asset listing."""
    assert len(my_rgc[CFG_SERVERS_KEY]) == 1, "Expected only one test server"
    server = my_rgc[CFG_SERVERS_KEY][0]
    result = my_rgc.listr(genome=genome, as_digests=True)
    assert (
        len(result.keys()) == 1
    ), "More servers in list remote result than subscribed to"
    server_key = list(result.keys())[0]
    assert server_key.startswith(server)
    json_genomes = send_data_request(server_key, params={"includeSeekKeys": True})
    if not genome:
        assert len(json_genomes) == len(result[server_key])
        for g, assets in json_genomes.items():
            assert len(assets) == len(result[server_key][g])
    else:
        assert len(genome) == len(result[server_key])


def test_list_remote_faulty(my_rgc):
    my_rgc[CFG_SERVERS_KEY].append("www.google.com")
    assert len(my_rgc[CFG_SERVERS_KEY]) == 2, "Expected two test servers"
    result = my_rgc.listr()
    assert (
        len(result.keys()) == 1
    ), "More servers in list remote result than subscribed to"
