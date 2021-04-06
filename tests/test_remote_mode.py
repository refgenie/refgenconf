"""
RGC remote mode tests. These tests assert RefGenConf can communicate with
server and not be initialized in some cases
"""

import pytest

from refgenconf import RefGenConf
from refgenconf.const import CFG_SERVERS_KEY

from .test_populate import get_demo_dicts

__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"


class RemoteModeTests:
    @pytest.mark.parametrize("remote_class", ["http", "s3"])
    @pytest.mark.parametrize(
        "servers", ["http://rg.databio.org"]
    )  # TODO: change after release
    @pytest.mark.parametrize("reset", [True, False])
    @pytest.mark.parametrize("genome", ["rCRSd", "mouse_chrM2x"])
    @pytest.mark.parametrize("asset", ["fasta", "bowtie2_index"])
    def test_seekr(self, remote_class, servers, reset, genome, asset):
        unbound_rgc = RefGenConf()
        unbound_rgc.subscribe(servers, no_write=True, reset=reset)
        isinstance(
            unbound_rgc.seekr(
                genome_name=genome, asset_name=asset, remote_class=remote_class
            ),
            str,
        )

    @pytest.mark.parametrize("remote_class", ["http", "s3"])
    @pytest.mark.parametrize(
        "servers", ["http://rg.databio.org"]
    )  # TODO: change after release
    @pytest.mark.parametrize("reset", [True, False])
    @pytest.mark.parametrize("genome", ["rCRSd", "mouse_chrM2x"])
    @pytest.mark.parametrize("asset", ["fasta", "bowtie2_index"])
    def test_populater(self, remote_class, servers, reset, genome, asset):
        demo, nested_demo = get_demo_dicts(genome=genome, asset=asset, str_len=50)
        unbound_rgc = RefGenConf()
        unbound_rgc.subscribe(servers, no_write=True, reset=reset)
        assert unbound_rgc.seekr(
            genome_name=genome, asset_name=asset, remote_class=remote_class
        ) in str(unbound_rgc.populater(glob=demo, remote_class=remote_class))
        assert unbound_rgc.seekr(
            genome_name=genome, asset_name=asset, remote_class=remote_class
        ) in str(unbound_rgc.populater(glob=nested_demo, remote_class=remote_class))

    @pytest.mark.parametrize("servers", ["http://refgenomes.databio.org"])
    @pytest.mark.parametrize("reset", [True, False])
    @pytest.mark.parametrize("genome", ["rCRSd", "mouse_chrM2x", None])
    def test_listr(self, servers, reset, genome):
        unbound_rgc = RefGenConf()
        unbound_rgc.subscribe(servers, no_write=True, reset=reset)
        remote_list = unbound_rgc.listr(genome=genome)

        assert len(remote_list) == len(unbound_rgc[CFG_SERVERS_KEY])
        if genome is not None:
            assert all(
                [
                    len(assets_dict.keys()) == 1 and genome in assets_dict.keys()
                    for url, assets_dict in remote_list.items()
                ]
            )
        else:
            assert isinstance(remote_list, dict)
