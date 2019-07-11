""" Tests for updating a configuration object's genomes section """

import pytest
from attmap import PathExAttMap
from refgenconf import CFG_FOLDER_KEY, CFG_GENOMES_KEY, CFG_SERVER_KEY, \
    DEFAULT_SERVER, RefGenConf as RGC
from refgenconf.const import CFG_ASSETS_KEY
from tests.conftest import bind_to_assets, get_conf_genomes, CONF_DATA

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


def _asset_data_is_pxam(a, g, c):
    return isinstance(c[CFG_GENOMES_KEY][g][CFG_ASSETS_KEY][a], PathExAttMap)


@pytest.fixture(scope="function")
def rgc(tmpdir):
    """ Provide an RGC instance; avoid disk read/write and stay in memory. """
    return RGC({CFG_GENOMES_KEY: dict(CONF_DATA),
                CFG_FOLDER_KEY: tmpdir.strpath,
                CFG_SERVER_KEY: DEFAULT_SERVER})


@pytest.mark.parametrize("assembly", ["dm3"])
@pytest.mark.parametrize("validate", [
    lambda g, c: g in c[CFG_GENOMES_KEY],
    lambda g, c: isinstance(c[CFG_GENOMES_KEY], PathExAttMap)])
def test_new_genome(rgc, assembly, validate):
    """ update_genomes can insert new assembly. """
    assert assembly not in rgc[CFG_GENOMES_KEY]
    rgc.update_assets(assembly)
    assert validate(assembly, rgc)


@pytest.mark.parametrize("assembly", get_conf_genomes())
@pytest.mark.parametrize("asset", ["brand_new_asset", "align_index"])
@pytest.mark.parametrize("validate", [
    lambda a, g, c: a in c[CFG_GENOMES_KEY][g][CFG_ASSETS_KEY],
    _asset_data_is_pxam])
def test_new_asset(rgc, assembly, asset, validate):
    """ update_genomes can insert new asset for existing assembly. """
    assert assembly in rgc[CFG_GENOMES_KEY]
    assert asset not in rgc[CFG_GENOMES_KEY][assembly][CFG_ASSETS_KEY]
    rgc.update_assets(assembly, asset)
    assert validate(asset, assembly, rgc)


@pytest.mark.parametrize("assembly", ["dm3"])
@pytest.mark.parametrize("asset", ["brand_new_asset", "align_index"])
@pytest.mark.parametrize("validate", [
    lambda _, g, c: g in c[CFG_GENOMES_KEY],
    lambda a, g, c: a in c[CFG_GENOMES_KEY][g][CFG_ASSETS_KEY],
    lambda a, g, c: isinstance(c[CFG_GENOMES_KEY][g], PathExAttMap),
    _asset_data_is_pxam
])
def test_new_genome_and_asset(rgc, assembly, asset, validate):
    """ update_genomes can insert assembly and asset. """
    assert assembly not in rgc[CFG_GENOMES_KEY]
    rgc.update_assets(assembly, asset)
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
def test_update_asset_data(tmpdir, old_data, new_data, expected):
    """ update_genomes can modify data for existing assembly and asset. """
    assembly = "hg38"
    asset = "idx_bt2"
    c = RGC({CFG_GENOMES_KEY: {assembly: bind_to_assets({asset: old_data})},
             CFG_FOLDER_KEY: tmpdir.strpath,
             CFG_SERVER_KEY: DEFAULT_SERVER})
    def get_asset_data(refgencfg, a_name):
        return refgencfg[CFG_GENOMES_KEY][assembly][CFG_ASSETS_KEY][a_name].to_dict()
    assert expected != get_asset_data(c, asset)
    c.update_assets(assembly, asset, new_data)
    assert expected == get_asset_data(c, asset)


@pytest.mark.parametrize("args", [
    ("hg38", ["a1", "a2"]), (["g1", "g2"], "new_tool_index"),
    ("mm10", "align_index", "not_a_map")])
def test_illegal_argtype(rgc, args):
    """ update_genomes accurately restricts argument types. """
    with pytest.raises(TypeError):
        rgc.update_assets(*args)
