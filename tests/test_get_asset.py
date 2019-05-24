""" Tests for ReferenceGenomeConfiguration.get_asset """

import pytest
from refgenconf import *
from tests.conftest import get_conf_genomes, CONF_DATA, HG38_DATA, MM10_DATA, \
    MITO_DATA

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


@pytest.mark.parametrize("check_exist", [lambda: True, lambda _1, _2: True])
@pytest.mark.parametrize(
    ["gname", "aname"], [(g, a) for g, data in CONF_DATA for a in data])
def test_check_exist_param_type(rgc, check_exist, gname, aname):
    with pytest.raises(TypeError):
        rgc.get_asset(gname, aname, check_exist=check_exist)


@pytest.mark.skip("not implemented")
def test_existence_check_strict():
    pass


@pytest.mark.skip("not implemented")
def test_existence_check_non_strict():
    pass


def _get_asset(rgc, g, a, **kwargs):
    kwds = {"strict_exists": None}
    kwds.update(kwargs)
    return rgc.get_asset(g, a, **kwds)
