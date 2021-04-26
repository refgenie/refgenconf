""" Tests for RefGenConf.tag. These tests depend on successful completion of tests is test_1pull_asset.py """

import mock
import pytest


class TestTagging:
    @pytest.mark.parametrize(
        ["gname", "aname", "new_tname"],
        [
            ("rCRSd", "bowtie2_index", "newtag"),
            ("mouse_chrM2x", "bwa_index", "newtag"),
        ],
    )
    def test_tag_and_back(self, my_rgc, gname, aname, new_tname):
        """ The default asset is removed if specific not provided """
        tname = my_rgc.get_default_tag(gname, aname)
        with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
            my_rgc.tag(gname, aname, tname, new_tname)
        my_rgc.seek(gname, aname, new_tname)
        with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
            my_rgc.tag(gname, aname, new_tname, tname)
        my_rgc.seek(gname, aname, tname)
