""" Tests for basic functionality of the RefGenConf constructor """

import os
import pytest
from attmap import PathExAttMap
from yacman import AliasedYacAttMap
from refgenconf import RefGenConf, ConfigNotCompliantError
from refgenconf.const import (
    CFG_FOLDER_KEY,
    CFG_GENOMES_KEY,
    CFG_SERVERS_KEY,
    DEFAULT_SERVER,
    RGC_REQ_KEYS,
)

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


class TestRefGenConf:
    def test_reads_file(self, cfg_file):
        assert isinstance(RefGenConf(cfg_file), RefGenConf)

    def test_creation_of_empty_object_sets_req_attrs(self):
        assert all([k in RefGenConf() for k in RGC_REQ_KEYS])

    def test_genome_folder_is_pwd_if_no_folder_key_and_raw_entries_passed(self, ro_rgc):
        data = PathExAttMap({k: v for k, v in ro_rgc.items() if k != CFG_FOLDER_KEY})
        new_rgc = RefGenConf(entries=data)
        assert os.getcwd() == new_rgc[CFG_FOLDER_KEY]

    @pytest.mark.parametrize(
        "genomes",
        [None, "genomes", 10] + [dt(["mm10", "hg38"]) for dt in [list, set, tuple]],
    )
    def test_illegal_genomes_mapping_type_gets_converted_to_empty_mapping(
        self, genomes, tmpdir
    ):
        rgc = RefGenConf(
            entries={
                CFG_FOLDER_KEY: tmpdir.strpath,
                CFG_GENOMES_KEY: genomes,
                CFG_SERVERS_KEY: DEFAULT_SERVER,
            }
        )
        res = rgc[CFG_GENOMES_KEY]
        assert isinstance(res, AliasedYacAttMap)
        assert 0 == len(res)

    def test_errors_on_old_cfg(self, cfg_file_old):
        with pytest.raises(ConfigNotCompliantError):
            RefGenConf(filepath=cfg_file_old)
