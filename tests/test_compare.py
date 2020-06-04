""" Tests for RefGenConf.compare. These tests depend on successful completion of tests is test_1pull_asset.py """

import pytest
import os

__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"


class TestCompare:
    @pytest.mark.parametrize(["gname1", "gname2", "result"],
                             [("rCRSd", "rCRSd", 63),
                              ("mouse_chrM2x", "mouse_chrM2x", 63),
                              ("rCRSd", "mouse_chrM2x", 0)])
    def test_compare_result(self, ro_rgc, gname1, gname2, result):
        assert ro_rgc.compare(gname1, gname2) == result

    @pytest.mark.parametrize(["gname1", "gname2"],
                             [("rCRSd", "rCRSd"),
                              ("mouse_chrM2x", "mouse_chrM2x"),
                              ("rCRSd", "mouse_chrM2x")])
    def test_compare_errors_when_no_asd_json(self, ro_rgc, gname1, gname2):
        jfp = ro_rgc.get_asds_path(gname1)
        os.rename(jfp, jfp + "_renamed")
        with pytest.raises(OSError):
            ro_rgc.compare(gname1, gname2)
        os.rename(jfp + "_renamed", jfp)
