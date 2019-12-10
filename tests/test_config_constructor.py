""" Tests for basic functionality of the RefGenConf constructor """

import os
import pytest
from attmap import PathExAttMap
from refgenconf import RefGenConf, ConfigNotCompliantError
from refgenconf.const import CFG_FOLDER_KEY, CFG_GENOMES_KEY, CFG_SERVERS_KEY, \
    DEFAULT_SERVER, RGC_REQ_KEYS

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

    def test_genome_folder_is_value_from_config_file_if_key_present(self, tmpdir_factory, tmpdir, made_genome_config_file):
        conf_file = tmpdir_factory.mktemp("data2").join("refgenie.yaml").strpath
        expected = tmpdir.strpath
        with open(made_genome_config_file, 'r') as fin, open(conf_file, 'w') as fout:
            found = False
            for l in fin:
                if l.startswith(CFG_FOLDER_KEY):
                    fout.write("{}: {}\n".format(CFG_FOLDER_KEY, expected))
                else:
                    fout.write(l)
                    if l.startswith(CFG_SERVERS_KEY):
                        found = True
            if not found:
                fout.write("{}: {}".format(CFG_SERVERS_KEY, DEFAULT_SERVER))
        rgc = RefGenConf(filepath=conf_file)
        assert expected != os.path.dirname(conf_file)
        assert expected == rgc[CFG_FOLDER_KEY]

    @pytest.mark.parametrize("genomes", [None, "genomes", 10] + [dt(["mm10", "hg38"]) for dt in [list, set, tuple]])
    def test_illegal_genomes_mapping_type_gets_converted_to_empty_mapping(self, genomes, tmpdir):
        rgc = RefGenConf(entries={
            CFG_FOLDER_KEY: tmpdir.strpath,
            CFG_GENOMES_KEY: genomes,
            CFG_SERVERS_KEY: DEFAULT_SERVER
        })
        res = rgc[CFG_GENOMES_KEY]
        assert isinstance(res, PathExAttMap)
        assert 0 == len(res)

    def test_errors_on_old_cfg(self, cfg_file_old):
        with pytest.raises(ConfigNotCompliantError):
            RefGenConf(filepath=cfg_file_old)
