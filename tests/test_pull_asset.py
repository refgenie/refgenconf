""" Tests for asset pull """

import mock
import os
import random
import shutil
import string
from urllib.error import HTTPError
import pytest
from yacman import YacAttMap
from tests.conftest import CONF_DATA
from refgenconf.refgenconf import _download_url_to_file


DOWNLOAD_FUNCTION = "refgenconf.refgenconf.{}".format(_download_url_to_file.__name__)
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
    if os.path.exists(path):
        shutil.rmtree(path)


@pytest.fixture
def gencfg(temp_genome_config_file):
    """ Provide test case with copied version of test session's genome config. """
    fn = "".join(random.choice(string.ascii_letters) for _ in range(15)) + ".yaml"
    fp = os.path.join(os.path.dirname(temp_genome_config_file), fn)
    assert not os.path.exists(fp)
    shutil.copy(temp_genome_config_file, fp)
    assert os.path.isfile(fp)
    return fp


def _get_get_url(genome, asset):
    """ Create 3-arg function that determines URL from genome and asset names. """
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
    """ Verify download and unpacking of tarball asset. """
    exp_file = os.path.join(rgc.genome_folder, genome, asset + exp_file_ext)
    assert not os.path.exists(exp_file)
    rgc.pull_asset(genome, asset, gencfg, get_url=_get_get_url(genome, asset))
    assert os.path.isfile(exp_file)
    os.unlink(exp_file)


@pytest.mark.remote_data
@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
def test_pull_asset_updates_genome_config(
        rgc, genome, asset, gencfg, remove_genome_folder):
    """ Verify asset pull's side-effect of updating the genome config file. """
    try:
        del rgc.genomes[genome][asset]
    except KeyError:
        pass
    rgc.write(gencfg)
    old_data = YacAttMap(gencfg)
    assert asset not in old_data.genomes[genome]
    rgc.pull_asset(genome, asset, gencfg, get_url=_get_get_url(genome, asset))
    new_data = YacAttMap(gencfg)
    assert asset in new_data.genomes[genome]
    assert asset == new_data.genomes[genome][asset].path


@pytest.mark.remote_data
@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
def test_pull_asset_returns_key_value_pair(
        rgc, genome, asset, gencfg, remove_genome_folder):
    """ Verify asset pull returns asset name, and value if pulled. """
    res = rgc.pull_asset(genome, asset, gencfg, get_url=_get_get_url(genome, asset))
    key, val = _parse_single_pull(res)
    assert asset == key
    assert asset == val


@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
@pytest.mark.parametrize("error", [ConnectionRefusedError, HTTPError])
def test_pull_asset_pull_error(
        rgc, genome, asset, gencfg, remove_genome_folder, error):
    """ Error pulling asset raises no exception but returns null value. """
    class SubErr(error):
        def __init__(self):
            pass
        def __str__(self):
            return self.__class__.__name__
    def raise_error(*args, **kwargs):
        raise SubErr()
    with mock.patch(DOWNLOAD_FUNCTION, side_effect=raise_error):
        res = rgc.pull_asset(genome, asset, gencfg, get_url=_get_get_url(genome, asset))
    key, val = _parse_single_pull(res)
    assert asset == key
    assert val is None


@pytest.mark.parametrize(
    ["genome", "asset"], [(g, a) for g in REMOTE_ASSETS for a in [None, 1, -0.1]])
def test_pull_asset_illegal_asset_name(
        rgc, genome, asset, gencfg, remove_genome_folder):
    """ TypeError occurs if asset argument is not iterable. """
    with pytest.raises(TypeError):
        rgc.pull_asset(genome, asset, gencfg, get_url=_get_get_url(genome, asset))


def _parse_single_pull(result):
    try:
        k, v = result[0]
    except (IndexError, ValueError):
        print("Single pull result should be a list with one pair; got {}".
              format(result))
        raise
    return k, v
