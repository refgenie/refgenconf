""" Tests for updating a configuration object's genomes section """

import pytest
from attmap import PathExAttMap
from refgenconf import CFG_GENOMES_KEY, RefGenConf as RGC
from tests.conftest import get_conf_genomes, CONF_DATA

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


@pytest.fixture(scope="function")
def rgc():
    """ Provide an RGC instance; avoid disk read/write and stay in memory. """
    return RGC({CFG_GENOMES_KEY: dict(CONF_DATA)})


@pytest.mark.parametrize("assembly", ["dm3"])
@pytest.mark.parametrize("validate", [
    lambda a, c: a in c[CFG_GENOMES_KEY],
    lambda a, c: isinstance(c[CFG_GENOMES_KEY][a], PathExAttMap)])
def test_new_genome(rgc, assembly, validate):
    """ update_genomes can insert new assembly. """
    assert assembly not in rgc[CFG_GENOMES_KEY]
    rgc.update_genomes(assembly)
    assert validate(assembly, rgc)


@pytest.mark.parametrize("assembly", get_conf_genomes())
@pytest.mark.parametrize("asset", ["brand_new_asset", "align_index"])
@pytest.mark.parametrize("validate", [
    lambda a, g, c: a in c[CFG_GENOMES_KEY][g],
    lambda a, g, c: isinstance(c[CFG_GENOMES_KEY][g][a], PathExAttMap)])
def test_new_asset(rgc, assembly, asset, validate):
    """ update_genomes can insert new asset for existing assembly. """
    assert assembly in rgc[CFG_GENOMES_KEY]
    assert asset not in rgc[CFG_GENOMES_KEY][assembly]
    rgc.update_genomes(assembly, asset)
    assert validate(asset, assembly, rgc)


@pytest.mark.parametrize("assembly", ["dm3"])
@pytest.mark.parametrize("asset", ["brand_new_asset", "align_index"])
@pytest.mark.parametrize("validate", [
    lambda _, g, c: g in c[CFG_GENOMES_KEY],
    lambda a, g, c: a in c[CFG_GENOMES_KEY][g],
    lambda a, g, c: isinstance(c[CFG_GENOMES_KEY][g], PathExAttMap),
    lambda a, g, c: isinstance(c[CFG_GENOMES_KEY][g][a], PathExAttMap)
])
def test_new_genome_and_asset(rgc, assembly, asset, validate):
    """ update_genomes can insert assembly and asset. """
    assert assembly not in rgc[CFG_GENOMES_KEY]
    rgc.update_genomes(assembly, asset)
    assert validate(asset, assembly, rgc)


@pytest.mark.parametrize(["old_data", "new_data", "expected"], [
    ({"size": "4G"}, {"path": "/home/res/gen/bt2.hg38"},
     {"size": "4G", "path": "/home/res/gen/bt2.hg38"}),
    ({}, {"size": "4G"}, {"size": "4G"}),
    ({}, {"path": "/home/res/gen/bt2.hg38"}, {"path": "/home/res/gen/bt2.hg38"}),
    ({}, {"size": "4G", "path": "/home/res/gen/bt2.hg38"},
     {"size": "4G", "path": "/home/res/gen/bt2.hg38"}),
    ({"size": "4G"}, {"size": "2G"}, {"size": "2G"})
])
def test_update_asset_data(old_data, new_data, expected):
    """ update_genomes can modify data for existing assembly and asset. """
    assembly = "hg38"
    asset = "idx_bt2"
    c = RGC({CFG_GENOMES_KEY: {assembly: {asset: old_data}}})
    assert expected != c[CFG_GENOMES_KEY][assembly][asset].to_dict()
    c.update_genomes(assembly, asset, new_data)
    assert expected == c[CFG_GENOMES_KEY][assembly][asset].to_dict()


@pytest.mark.parametrize("args", [
    ("hg38", ["a1", "a2"]), (["g1", "g2"], "new_tool_index"),
    ("mm10", "align_index", "not_a_map")])
def test_illegal_argtype(rgc, args):
    """ update_genomes accurately restricts argument types. """
    with pytest.raises(TypeError):
        rgc.update_genomes(*args)
