""" Basic RGC asset tests """

import pytest
from tests.conftest import CONF_DATA, HG38_DATA, MM10_DATA, MITO_DATA

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


BT2_EXP = ["hg38", "mm10", "rCRSd"]
BT1_EXP = ["rCRSd"]
HISAT2_EXP = ["hg38"]
BLACKLIST_EXP = ["mm10"]
TSS_EXP = ["hg38"]
GTF_EXP = ["hg38"]


def test_assets_dict(rgc):
    """ Verify mapping of genome name to assets key-value collection. """
    assert {g: list(am.keys()) for g, am in CONF_DATA} == rgc.assets_dict()


@pytest.mark.parametrize(
    ["kwargs", "expected"],
    [({}, "\n".join("  " + "{}: {}".format(g, "; ".join(assets.keys()))
                    for g, assets in CONF_DATA)),
     ({"offset_text": ""},
      "\n".join("{}: {}".format(g, "; ".join(assets.keys()))
                for g, assets in CONF_DATA)),
     ({"asset_sep": ","},
      "\n".join("  " + "{}: {}".format(
          g, ",".join(assets.keys())) for g, assets in CONF_DATA)),
     ({"genome_assets_delim": " -- "},
      "\n".join("  " + "{} -- {}".format(
          g, "; ".join(assets.keys())) for g, assets in CONF_DATA))])
def test_assets_str(rgc, kwargs, expected):
    """ Verify text representation of the configuration instance's assets. """
    print("kwargs: {}".format(kwargs))
    assert expected == rgc.assets_str(**kwargs)


@pytest.mark.parametrize(["gname", "expected"], [
    ("hg38", [a for a, _ in HG38_DATA]),
    ("mm10", [a for a, _ in MM10_DATA]),
    ("rCRSd", [a for a, _ in MITO_DATA]),
    (None, {g: list(assets.keys()) for g, assets in CONF_DATA})
])
def test_list_assets_by_genome(rgc, gname, expected):
    """ Verify listing of asset name/key/type, possible for one/all genomes. """
    assert expected == rgc.list_assets_by_genome(gname)


@pytest.mark.parametrize(["asset", "expected"], [
    (None, {"bowtie2": BT2_EXP, "bowtie": BT1_EXP,
            "hisat2": HISAT2_EXP, "blacklist": BLACKLIST_EXP,
            "tss_annotation": TSS_EXP, "gtf": GTF_EXP}),
    ("bowtie2", BT2_EXP), ("bowtie", BT1_EXP), ("hisat2", HISAT2_EXP),
    ("gtf", GTF_EXP), ("tss_annotation", TSS_EXP)
])
def test_list_genomes_by_asset(rgc, asset, expected):
    """ Veerify listing of genomes by asset name/key/type. """
    assert expected == rgc.list_genomes_by_asset(asset)
