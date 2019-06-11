""" Tests for asset pull """

import mock
import os
import sys
if sys.version_info >= (3, ):
    from urllib.error import HTTPError
else:
    from urllib2 import HTTPError
    ConnectionRefusedError = Exception
import pytest
from yacman import YacAttMap
from tests.conftest import CONF_DATA, IDX_BT2_VAL, REMOTE_ASSETS, REQUESTS, \
    get_get_url, lift_into_path_pair
import refgenconf
from refgenconf.refgenconf import _download_url_progress
from refgenconf.const import *

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


DOWNLOAD_FUNCTION = "refgenconf.refgenconf.{}".format(_download_url_progress.__name__)


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
    with mock.patch.object(
            refgenconf.refgenconf, "_download_json",
            lambda _: {CFG_ARCHIVE_SIZE_KEY: "0GB", CFG_ASSET_PATH_KEY: exp_file}), \
         mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
        rgc.pull_asset(genome, asset, gencfg,
                       get_main_url=get_get_url(genome, asset))
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
    checksum_tmpval = "not-a-checksum"
    with mock.patch.object(
        refgenconf.refgenconf, "_download_json",
        return_value=YacAttMap({CFG_CHECKSUM_KEY: checksum_tmpval,
                                CFG_ARCHIVE_SIZE_KEY: "0 GB", CFG_ASSET_PATH_KEY: "testpath"})), \
         mock.patch.object(refgenconf.refgenconf, "checksum",
                           return_value=checksum_tmpval):
        rgc.pull_asset(genome, asset, gencfg,
                       get_main_url=get_get_url(genome, asset))
    new_data = YacAttMap(gencfg)
    assert asset in new_data.genomes[genome]
    assert "testpath" == new_data.genomes[genome][asset].path


@pytest.mark.remote_data
@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
def test_pull_asset_returns_key_value_pair(
        rgc, genome, asset, gencfg, remove_genome_folder):
    """ Verify asset pull returns asset name, and value if pulled. """
    checksum_tmpval = "not-a-checksum"
    with mock.patch.object(
            refgenconf.refgenconf, "_download_json",
            return_value=YacAttMap({
                CFG_CHECKSUM_KEY: checksum_tmpval,
                CFG_ARCHIVE_SIZE_KEY: "0 GB", CFG_ASSET_PATH_KEY: "testpath"})), \
         mock.patch.object(refgenconf.refgenconf, "checksum",
                           return_value=checksum_tmpval):
        res = rgc.pull_asset(
            genome, asset, gencfg, get_main_url=get_get_url(genome, asset))
    key, val = _parse_single_pull(res)
    assert asset == key
    assert "testpath" == val


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
        res = rgc.pull_asset(genome, asset, gencfg, get_main_url=get_get_url(genome, asset))
    key, val = _parse_single_pull(res)
    assert asset == key
    assert val is None


@pytest.mark.parametrize(
    ["genome", "asset"], [(g, a) for g in REMOTE_ASSETS for a in [None, 1, -0.1]])
def test_pull_asset_illegal_asset_name(rgc, genome, asset, gencfg, remove_genome_folder):
    """ TypeError occurs if asset argument is not iterable. """
    with pytest.raises(TypeError):
        rgc.pull_asset(genome, asset, gencfg, get_main_url=get_get_url(genome, asset))


@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
def test_pull_asset_checksum_mismatch(rgc, genome, asset, gencfg, remove_genome_folder):
    """ Checksum mismatch short-circuits asset pull, returning null value. """
    with mock.patch.object(
        refgenconf.refgenconf, "_download_json",
        return_value=YacAttMap({CFG_CHECKSUM_KEY: "not-a-checksum",
                                CFG_ARCHIVE_SIZE_KEY: "0 GB"})), \
        mock.patch(DOWNLOAD_FUNCTION, side_effect=lambda _1, _2, _3: None), \
        mock.patch.object(refgenconf.refgenconf, "checksum", return_value="checksum2"):
        res = rgc.pull_asset(genome, asset, gencfg, get_main_url=get_get_url(genome, asset))
    key, val = _parse_single_pull(res)
    assert asset == key
    assert val is None


@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
def test_abort_pull_asset(rgc, genome, asset, gencfg, remove_genome_folder):
    """ Test responsiveness to user abortion of pull request. """
    with mock.patch.object(
            refgenconf.refgenconf, "_download_json",
            return_value=YacAttMap({CFG_CHECKSUM_KEY: "not-a-checksum",
                                    CFG_ARCHIVE_SIZE_KEY: "0 GB"})), \
        mock.patch("refgenconf.refgenconf._is_large_archive", return_value=True), \
        mock.patch("refgenconf.refgenconf.query_yes_no", return_value=False):
        res = rgc.pull_asset(genome, asset, gencfg, get_main_url=get_get_url(genome, asset))
    key, val = _parse_single_pull(res)
    assert asset == key
    assert val is None


def _parse_single_pull(result):
    try:
        k, v = result[0]
    except (IndexError, ValueError):
        print("Single pull result should be a list with one pair; got {}".
              format(result))
        raise
    return k, v
