""" Tests for asset pull """

import os
import random
import shutil
import string
import pytest
from tests.conftest import CONF_DATA


URL_BASE = "https://raw.githubusercontent.com/databio/refgenieserver/master/files"
REMOTE_ASSETS = {
    "mm10": {"bowtie2": ".tar", "kallisto": ".tar"},
    "hg38": {"bowtie2": ".tar", "epilog": ".tgz", "kallisto": ".tar"}}
REQUESTS = [(g, a) for g, ext_by_asset in REMOTE_ASSETS.items()
            for a in ext_by_asset]


@pytest.fixture
def remove_genome_folder(request):
    """ Remove a test case's folder for a particular genome. """
    folder = request.getfixturevalue("rgc").genome_folder
    genome = request.getfixturevalue("genome")
    path = os.path.join(folder, genome)
    yield
    shutil.rmtree(path)


@pytest.fixture
def gencfg(temp_genome_config_file):
    fn = "".join(random.choice(string.ascii_letters) for _ in range(15)) + ".yaml"
    fp = os.path.join(os.path.dirname(temp_genome_config_file), fn)
    assert not os.path.exists(fp)
    shutil.copy(temp_genome_config_file, fp)
    assert os.path.isfile(fp)
    return fp


def _build_url_fetch(genome, asset):
    return (lambda _, g, a: "{base}/{g}/{fn}".format(
        base=URL_BASE, g=genome, fn=a + REMOTE_ASSETS[g][asset]))


@pytest.mark.parametrize(
    ["genome", "asset"], [(g, a) for g, assets in CONF_DATA for a in assets])
def test_no_unpack(rgc, genome, asset, temp_genome_config_file):
    """ Tarballs must be unpacked. """
    with pytest.raises(NotImplementedError):
        rgc.pull_asset(genome, asset, temp_genome_config_file, unpack=False)


@pytest.mark.remote_data
@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
@pytest.mark.parametrize("exp_file_ext", [".tar", ".txt"])
def test_pull_asset_download(rgc, genome, asset, gencfg, exp_file_ext,
                             remove_genome_folder):
    exp_file = os.path.join(rgc.genome_folder, genome, asset + exp_file_ext)
    assert not os.path.exists(exp_file)
    rgc.pull_asset(genome, asset, gencfg, get_url=_build_url_fetch(genome, asset))
    assert os.path.isfile(exp_file)
    os.unlink(exp_file)


@pytest.mark.remote_data
@pytest.mark.skip("not implemented")
@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
def test_pull_asset_updates_genome_config(genome, asset):
    pass


@pytest.mark.remote_data
@pytest.mark.skip("not implemented")
@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
def test_pull_asset_updates_genome_config(genome, asset):
    pass
