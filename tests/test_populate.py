""" Tests for RefGenConf.populate. These tests depend on successful completion of tests is test_1pull_asset.py """

import pytest
import random
import string
from refgenconf.exceptions import MissingAssetError
from yacman.exceptions import UndefinedAliasError


def _generate_random_text_template(str_len):
    res = ""
    str_col = string.ascii_lowercase + string.ascii_uppercase
    r_bound = len(str_col) - 1
    for _ in range(0, str_len):
        res += str_col[random.randint(0, r_bound)]
    idx = random.randint(0, r_bound)
    res = res[:idx] + " {} " + res[idx:]
    print(f"test string for populate: {res}")
    return res


def _get_demo_dicts(genome, asset, str_len):
    demo = {
        "genome": _generate_random_text_template(str_len=str_len).format(
            f"refgenie://{genome}/{asset}"
        ),
        "other_attr": "something",
        "bt2": _generate_random_text_template(str_len=str_len).format(
            f"refgenie://{genome}/{asset}"
        ),
    }
    nested_demo = {
        "top_level_attr": "val",
        "other_top_attr": "don't do anything to this",
        "nested_dict": demo,
    }
    return demo, nested_demo


class TestPopulate:
    @pytest.mark.parametrize(
        ["gname", "aname"], [("rCRSd", "fasta"), ("human_repeats", "fasta")]
    )
    def test_populate_single_string(self, ro_rgc, gname, aname):
        assert ro_rgc.populate(f"refgenie://{gname}/{aname}") == ro_rgc.seek(
            genome_name=gname, asset_name=aname
        )

    @pytest.mark.parametrize(
        ["gname", "aname"], [("rCRSd", "fasta"), ("human_repeats", "fasta")]
    )
    @pytest.mark.parametrize("str_len", [50, 100])
    def test_populate_text(self, ro_rgc, gname, aname, str_len):
        assert ro_rgc.seek(genome_name=gname, asset_name=aname) in ro_rgc.populate(
            _generate_random_text_template(str_len).format(
                f"refgenie://{gname}/{aname}"
            )
        )

    @pytest.mark.parametrize(
        ["gname", "aname"], [("rCRSd", "fasta"), ("human_repeats", "fasta")]
    )
    @pytest.mark.parametrize("str_len", [50, 100])
    def test_populate_dicts(self, ro_rgc, gname, aname, str_len):
        demo, nested_demo = _get_demo_dicts(genome=gname, asset=aname, str_len=str_len)
        assert ro_rgc.seek(genome_name=gname, asset_name=aname) in str(
            ro_rgc.populate(demo)
        )
        assert ro_rgc.seek(genome_name=gname, asset_name=aname) in str(
            ro_rgc.populate(nested_demo)
        )

    @pytest.mark.parametrize(
        ["gname", "aname"], [("rCRSd", "fasta"), ("human_repeats", "fasta")]
    )
    @pytest.mark.parametrize("str_len", [50, 100])
    def test_populate_lists(self, ro_rgc, gname, aname, str_len):
        demo, nested_demo = _get_demo_dicts(genome=gname, asset=aname, str_len=str_len)
        demo_list = [demo, nested_demo]
        assert ro_rgc.seek(genome_name=gname, asset_name=aname) in str(
            ro_rgc.populate(demo_list)
        )

    @pytest.mark.parametrize("aname", ["asset", "test", "bogus"])
    @pytest.mark.parametrize("gname", ["human_repeats", "rCRSd"])
    def test_populate_recognizes_missing_asset(self, ro_rgc, gname, aname):
        with pytest.raises(MissingAssetError):
            ro_rgc.populate(f"refgenie://{gname}/{aname}")

    @pytest.mark.parametrize("aname", ["fasta", "bowtie2_index"])
    @pytest.mark.parametrize("gname", ["asset", "test", "bogus"])
    def test_populate_recognizes_missing_genome(self, ro_rgc, gname, aname):
        with pytest.raises(UndefinedAliasError):
            ro_rgc.populate(f"refgenie://{gname}/{aname}")
