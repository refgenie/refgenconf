import pytest
from .conftest import REQUESTS
from collections import Mapping


@pytest.mark.parametrize(["genome", "asset", "tag"], REQUESTS)
def test_is_asset_complete_returns_correct_result(genome, asset, tag, my_rgc):
    assert my_rgc.is_asset_complete(genome, asset, tag)


@pytest.mark.parametrize("genome", ["rCRSd"])
def test_get_genome_attributes(genome, my_rgc):
    assert isinstance(my_rgc.get_genome_attributes(genome), Mapping)
