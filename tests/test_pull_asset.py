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
from tests.conftest import CONF_DATA, REMOTE_ASSETS, REQUESTS, \
    get_get_url
import refgenconf
from refgenconf.const import *
from refgenconf.exceptions import DownloadJsonError
from refgenconf.refgenconf import _download_url_progress

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


DOWNLOAD_FUNCTION = \
    "refgenconf.refgenconf.{}".format(_download_url_progress.__name__)


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
    if sys.version_info.major < 3:
        pytest.xfail("pull_asset download tests fail on py2")
    exp_file = os.path.join(rgc.genome_folder, genome, asset + exp_file_ext)
    assert not os.path.exists(exp_file)
    with mock.patch.object(
            refgenconf.refgenconf, "_download_json", lambda _: {
                CFG_ARCHIVE_SIZE_KEY: "0GB", CFG_ASSET_PATH_KEY: exp_file}), \
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
        return_value=YacAttMap({
            CFG_CHECKSUM_KEY: checksum_tmpval,
            CFG_ARCHIVE_SIZE_KEY: "0 GB",
            CFG_ASSET_PATH_KEY: "testpath"})), \
         mock.patch.object(refgenconf.refgenconf, "checksum",
                           return_value=checksum_tmpval), \
         mock.patch.object(refgenconf.refgenconf, "_download_url_progress",
                           return_value=None), \
         mock.patch.object(refgenconf.refgenconf, "_untar", return_value=None):
        rgc.pull_asset(genome, asset, gencfg,
                       get_main_url=get_get_url(genome, asset))
    new_data = YacAttMap(gencfg)
    new_assets = new_data.genomes[genome][CFG_ASSETS_KEY]
    assert asset in new_assets
    assert "testpath" == new_assets[asset].path


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
                CFG_ARCHIVE_SIZE_KEY: "0 GB",
                CFG_ASSET_PATH_KEY: "testpath"})), \
         mock.patch.object(refgenconf.refgenconf, "checksum",
                           return_value=checksum_tmpval), \
         mock.patch.object(refgenconf.refgenconf, "_download_url_progress"), \
         mock.patch.object(refgenconf.refgenconf, "_untar"):
        res = rgc.pull_asset(
            genome, asset, gencfg, get_main_url=get_get_url(genome, asset))
    key, val = _parse_single_pull(res)
    assert asset == key
    assert "testpath" == val


@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
@pytest.mark.parametrize(
    "error", [ConnectionRefusedError, HTTPError, DownloadJsonError])
def test_pull_asset_pull_error(
        rgc, genome, asset, gencfg, remove_genome_folder, error):
    """ Error pulling asset is exceptional. """
    args = (genome, asset, gencfg)
    kwargs = {"get_main_url": get_get_url(genome, asset)}
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
                return_value=YacAttMap({CFG_CHECKSUM_KEY: "not-a-checksum",
                                        CFG_ARCHIVE_SIZE_KEY: "0 GB"})), \
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
        rgc.pull_asset(genome, asset, gencfg,
                       get_main_url=get_get_url(genome, asset))


@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
def test_pull_asset_checksum_mismatch(
        rgc, genome, asset, gencfg, remove_genome_folder):
    """ Checksum mismatch short-circuits asset pull, returning null value. """
    with mock.patch.object(
        refgenconf.refgenconf, "_download_json",
        return_value=YacAttMap({CFG_CHECKSUM_KEY: "not-a-checksum",
                                CFG_ARCHIVE_SIZE_KEY: "0 GB"})), \
        mock.patch(DOWNLOAD_FUNCTION, side_effect=lambda _1, _2, _3: None), \
        mock.patch.object(
            refgenconf.refgenconf, "checksum", return_value="checksum2"):
        res = rgc.pull_asset(genome, asset, gencfg,
                             get_main_url=get_get_url(genome, asset))
    key, val = _parse_single_pull(res)
    assert asset == key
    assert val is None


@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
def test_negative_response_to_large_download_prompt(
        rgc, genome, asset, gencfg, remove_genome_folder):
    """ Test responsiveness to user abortion of pull request. """
    with mock.patch.object(
            refgenconf.refgenconf, "_download_json",
            return_value=YacAttMap({CFG_CHECKSUM_KEY: "not-a-checksum",
                                    CFG_ARCHIVE_SIZE_KEY: "1M"})), \
        mock.patch("refgenconf.refgenconf._is_large_archive", return_value=True), \
        mock.patch("refgenconf.refgenconf.query_yes_no", return_value=False):
        res = rgc.pull_asset(
            genome, asset, gencfg, get_main_url=get_get_url(genome, asset))
    key, val = _parse_single_pull(res)
    assert asset == key
    assert val is None


@pytest.mark.parametrize(["genome", "asset"], REQUESTS)
def test_download_interruption(
        rgc, genome, asset, gencfg, remove_genome_folder, caplog):
    """ Download interruption provides appropriate warning message and halts. """
    import signal
    def kill_download(*args, **kwargs):
        os.kill(os.getpid(), signal.SIGINT)
    with mock.patch.object(refgenconf.refgenconf, "_download_json",
                           return_value=YacAttMap({
                               CFG_CHECKSUM_KEY: "dummy",
                               CFG_ARCHIVE_SIZE_KEY: "1M"})),\
         mock.patch(DOWNLOAD_FUNCTION, side_effect=kill_download), \
         caplog.at_level(logging.WARNING), \
         pytest.raises(SystemExit):
        rgc.pull_asset(genome, asset, gencfg, get_main_url=get_get_url(genome, asset))
    records = caplog.records
    assert 1 == len(records)
    r = records[0]
    assert "WARNING" == r.levelname
    assert "The download was interrupted" in r.msg


class PreexistingAssetTests:
    """ Tests for asset pull when the asset path already exists. """

    @staticmethod
    def _assert_result(res, exp_key, exp_val):
        """ Check the return key/value from the pull operation. """
        k, v = _parse_single_pull(res)
        assert exp_key == k
        assert exp_val == v

    @staticmethod
    def _assert_single_message(log, levname, test_text):
        """ Verify presence of a log message with expected level and content. """
        assert levname in dir(logging), "Not a logging level: {}".format(levname)
        msgs = [r.msg for r in log.records if r.levelname == levname]
        matched = list(filter(test_text, msgs))
        assert 1 == len(matched)

    def _assert_preserved(self, rgc, genome, asset, res, init_time, log):
        """ Verify behavior expected if asset was preserved. """
        exp_val = rgc.filepath(genome, asset)
        self._assert_result(res, asset, exp_val)
        assert init_time == os.path.getmtime(exp_val)
        self._assert_single_message(
            log, "DEBUG", lambda m: m == "Preserving existing: {}".format(exp_val))

    def _assert_overwritten(self, rgc, genome, asset, res, init_time, log):
        """ Verify behavior expected if asset was overwritten. """
        exp_val = rgc.filepath(genome, asset)
        self._assert_result(res, asset, exp_val)
        assert init_time < os.path.getmtime(exp_val)
        self._assert_single_message(
            log, "DEBUG", lambda m: m == "Overwriting: {}".format(exp_val))

    @pytest.mark.parametrize(["genome", "asset"], REQUESTS)
    @pytest.mark.parametrize(["force", "exp_overwrite", "reply_patch"], [
        (True, True, {"side_effect": lambda *args, **kwargs: pytest.fail(
            "Forced short-circuit failed")}),
        (None, True, {"return_value": True}),
        (False, False, {"side_effect": lambda *args, **kwargs: pytest.fail(
            "Forced short-circuit failed")}),
        (None, False, {"return_value": False})])
    def test_asset_already_exists(
            self, rgc, genome, asset, gencfg,
            force, exp_overwrite, reply_patch, caplog, remove_genome_folder):
        """ Overwrite may be prespecified or determined by response to prompt. """
        fp = rgc.filepath(genome, asset)
        assert not os.path.exists(fp)
        if not os.path.exists(os.path.dirname(fp)):
            os.makedirs(os.path.dirname(fp))
        with open(fp, 'w'):
            print("Create empty file: {}".format(fp))
        init_time = os.path.getmtime(fp)
        dummy_checksum_value = "fixed_value"
        def touch(*_args, **_kwargs):
            with open(fp, 'w'):
                print("Recreating: {}".format(fp))

        time.sleep(0.01)
        assert os.path.isfile(fp)
        with mock.patch.object(
                refgenconf.refgenconf, "_download_json", return_value=YacAttMap({
                    CFG_CHECKSUM_KEY: "fixed_value",
                    CFG_ARCHIVE_SIZE_KEY: "1M",
                    CFG_ASSET_PATH_KEY: fp
                })), \
             mock.patch.object(refgenconf.refgenconf, "query_yes_no", **reply_patch), \
             mock.patch(DOWNLOAD_FUNCTION, side_effect=touch), \
             mock.patch.object(refgenconf.refgenconf, "checksum",
                               return_value=dummy_checksum_value), \
             mock.patch.object(refgenconf.refgenconf, "_untar"), \
             caplog.at_level(logging.DEBUG):
            res = rgc.pull_asset(genome, asset, gencfg, force=force,
                                 get_main_url=get_get_url(genome, asset))
        assertion_arguments = (rgc, genome, asset, res, init_time, caplog)
        verify = self._assert_overwritten if exp_overwrite else self._assert_preserved
        verify(*assertion_arguments)


def _parse_single_pull(result):
    """ Unpack asset pull result, expecting asset name and value. """
    try:
        k, v = result[0]
    except (IndexError, ValueError):
        print("Single pull result should be a list with one pair; got {}".
              format(result))
        raise
    return k, v
