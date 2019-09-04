""" Tests for ReferenceGenomeConfiguration.get_asset """

import os
import pytest
from refgenconf import *
from refgenconf.const import CFG_ASSETS_KEY
from tests.conftest import bind_to_assets, get_conf_genomes, \
    lift_into_path_pair, CONF_DATA, \
    HG38_DATA, MM10_DATA, MITO_DATA
from veracitools import ExpectContext

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


@pytest.fixture
def temp_asset_spec(tmpdir):
    """ Provide test case with a temp asset path. """
    fn = "semaphore.txt"
    fp = tmpdir.join(fn).strpath
    assert not os.path.exists(fp)
    return fp


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
    """ Request for unknown asset raises appropriate error. """
    assert gname in rgc.genomes
    with pytest.raises(MissingAssetError):
        _get_asset(rgc, gname, aname)


# TODO: test tag and seek keys here
@pytest.mark.parametrize(["gname", "aname", "tag"], [("rCRSd", "bowtie2_index", "default")])
def test_get_asset_accuracy(my_rgc, gname, aname, tag):
    """ Asset request for particular genome is accurate. """
    print(_get_asset(my_rgc, gname, aname, tag_name=tag))
    assert _get_asset(my_rgc, gname, aname, tag_name=tag) is not None


@pytest.mark.parametrize("check_exist", [lambda: True, lambda _1, _2: True])
@pytest.mark.parametrize(
    ["gname", "aname"], [(g, a) for g, data in CONF_DATA for a in data])
def test_check_exist_param_type(rgc, check_exist, gname, aname):
    """ The asset existence check must be a one-arg function. """
    with pytest.raises(TypeError):
        rgc.get_asset(gname, aname, check_exist=check_exist)


@pytest.mark.parametrize(
    ["gname", "aname", "tname"],
    [("rCRSd", "fasta", "default"), ("rCRSd", "fasta", "test"), ("mouse_chrM2", "fasta", "default")])
def test_asset_already_exists(my_rgc, gname, aname, tname):

    def folder():
        return my_rgc[CFG_FOLDER_KEY]
    fullpath = os.path.join(folder(), gname, aname, tname)
    print("fullpath: " + fullpath)
    assert fullpath == my_rgc.get_asset(gname, aname, tname)


def _get_asset(rgc, g, a, **kwargs):
    """
    Call the asset fetch function.

    :param refgenconf.RefGenConf rgc: configuration instance
    :param str g: genome name
    :param str a: asset name
    """
    kwds = {"strict_exists": None}
    kwds.update(kwargs)
    return rgc.get_asset(g, a, **kwds)
