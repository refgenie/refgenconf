""" Test suite shared objects and setup """

import os
import random
import shutil
import string
import pytest
import yaml
from attmap import PathExAttMap
from refgenconf import __version__ as package_version
from refgenconf import RefGenConf
from refgenconf.const import *

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


IDX_BT2_VAL = "indexed_bowtie2"
HG38_DATA = [
    ("bowtie2", IDX_BT2_VAL), ("hisat2", "indexed_hisat2"),
    ("tss_annotation", "TSS.bed.gz"), ("gtf", "blah.gtf")]

HG38_DATA = [
    ("bowtie2", IDX_BT2_VAL), ("hisat2", "indexed_hisat2"),
    ("tss_annotation", "TSS.bed.gz"), ("gtf", "blah.gtf")]



MM10_DATA = [("bowtie2", IDX_BT2_VAL), ("blacklist", "blacklist/mm10.bed")]
MITO_DATA = [("bowtie2", IDX_BT2_VAL), ("bowtie", "indexed_bowtie")]


REMOTE_ASSETS = {
    "rCRSd": {"bowtie2": ".tgz", "fasta": ".tgz"},
    "mouse_chrM2": {"bowtie2": ".tgz", "fasta": ".tgz"}}
REQUESTS = [(g, a, "default") for g, ext_by_asset in REMOTE_ASSETS.items() for a in ext_by_asset]
URL_BASE = "https://raw.githubusercontent.com/databio/refgenieserver/master/files"


def _bind_to_path(kvs):
    return [(k, lift_into_path_pair(v)) for k, v in kvs]


def lift_into_path_pair(name):
    return {"path": name}


CONF_DATA = [
    (g, {CFG_ASSETS_KEY: PathExAttMap(_bind_to_path(data))}) for g, data
    in [("hg38", HG38_DATA), ("mm10", MM10_DATA), ("rCRSd", MITO_DATA)]
]


def bind_to_assets(data):
    return {CFG_ASSETS_KEY: data}


def get_conf_genomes():
    """
    Get the collection of reference genome assembly names used in test data.

    :return list[str]: collection of test data reference genome assembly names
    """
    return list(list(zip(*CONF_DATA))[0])


@pytest.fixture
def data_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@pytest.fixture
def cfg_file(data_path):
    return os.path.join(data_path, "genomes.yaml")


@pytest.fixture
def cfg_file_old(data_path):
    return os.path.join(data_path, "genomes_v2.yaml")


@pytest.fixture
def cfg_file_copy(cfg_file, tmpdir_factory):
    """ Provide test case with copied version of test session's genome config. """
    fn = "".join(random.choice(string.ascii_letters) for _ in range(15)) + ".yaml"
    fp = os.path.join(tmpdir_factory.mktemp("test").strpath, fn)
    assert not os.path.exists(fp)
    shutil.copy(cfg_file, fp)
    assert os.path.isfile(fp)
    return fp


@pytest.fixture
def gencfg(temp_genome_config_file):
    """ Provide test case with copied version of test session's genome config. """
    fn = "".join(random.choice(string.ascii_letters) for _ in range(15)) + ".yaml"
    fp = os.path.join(os.path.dirname(temp_genome_config_file), fn)
    assert not os.path.exists(fp)
    shutil.copy(temp_genome_config_file, fp)
    assert os.path.isfile(fp)
    return fp


def get_get_url(genome, asset, base=URL_BASE):
    """
    Create 3-arg function that determines URL from genome and asset names.

    :param str genome: the reference genome assembly ID, e.g. mm10
    :param str asset: the name of the asset to use in the URL, e.g. bowtie2
    :param str base: the base of the URL to create
    :return function(object, str, str): function with which to build URL
        based on reference genome assembly ID, asset name, and one unused
        positional argument
    """
    return (lambda _, v, g, a: "{base}/{g}/{fn}".format(base=base, v=API_VERSION, g=genome, fn=a + REMOTE_ASSETS[g][asset]))


@pytest.fixture(scope="session")
def made_genome_config_file(temp_genome_config_file):
    """ Make the test session's genome config file. """
    genome_folder = os.path.dirname(temp_genome_config_file)
    extra_kv_lines = ["{}: {}".format(CFG_FOLDER_KEY, genome_folder),
                      "{}: {}".format(CFG_SERVER_KEY, DEFAULT_SERVER),
                      "{}: {}".format(CFG_VERSION_KEY, package_version),
                      "{}:".format(CFG_GENOMES_KEY)]
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


@pytest.fixture
def my_rgc(cfg_file):
    return RefGenConf(cfg_file)


@pytest.fixture
def all_genomes(my_rgc):
    return my_rgc[CFG_GENOMES_KEY].keys()


@pytest.fixture
def remove_genome_folder(request):
    """ Remove a test case's folder for a particular genome. """
    folder = request.getfixturevalue("rgc").genome_folder
    genome = request.getfixturevalue("genome")
    path = os.path.join(folder, genome)
    yield
    if os.path.exists(path):
        shutil.rmtree(path)


@pytest.fixture(scope="session")
def temp_genome_config_file(tmpdir_factory):
    """ The genome configuration file for the test suite. """
    return tmpdir_factory.mktemp("data").join("refgenie.yaml").strpath
