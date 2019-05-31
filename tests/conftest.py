""" Test suite shared objects and setup """

import os
import pytest
import yaml
from attmap import PathExAttMap
from refgenconf import RefGenConf

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"



HG38_DATA = [
    ("bowtie2", "indexed_bowtie2"), ("hisat2", "indexed_hisat2"),
    ("tss_annotation", "TSS.bed.gz"), ("gtf", "blah.gtf")]
MM10_DATA = [("bowtie2", "indexed_bowtie2"), ("blacklist", "blacklist/mm10.bed")]
MITO_DATA = [("bowtie2", "indexed_bowtie2"), ("bowtie", "indexed_bowtie")]


def _bind_to_path(kvs):
    return [(k, lift_into_path_pair(v)) for k, v in kvs]


def lift_into_path_pair(name):
    return {"path": name}


CONF_DATA = [(g, PathExAttMap(_bind_to_path(data))) for g, data in
             [("hg38", HG38_DATA), ("mm10", MM10_DATA), ("rCRSd", MITO_DATA)]]


def get_conf_genomes():
    """
    Get the collection of reference genome assembly names used in test data.

    :return list[str]: collection of test data reference genome assembly names
    """
    return list(list(zip(*CONF_DATA))[0])


@pytest.fixture(scope="session")
def temp_genome_config_file(tmpdir_factory):
    """ The genome configuration file for the test suite. """
    return tmpdir_factory.mktemp("data").join("refgenie.yaml").strpath


@pytest.fixture(scope="session")
def made_genome_config_file(temp_genome_config_file):
    """ Make the test session's genome config file. """
    genome_folder = os.path.dirname(temp_genome_config_file)
    extra_kv_lines = ["genome_folder: {}".format(genome_folder),
                      "genome_server: http://localhost",
                      "genomes:"]
    gen_data_lines = PathExAttMap(CONF_DATA).get_yaml_lines()
    fp = temp_genome_config_file
    with open(fp, 'w') as f:
        f.write("\n".join(extra_kv_lines + ["  " + l for l in gen_data_lines]))
    return fp


@pytest.fixture
def rgc(made_genome_config_file):
    """ Provide test case with a genome config instance. """
    with open(made_genome_config_file, 'r') as f:
        return RefGenConf(yaml.load(f, yaml.SafeLoader))
