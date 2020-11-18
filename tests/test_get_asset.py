
""" Tests for RefGenConf.get_asset. These tests depend on successful completion of tests is test_1pull_asset.py """

import os
import pytest
from refgenconf.exceptions import *
from yacman.exceptions import UndefinedAliasError
from refgenconf.const import *
from tests.conftest import CONF_DATA
from shutil import rmtree


class TestGetAsset:
    @pytest.mark.parametrize(["gname", "aname", "tname", "seek_key"],
                             [("rCRSd", "fasta", "default", "fasta"), ("rCRSd", "fasta", "default", None)])
    def test_result(self, ro_rgc, gname, aname, tname, seek_key):
        assert isinstance(ro_rgc.seek(gname, aname, tname, seek_key), str)

    @pytest.mark.parametrize(["gname", "aname", "tname", "seek_key", "etype"],
                             [("rCRSd", "missing", "default", None, MissingAssetError),
                              ("missing", "bowtie2_index", "default", None, UndefinedAliasError),
                              ("rCRSd", "bowtie2_index", "missing", None, MissingTagError),
                              ("rCRSd", "bowtie2_index", "default", "missing", MissingSeekKeyError)])
    def test_all_exceptions(self, ro_rgc, gname, aname, tname, seek_key, etype):
        with pytest.raises(etype):
            ro_rgc.seek(gname, aname, tname, seek_key)

    @pytest.mark.parametrize("check_exist", [lambda: True, lambda _1, _2: True])
    @pytest.mark.parametrize("gname,aname", [("human_repeats", "fasta")])
    def test_check_exist_param_type(self, ro_rgc, check_exist, gname, aname):
        """ The asset existence check must be a one-arg function. """
        with pytest.raises(TypeError):
            ro_rgc.seek(gname, aname, check_exist=check_exist)

    @pytest.mark.parametrize(
        ["gname", "aname", "tname"], [("rCRSd", "fasta", "default"), ("mouse_chrM2x", "fasta", "default")])
    def test_result_correctness(self, ro_rgc, gname, aname, tname):
        """ The FASTA file asset is returned  when fasta asset is requested, not the entire dir """
        assert os.path.join(ro_rgc[CFG_FOLDER_KEY], gname, aname, tname) != ro_rgc.seek(gname, aname, tname)