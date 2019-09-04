""" Tests for asset pull """

import logging
import mock
import os
import sys
import time
if sys.version_info.major < 3:
    from urllib2 import HTTPError
    ConnectionRefusedError = Exception
else:
    from urllib.error import HTTPError
import pytest
from yacman import YacAttMap
from tests.conftest import REMOTE_ASSETS, REQUESTS, \
    get_get_url
import refgenconf
from refgenconf.const import *
from refgenconf.exceptions import *
from refgenconf.refgenconf import _download_url_progress

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


DOWNLOAD_FUNCTION = "refgenconf.refgenconf.{}".format(_download_url_progress.__name__)


@pytest.mark.parametrize(
    ["genome", "asset", "tag"], [("rCRSd", "fasta", "default"), ("rCRSd", "fasta", "default")])
def test_no_unpack(rgc, genome, asset, tag, temp_genome_config_file):
    """ Tarballs must be unpacked. """
    with pytest.raises(NotImplementedError):
        rgc.pull_asset(genome, asset, tag, temp_genome_config_file, unpack=False)


@pytest.mark.parametrize(["gname", "aname", "tname"], [("rCRSd", "fasta", "test"), ("rCRSd", "fasta", "default"), ("mouse_chrM2", "fasta", "default")])
def test_pull_asset(my_rgc, cfg_file, gname, aname, tname):
    with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
        print("\nPulling; genome: {}, asset: {}, tag: {}\n".format(gname, aname, tname))
        my_rgc.pull_asset(gname, aname, tname, cfg_file)
        print(my_rgc)
        my_rgc.remove_assets(gname, aname, tname)
        print(my_rgc)


@pytest.mark.parametrize(["gname", "aname", "tname"], [("rCRSd", "fasta", "default")])
def test_pull_asset_updates_genome_config(my_rgc, cfg_file, gname, aname, tname):
    args = [gname, aname, tname]
    my_rgc.remove_assets(*args)
    print(my_rgc)
    with pytest.raises(RefgenconfError):
        my_rgc.get_asset(*args)
    with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
        my_rgc.pull_asset(*args, cfg_file)
    my_rgc.get_asset(*args)


@pytest.mark.remote_data
@pytest.mark.parametrize(["genome", "asset", "tag"], REQUESTS)
def test_pull_asset_returns_key_value_pair(
        rgc, genome, asset, tag, gencfg, remove_genome_folder):
    """ Verify asset pull returns asset name, and value if pulled. """
    checksum_tmpval = "not-a-checksum"
    with mock.patch.object(
            refgenconf.refgenconf, "_download_json",
            return_value=YacAttMap({
                CFG_ARCHIVE_CHECKSUM_KEY: checksum_tmpval,
                CFG_ARCHIVE_SIZE_KEY: "0 GB",
                CFG_ASSET_PATH_KEY: "testpath",
                CFG_ASSET_PARENTS_KEY: []})), \
         mock.patch.object(refgenconf.refgenconf, "checksum",
                           return_value=checksum_tmpval), \
         mock.patch.object(refgenconf.refgenconf, "_download_url_progress"), \
         mock.patch.object(refgenconf.refgenconf, "_untar"):
        res = rgc.pull_asset(genome, asset, tag, gencfg, get_json_url=get_get_url(genome, asset))
    key, val = _parse_single_pull(res)
    assert asset == key
    assert "testpath" == val


@pytest.mark.parametrize(["genome", "asset", "tag"], REQUESTS)
@pytest.mark.parametrize("error", [ConnectionRefusedError, HTTPError, DownloadJsonError])
def test_pull_asset_pull_error(rgc, genome, asset, tag, gencfg, remove_genome_folder, error):
    """ Error pulling asset is exceptional. """
    args = (genome, asset, tag, gencfg)
    kwargs = {"get_json_url": get_get_url(genome, asset)}
    if error is DownloadJsonError:
        def raise_error(*args, **kwargs):
            raise DownloadJsonError(None)
        with mock.patch("refgenconf.refgenconf._download_json",
                        side_effect=raise_error), \
             pytest.raises(DownloadJsonError):
            rgc.pull_asset(*args, **kwargs)
    else:
        class SubErr(error):
            def __init__(self):
                pass

            def __str__(self):
                return self.__class__.__name__

        def raise_error(*args, **kwargs):
            raise SubErr()
        with mock.patch.object(
                refgenconf.refgenconf, "_download_json",
                return_value=YacAttMap({CFG_ARCHIVE_CHECKSUM_KEY: "not-a-checksum",
                                        CFG_ARCHIVE_SIZE_KEY: "0 GB",
                                        CFG_ASSET_PARENTS_KEY: []})), \
             mock.patch(DOWNLOAD_FUNCTION, side_effect=raise_error):
            res = rgc.pull_asset(*args, **kwargs)
            key, val = _parse_single_pull(res)
            assert asset == key
            assert val is None


@pytest.mark.parametrize(["genome", "asset"], [
    (g, a) for g in REMOTE_ASSETS for a in [None, 1, -0.1]])
def test_pull_asset_illegal_asset_name(
        rgc, genome, asset, gencfg, remove_genome_folder):
    """ TypeError occurs if asset argument is not iterable. """
    with pytest.raises(TypeError):
        rgc.pull_asset(genome, asset, gencfg, get_json_url=get_get_url(genome, asset))


@pytest.mark.parametrize(["genome", "asset", "tag"], REQUESTS)
def test_negative_response_to_large_download_prompt(
        rgc, genome, asset, tag, gencfg, remove_genome_folder):
    """ Test responsiveness to user abortion of pull request. """
    with mock.patch.object(
            refgenconf.refgenconf, "_download_json",
            return_value=YacAttMap({CFG_ARCHIVE_CHECKSUM_KEY: "not-a-checksum",
                                    CFG_ARCHIVE_SIZE_KEY: "1M",
                                    CFG_ASSET_PARENTS_KEY: []})), \
        mock.patch("refgenconf.refgenconf._is_large_archive", return_value=True), \
        mock.patch("refgenconf.refgenconf.query_yes_no", return_value=False):
        res = rgc.pull_asset(
            genome, asset, tag, gencfg, get_json_url=get_get_url(genome, asset))
    key, val = _parse_single_pull(res)
    assert asset == key
    assert val is None


@pytest.mark.parametrize(["genome", "asset", "tag"], REQUESTS)
def test_download_interruption(
        rgc, genome, asset, tag, gencfg, remove_genome_folder, caplog):
    """ Download interruption provides appropriate warning message and halts. """
    import signal
    def kill_download(*args, **kwargs):
        os.kill(os.getpid(), signal.SIGINT)
    with mock.patch.object(refgenconf.refgenconf, "_download_json",
                           return_value=YacAttMap({
                               CFG_ARCHIVE_CHECKSUM_KEY: "dummy",
                               CFG_ARCHIVE_SIZE_KEY: "1M",
                               CFG_ASSET_PARENTS_KEY: []})),\
         mock.patch(DOWNLOAD_FUNCTION, side_effect=kill_download), \
         caplog.at_level(logging.WARNING), \
         pytest.raises(SystemExit):
        rgc.pull_asset(genome, asset, tag, gencfg, get_json_url=get_get_url(genome, asset))
    records = caplog.records
    assert 1 == len(records)
    r = records[0]
    assert "WARNING" == r.levelname
    assert "The download was interrupted" in r.msg

def _parse_single_pull(result):
    """ Unpack asset pull result, expecting asset name and value. """
    try:
        k, v = result
    except (IndexError, ValueError):
        print("Single pull result should be a list with one pair; got {}".
              format(result))
        raise
    return k, v
