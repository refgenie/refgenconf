"""Tests for asset pull"""

import logging
import os
import sys

import mock

if sys.version_info.major < 3:
    ConnectionRefusedError = Exception
else:
    pass

import pytest

from refgenconf import RefGenConf
from refgenconf.const import *
from refgenconf.exceptions import *
from refgenconf.refgenconf import _download_url_progress

from .conftest import remove_asset_and_file

__author__ = "Vince Reuter, Michal Stolarczyk"
__email__ = "vreuter@virginia.edu"


DOWNLOAD_FUNCTION = "refgenconf.refgenconf.{}".format(_download_url_progress.__name__)


@pytest.mark.parametrize(
    ["gname", "aname"], [("human_repeats", 1), ("mouse_chrM2x", None)]
)
def test_pull_asset_illegal_asset_name(my_rgc, gname, aname):
    """TypeError occurs if asset argument is not iterable."""
    with pytest.raises(TypeError):
        my_rgc.pull(gname, aname)


@pytest.mark.parametrize(
    ["gname", "aname", "tname"],
    [
        ("human_repeats", "bwa_index", "default"),
        ("mouse_chrM2x", "bwa_index", "default"),
    ],
)
def test_download_interruption(my_rgc, gname, aname, tname, caplog):
    """Download interruption provides appropriate warning message and halts."""
    import signal

    print("filepath: " + my_rgc.__internal.file_path)

    def kill_download(*args, **kwargs):
        os.kill(os.getpid(), signal.SIGINT)

    with (
        mock.patch(DOWNLOAD_FUNCTION, side_effect=kill_download),
        mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True),
        caplog.at_level(logging.WARNING),
        pytest.raises(SystemExit),
    ):
        my_rgc.pull(gname, aname, tname)
    records = caplog.records
    assert 1 == len(records)
    r = records[0]
    assert "WARNING" == r.levelname
    assert "The download was interrupted" in r.msg


@pytest.mark.parametrize(
    ["gname", "aname", "tname"],
    [("human_repeats", "fasta", "default"), ("mouse_chrM2x", "fasta", "default")],
)
def test_pull_asset(my_rgc, gname, aname, tname):
    with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
        print("\nPulling; genome: {}, asset: {}, tag: {}\n".format(gname, aname, tname))
        my_rgc.pull(gname, aname, tname)


@pytest.mark.parametrize(
    ["gname", "aname", "tname"],
    [("rCRSd", "bowtie2_index", "default"), ("mouse_chrM2x", "bwa_index", "default")],
)
def test_parent_asset_mismatch(my_rgc, gname, aname, tname):
    """Test that an exception is raised when remote and local parent checksums do not match on pull"""
    with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
        my_rgc.pull(gname, "fasta", tname)
    my_rgc.make_writable()
    my_rgc.write()
    ori = my_rgc[CFG_GENOMES_KEY][gname][CFG_ASSETS_KEY]["fasta"][CFG_ASSET_TAGS_KEY][
        tname
    ][CFG_ASSET_CHECKSUM_KEY]
    my_rgc[CFG_GENOMES_KEY][gname][CFG_ASSETS_KEY]["fasta"][CFG_ASSET_TAGS_KEY][tname][
        CFG_ASSET_CHECKSUM_KEY
    ] = "wrong"
    with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
        with pytest.raises(RemoteDigestMismatchError):
            my_rgc.pull(gname, aname, tname)
    with my_rgc as r:
        r[CFG_GENOMES_KEY][gname][CFG_ASSETS_KEY]["fasta"][CFG_ASSET_TAGS_KEY][tname][
            CFG_ASSET_CHECKSUM_KEY
        ] = ori
    my_rgc.make_readonly()


@pytest.mark.parametrize(
    ["gname", "aname", "tname"],
    [("rCRSd", "bowtie2_index", "default"), ("mouse_chrM2x", "bwa_index", "default")],
)
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
        rgc.pull(gname, aname, tname)
    assert not ori_rgc.to_dict() == rgc.to_dict()
    post_rgc = RefGenConf(filepath=cfg_file, writable=False)
    assert isinstance(post_rgc.seek(gname, aname, tname), str)


@pytest.mark.parametrize(
    ["gname", "aname", "tname", "state"],
    [
        ("rCRSd", "fasta", "default", True),
        ("human_repeats", "fasta", "default", True),
        ("mouse_chrM2x", "fasta", "default", False),
    ],
)
def test_pull_asset_works_with_nonwritable_and_writable_rgc(
    cfg_file, gname, aname, tname, state
):
    rgc = RefGenConf(filepath=cfg_file, writable=state)
    remove_asset_and_file(rgc, gname, aname, tname)
    print("\nPulling; genome: {}, asset: {}, tag: {}\n".format(gname, aname, tname))
    with mock.patch("refgenconf.refgenconf.query_yes_no", return_value=True):
        rgc.pull(gname, aname, tname)
    if state:
        rgc.make_readonly()
