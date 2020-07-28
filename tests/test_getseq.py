
""" Tests for RefGenConf.getseq. These tests depend on successful completion of tests is test_1pull_asset.py """

import pytest
from pyfaidx import FastaRecord, Sequence


class TestGetSeq:
    @pytest.mark.parametrize(["gname", "chr"], [("rCRSd", "rCRSd"), ("human_repeats", "U14567.1")])
    def test_qetseq_just_chr(self, ro_rgc, gname, chr):
        assert isinstance(ro_rgc.getseq(genome=gname, locus=chr), FastaRecord)

    @pytest.mark.parametrize(["gname", "chr"],
                             [("rCRSd", "rCRSd"), ("human_repeats", "U14567.1")])
    @pytest.mark.parametrize(["start", "end"],
                             [(1, 20), (2, 30), (1, 2), (2, 100)])
    def test_qetseq_interval(self, ro_rgc, gname, chr, start, end):
        seq = ro_rgc.getseq(genome=gname, locus="{}:{}-{}".format(chr, start, end))
        assert isinstance(seq, Sequence)
        assert len(seq) == end-start
