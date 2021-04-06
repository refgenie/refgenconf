"""
RGC remote mode tests. These tests assert RefGenConf can communicate with
server and not be initialized in some cases
"""

import pytest

from refgenconf import RefGenConf

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
        unbound_rgc.seekr(
            genome_name=genome, asset_name=asset, remote_class=remote_class
        )
