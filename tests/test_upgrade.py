import os
import urllib.request

import mock
import pytest

from refgenconf import RefGenConf, upgrade_config
from refgenconf.const import *
from refgenconf.exceptions import *
from refgenconf.refgenconf import _download_url_progress
from refgenconf.refgenconf_v03 import _RefGenConfV03

__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"


DOWNLOAD_FUNCTION = f"refgenconf.refgenconf.{_download_url_progress.__name__}"


class TestUpgradeExceptions:
    def test_cfg_v03_errors_with_new_constructor(self, cfg_file_old):
        with pytest.raises(ConfigNotCompliantError):
            RefGenConf(filepath=cfg_file_old)

    @pytest.mark.parametrize("target_version", ["0.5", 0.1, "IDK", [1, 2, 3]])
    def test_unavailable_conversions(self, target_version, cfg_file_old):
        with pytest.raises(NotImplementedError):
            upgrade_config(filepath=cfg_file_old, target_version=target_version)


class TestUpgrade03to04:
    @pytest.mark.parametrize("genome", ["human_repeats", "rCRSd"])
    def test_get_old_data(self, cfg_file_old, genome):
        old_rgc = _RefGenConfV03(cfg_file_old)
        # get some old asset data on disk
        with mock.patch("refgenconf.refgenconf_v03.query_yes_no", return_value=True):
            print(f"\nPulling: {genome}/fasta:default\n")
            old_rgc.pull(genome=genome, asset="fasta", tag="default")

    def test_all_server_local_mix(self, cfg_file_old):
        """
        Test config upgrade from v0.3 to v0.4 when a mix of genomes in terms of
        remote digest availability is in defined the old config
        """
        old_rgc = _RefGenConfV03(cfg_file_old)
        # get some old asset data on disk
        g, a, t = "human_alu", "fasta", "default"
        try:
            pth = old_rgc.seek(g, "fasta", "default", strict_exists=True)
        except MissingGenomeError:
            src_url = f"http://big.databio.org/refgenie_raw/files.{g}.{a}.{a}"
            target_archive = f"/tmp/old/{g}.fa.gz"
            target_file = f"/tmp/old/{g}.fa"
            target_dir = f"/tmp/old/{g}/{a}/{t}"
            os.makedirs(target_dir, exist_ok=True)
            try:
                urllib.request.urlretrieve(src_url, target_archive)
            except Exception as e:
                import warnings

                warnings.warn(f"Could not download {src_url}, skipping test: {e}")
                return
            from subprocess import run

            run(
                f"gunzip {target_archive}; mv {target_file} {target_dir}",
                shell=True,
            )
            old_rgc.add(
                path=target_dir,
                genome=g,
                asset=a,
                tag="default",
                seek_keys={a: f"{g}.fa"},
                force=True,
            )
        else:
            print(f"{pth} exists")
        finally:
            upgrade_config(filepath=cfg_file_old, target_version="0.4", force=True)
        rgc = RefGenConf(cfg_file_old)
        assert rgc[CFG_VERSION_KEY] == REQ_CFG_VERSION
