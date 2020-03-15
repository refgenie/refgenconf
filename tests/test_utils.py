import pytest
from collections import Mapping


@pytest.mark.parametrize(["genome", "asset", "tag"], [("rCRSd", "fasta", "default")])
def test_is_asset_complete_returns_correct_result(genome, asset, tag, ro_rgc):
    ro_rgc.pull(genome, asset, tag)
    assert ro_rgc.is_asset_complete(genome, asset, tag)


@pytest.mark.parametrize("genome", ["rCRSd"])
def test_get_genome_attributes(genome, ro_rgc):
    assert isinstance(ro_rgc.get_genome_attributes(genome), Mapping)
