""" Tests for asset pull """

import logging
import mock
import os
import sys
if sys.version_info.major < 3:
    ConnectionRefusedError = Exception
else:
    from urllib.error import HTTPError
import pytest
from refgenconf.const import *
from refgenconf.exceptions import *
from refgenconf.refgenconf import _download_url_progress
from refgenconf import RefGenConf

from .conftest import remove_asset_and_file

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


DOWNLOAD_FUNCTION = "refgenconf.refgenconf.{}".format(_download_url_progress.__name__)


@pytest.mark.parametrize(
    ["genome", "asset", "tag"], [("rCRSd", "fasta", "default"), ("rCRSd", "fasta", "default")])
def test_no_unpack(rgc, genome, asset, tag):
    """ Tarballs must be unpacked. """
    with pytest.raises(NotImplementedError):
        rgc.pull_asset(genome, asset, tag, unpack=False)


@pytest.mark.parametrize(["gname", "aname"], [("human_repeats", 1), ("mouse_chrM2x", None)])
def test_pull_asset_illegal_asset_name(rgc, gname, aname):
    """ TypeError occurs if asset argument is not iterable. """
    with pytest.raises(TypeError):
        rgc.pull_asset(gname, aname)

@pytest.mark.parametrize(["gname", "aname", "tname"],
                         [("human_repeats", "bowtie2_index", "default"), ("mouse_chrM2x", "bwa_index", "default")])
def test_negative_response_to_large_download_prompt(rgc, gname, aname, tname):
    """ Test responsiveness to user abortion of pull request. """
    with mock.patch("refgenconf.refgenconf._is_large_archive", return_value=True), \
         mock.patch("refgenconf.refgenconf.query_yes_no", return_value=False):
        gat, archive_dict, server_url = rgc.pull_asset(gname, aname, tname)
    assert gat == [gname, aname, tname]


@pytest.mark.parametrize(["gname", "aname", "tname"],
                         [("human_repeats", "bowtie2_index", "default"), ("mouse_chrM2x", "bwa_index", "default")])
def test_download_interruption(my_rgc, gname, aname, tname, caplog):
    """ Download interruption provides appropriate warning message and halts. """
    import signal
    print("filepath: " + my_rgc._file_path)

    def kill_download(*args, **kwargs):
        os.kill(os.getpid(), signal.SIGINT)

    with mock.patch(DOWNLOAD_FUNCTION, side_effect=kill_download), \
         mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True), \
         caplog.at_level(logging.WARNING), \
         pytest.raises(SystemExit):
        my_rgc.pull_asset(gname, aname, tname)
    records = caplog.records
    assert 1 == len(records)
    r = records[0]
    assert "WARNING" == r.levelname
    assert "The download was interrupted" in r.msg


@pytest.mark.parametrize(["gname", "aname", "tname"], [("human_repeats", "fasta", "default"), ("mouse_chrM2x", "fasta", "default")])
def test_pull_asset(my_rgc, gname, aname, tname):
    with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
        print("\nPulling; genome: {}, asset: {}, tag: {}\n".format(gname, aname, tname))
        my_rgc.pull_asset(gname, aname, tname)


@pytest.mark.parametrize(["gname", "aname", "tname"],
                         [("rCRSd", "bowtie2_index", "default"), ("mouse_chrM2x", "bwa_index", "default")])
def test_parent_asset_mismatch(my_rgc, gname, aname, tname):
    """ Test that an exception is raised when remote and local parent checksums do not match on pull"""
    with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
        my_rgc.pull_asset(gname, "fasta", tname)
    my_rgc.make_writable()
    my_rgc.write()
    my_rgc[CFG_GENOMES_KEY][gname][CFG_ASSETS_KEY]["fasta"][CFG_ASSET_TAGS_KEY][tname][CFG_ASSET_CHECKSUM_KEY] = "wrong"
    with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
        with pytest.raises(RemoteDigestMismatchError):
            my_rgc.pull_asset(gname, aname, tname)


@pytest.mark.parametrize(["gname", "aname", "tname"], [("rCRSd", "bowtie2_index", "default"),
                                                       ("mouse_chrM2x", "bwa_index", "default")])
def test_pull_asset_updates_genome_config(cfg_file, gname, aname, tname):
    """
    Test that the object that was identical prior to the asset pull differs afterwards
    and the pulled asset metadata has been written to the config file
    """
    ori_rgc = RefGenConf(filepath=cfg_file, writable=False)
    rgc = RefGenConf(filepath=cfg_file, writable=False)
    remove_asset_and_file(rgc, gname, aname, tname)
    remove_asset_and_file(ori_rgc, gname, aname, tname)
    # ori_rgc.remove_assets(gname, aname, tname)
    assert ori_rgc.to_dict() == rgc.to_dict()
    with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
        print("\nPulling; genome: {}, asset: {}, tag: {}\n".format(gname, aname, tname))
        rgc.pull_asset(gname, aname, tname)
    assert not ori_rgc.to_dict() == rgc.to_dict()
    post_rgc = RefGenConf(filepath=cfg_file)
    assert isinstance(post_rgc.get_asset(gname, aname, tname), str)


@pytest.mark.parametrize(["gname", "aname", "tname"], [("human_repeats", "fasta", "default"), ("mouse_chrM2x", "fasta", "default")])
def test_pull_asset_works_with_nonwritable_and_writable_rgc(cfg_file, gname, aname, tname):
    rgc_ro = RefGenConf(filepath=cfg_file, writable=False)
    rgc_rw = RefGenConf(filepath=cfg_file, writable=True)
    remove_asset_and_file(rgc_rw, gname, aname, tname)
    remove_asset_and_file(rgc_ro, gname, aname, tname)
    with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
        print("\nPulling; genome: {}, asset: {}, tag: {}\n".format(gname, aname, tname))
        rgc_rw.pull_asset(gname, aname, tname)
        rgc_ro.pull_asset(gname, aname, tname)
    assert rgc_rw.to_dict() == rgc_ro.to_dict()
