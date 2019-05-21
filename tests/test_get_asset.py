""" Tests for ReferenceGenomeConfiguration.get_asset """

import pytest
from refgenconf import *

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


@pytest.mark.skip("not implemented")
@pytest.mark.parametrize(
    "gname", ["not-a-genome", "this_should_fail", "YoUrCrazeeOrganism"])
@pytest.mark.parametrize("aname", [
    "kallisto", "hisat2", "tss_annotation", "gtf", "bowtie2", "blacklist",
    "bowtie", "star"])
def test_get_asset_missing_assembly(rgc, gname, aname):
    assert gname not in rgc
    with pytest.raises(MissingGenomeError):
        rgc.get_asset(gname, aname)


@pytest.mark.skip("not implemented")
def test_get_asset_missing_asset(rgc):
    pass
