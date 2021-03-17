""" Tests for RefGenConf.getseq. These tests depend on successful completion of tests is test_1pull_asset.py """

import pytest
from pyfaidx import FastaRecord, Sequence


class TestPopulate:
    @pytest.mark.parametrize(
        ["gname", "chr"], [("rCRSd", "rCRSd"), ("human_repeats", "U14567.1")]
    )
    def test_populate(self, ro_rgc, gname, chr):
        print(ro_rgc.populate("refgenie://rCRSd/fasta"))
