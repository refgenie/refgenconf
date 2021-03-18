""" Tests for RefGenConf.populate. These tests depend on successful completion of tests is test_1pull_asset.py """

import pytest


class TestPopulate:
    @pytest.mark.parametrize(
        ["gname", "aname"], [("rCRSd", "fasta"), ("human_repeats", "fasta")]
    )
    def test_populate(self, ro_rgc, gname, aname):
        assert ro_rgc.populate(f"refgenie://{gname}/{aname}") == ro_rgc.seek(
            genome_name=gname, asset_name=aname
        )
