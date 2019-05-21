""" Test suite shared objects and setup """

import pytest
import yaml
from attmap import PathExAttMap
from refgenconf import RefGenomeConfiguration

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


HG38_DATA = [
    ("bowtie2", "indexed_bowtie2"), ("hisat2", "indexed_hisat2"),
    ("tss_annotation", "TSS.bed.gz"), ("gtf", "blah.gtf")]
MM10_DATA = [("bowtie2", "indexed_bowtie2"), ("blacklist", "blacklist/mm10.bed")]
MITO_DATA = [("bowtie2", "indexed_bowtie2"), ("bowtie", "indexed_bowtie")]

CONF_DATA = [
    ("hg38", PathExAttMap(HG38_DATA)),
    ("mm10", PathExAttMap(MM10_DATA)),
    ("rCRSd", PathExAttMap(MITO_DATA))]


def get_conf_genomes():
    """
    Get the collection of reference genome assembly names used in test data.

    :return list[str]: collection of test data reference genome assembly names
    """
    return list(list(zip(*CONF_DATA))[0])


@pytest.fixture(scope="session")
def rgc(tmpdir_factory):
    extra_kv_lines = ["genome_folder: $GENOMES",
                      "genome_server: http://localhost",
                      "genomes:"]
    gen_data_lines = PathExAttMap(CONF_DATA).get_yaml_lines()
    fp = tmpdir_factory.mktemp("data").join("refgenie.yaml").strpath
    with open(fp, 'w') as f:
        f.write("\n".join(extra_kv_lines + ["  " + l for l in gen_data_lines]))
    with open(fp, 'r') as f:
        return RefGenomeConfiguration(yaml.load(f, yaml.SafeLoader))
