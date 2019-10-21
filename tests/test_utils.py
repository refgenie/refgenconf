import pytest
from .conftest import REQUESTS
from collections import Mapping


@pytest.mark.parametrize(["genome", "asset", "tag"], REQUESTS)
def test_is_asset_complete_returns_correct_result(genome, asset, tag, ro_rgc):
    assert ro_rgc.is_asset_complete(genome, asset, tag)


@pytest.mark.parametrize("genome", ["rCRSd"])
def test_get_genome_attributes(genome, ro_rgc):
    assert isinstance(ro_rgc.get_genome_attributes(genome), Mapping)
