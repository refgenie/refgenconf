""" Tests for ReferenceGenomeConfiguration.get_asset """

import pytest
from refgenconf import *
from tests.conftest import get_conf_genomes, HG38_DATA, MM10_DATA, MITO_DATA

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


@pytest.mark.parametrize(
    "gname", ["not-a-genome", "this_should_fail", "YoUrCrazeeOrganism"])
@pytest.mark.parametrize("aname", [
    "kallisto", "hisat2", "tss_annotation", "gtf", "bowtie2", "blacklist",
    "bowtie", "star"])
def test_get_asset_missing_genome(rgc, gname, aname):
    """ Request for asset on a missing genome raises appropriate error. """
    assert gname not in rgc
    with pytest.raises(MissingGenomeError):
        _get_asset(rgc, gname, aname)


@pytest.mark.parametrize("gname", get_conf_genomes())
@pytest.mark.parametrize("aname", ["not-an-asset", "asset_fails"])
def test_get_asset_missing_asset(rgc, gname, aname):
    assert gname in rgc.genomes
    with pytest.raises(MissingAssetError):
        _get_asset(rgc, gname, aname)


@pytest.mark.parametrize(
    ["gname", "aname", "exp"],
    [(g, k, v) for g, data in
     [("hg38", HG38_DATA), ("mm10", MM10_DATA), ("rCRSd", MITO_DATA)]
     for k, v in data])
def test_get_asset_accuracy(rgc, gname, aname, exp):
    """ Asset request for particular genome is accurate. """
    assert exp == _get_asset(rgc, gname, aname)


def _get_asset(rgc, g, a):
    return rgc.get_asset(g, a, strict_exists=None)
