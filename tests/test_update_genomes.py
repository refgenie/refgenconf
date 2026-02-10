"""Tests for updating a configuration object's genomes section"""

import pytest
from attmap import PathExAttMap

from refgenconf import CFG_GENOMES_KEY
from refgenconf.const import CFG_ASSETS_KEY

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


def _asset_data_is_pxam(a, g, c):
    return isinstance(c[CFG_GENOMES_KEY][g][CFG_ASSETS_KEY][a], PathExAttMap)


@pytest.mark.parametrize("assembly", ["human_repeats", "rCRSd"])
@pytest.mark.parametrize("asset", ["brand_new_asset", "align_index"])
@pytest.mark.parametrize(
    "validate",
    [lambda a, g, c: a in c[CFG_GENOMES_KEY][g][CFG_ASSETS_KEY], _asset_data_is_pxam],
)
def test_new_asset(my_rgc, assembly, asset, validate):
    """update_genomes can insert new asset for existing assembly."""
    assert assembly in my_rgc[CFG_GENOMES_KEY]
    assert asset not in my_rgc[CFG_GENOMES_KEY][assembly][CFG_ASSETS_KEY]
    my_rgc.update_assets(assembly, asset)
    assert validate(asset, assembly, my_rgc)


# @pytest.mark.parametrize(["old_data", "new_data", "expected"], [
#     ({"size": "4G"}, {"path": "/home/res/gen/bt2.hg38"},
#      {"size": "4G", "path": "/home/res/gen/bt2.hg38"}),
#     ({}, {"size": "4G"}, {"size": "4G"}),
#     ({}, {"path": "/home/res/gen/bt2.hg38"}, {"path": "/home/res/gen/bt2.hg38"}),
#     ({}, {"size": "4G", "path": "/home/res/gen/bt2.hg38"},
#      {"size": "4G", "path": "/home/res/gen/bt2.hg38"}),
#     ({"size": "4G"}, {"size": "2G"}, {"size": "2G"})
# ])
# def test_update_asset_data(tmpdir, old_data, new_data, expected):
#     """ update_genomes can modify data for existing assembly and asset. """
#     assembly = "hg38"
#     asset = "idx_bt2"
#     c = RGC(entries={CFG_GENOMES_KEY: {assembly: bind_to_assets({asset: old_data})},
#              CFG_FOLDER_KEY: tmpdir.strpath,
#              CFG_SERVER_KEY: DEFAULT_SERVER})
#
#     def get_asset_data(refgencfg, a_name):
#         return refgencfg[CFG_GENOMES_KEY][assembly][CFG_ASSETS_KEY][a_name].to_dict()
#     assert expected != get_asset_data(c, asset)
#     c.update_assets(assembly, asset, new_data)
#     assert expected == get_asset_data(c, asset)


@pytest.mark.parametrize(
    "args",
    [
        ("human_repeats", ["a1", "a2"]),
        (["g1", "g2"], "new_tool_index"),
        ("rCRSd", "align_index", "not_a_map"),
    ],
)
def test_illegal_argtype(my_rgc, args):
    """update_genomes accurately restricts argument types."""
    with pytest.raises(TypeError):
        my_rgc.update_assets(*args)
