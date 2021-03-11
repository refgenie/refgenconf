""" Tests for RefGenConf.remove assets """

import pytest
import mock
from refgenconf.exceptions import *
from refgenconf.const import *


class TestRemoveAssets:
    @pytest.mark.parametrize(
        ["gname", "aname", "tname"],
        [("rCRSd", "fasta", None), ("mouse_chrM2x", "fasta", None)],
    )
    def test_default_tag_removal(self, my_rgc, gname, aname, tname):
        """ The default asset is removed if specific not provided """
        with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
            my_rgc.pull(gname, aname, tname)
            my_rgc.remove(gname, aname, tname)
        with pytest.raises(MissingAssetError):
            my_rgc.seek(gname, aname, tname)

    @pytest.mark.parametrize(
        ["gname", "aname"], [("rCRSd", "fasta"), ("mouse_chrM2x", "fasta")]
    )
    def test_asset_removal_after_last_tag_removed(self, my_rgc, gname, aname):
        """ The asset is removed when last tag is removed """
        my_rgc.pull(gname, aname, "default")
        asset = my_rgc.genomes[gname].assets[aname]
        for t in asset[CFG_ASSET_TAGS_KEY]:
            with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
                my_rgc.remove(gname, aname, t)
        with pytest.raises(MissingAssetError):
            my_rgc.seek(gname, aname, t)
