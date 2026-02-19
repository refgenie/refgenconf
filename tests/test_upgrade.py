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
            RefGenConf.from_yaml_file(cfg_file_old)

    @pytest.mark.parametrize("target_version", ["0.5", 0.1, "IDK", [1, 2, 3]])
    def test_unavailable_conversions(self, target_version, cfg_file_old):
        with pytest.raises(NotImplementedError):
            upgrade_config(filepath=cfg_file_old, target_version=target_version)


class TestUpgrade03to04:
    @pytest.mark.parametrize("genome", ["human_repeats", "rCRSd"])
    def test_get_old_data(self, cfg_file_old, genome):
        old_rgc = _RefGenConfV03.from_yaml_file(cfg_file_old)
        # get some old asset data on disk
        with mock.patch("refgenconf.refgenconf_v03.query_yes_no", return_value=True):
            print(f"\nPulling: {genome}/fasta:default\n")
            old_rgc.pull(genome=genome, asset="fasta", tag="default")

    def test_all_server_local_mix(self, cfg_file_old, tmp_path):
        """Test config upgrade from v0.3 to v0.4 when a mix of genomes in terms of
        remote digest availability is defined in the old config."""
        import shutil
        import yaml

        # Copy config to tmp_path so we don't mutate the shared test fixture
        cfg_copy = tmp_path / "genomes_v3.yaml"
        shutil.copy(cfg_file_old, cfg_copy)
        genome_folder = tmp_path / "genomes"
        genome_folder.mkdir()
        # Update genome_folder in the copied config
        with open(cfg_copy) as f:
            cfg_data = yaml.safe_load(f)
        cfg_data["genome_folder"] = str(genome_folder)
        with open(cfg_copy, "w") as f:
            yaml.dump(cfg_data, f)

        old_rgc = _RefGenConfV03.from_yaml_file(str(cfg_copy))
        g, a, t = "human_alu", "fasta", "default"
        try:
            old_rgc.seek(g, "fasta", "default", strict_exists=True)
        except MissingGenomeError:
            src_url = f"http://big.databio.org/refgenie_raw/files.{g}.{a}.{a}"
            target_archive = str(genome_folder / f"{g}.fa.gz")
            target_file = str(genome_folder / f"{g}.fa")
            target_dir = str(genome_folder / g / a / t)
            os.makedirs(target_dir, exist_ok=True)
            try:
                urllib.request.urlretrieve(src_url, target_archive)
            except Exception as e:
                pytest.skip(f"Could not download {src_url}: {e}")
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
        upgrade_config(filepath=str(cfg_copy), target_version="0.4", force=True)
        rgc = RefGenConf.from_yaml_file(str(cfg_copy))
        assert rgc[CFG_VERSION_KEY] == REQ_CFG_VERSION

    def test_incomplete_asset_does_not_raise_missing_seek_key_error(self, tmp_path):
        """Test that incomplete assets (no seek_keys) don't crash the upgrade check.

        This reproduces GitHub issue #281 where upgrade fails with MissingSeekKeyError
        for incomplete assets that were downloaded from remote but never fully built.
        The fix catches MissingSeekKeyError alongside MissingAssetError during the
        digest availability checking phase of upgrade_config().
        """
        import yaml
        from refgenconf.refgenconf_v03 import _RefGenConfV03

        # Create a v0.3 config with an incomplete fasta asset (missing seek_keys)
        incomplete_config = {
            "config_version": 0.3,
            "genome_folder": str(tmp_path / "genomes"),
            "genome_servers": ["http://refgenomes.databio.org"],
            "genomes": {
                "test_incomplete_genome": {
                    "assets": {
                        "fasta": {
                            "tags": {
                                "default": {
                                    # Only asset_digest, no seek_keys - this is the incomplete state
                                    "asset_digest": "abc123incomplete",
                                    "asset_parents": [],
                                    "asset_path": "fasta",
                                }
                            },
                            "default_tag": "default",
                        }
                    },
                }
            },
        }

        cfg_path = tmp_path / "incomplete_config.yaml"
        (tmp_path / "genomes").mkdir()
        with open(cfg_path, "w") as f:
            yaml.dump(incomplete_config, f)

        # Load with v0.3 loader
        rgc = _RefGenConfV03.from_yaml_file(str(cfg_path))

        # Calling seek on an incomplete asset should raise MissingSeekKeyError
        with pytest.raises(MissingSeekKeyError):
            rgc.seek("test_incomplete_genome", "fasta", "default", "fasta")

        # But getting the default tag should work (this is called before seek in upgrade)
        tag = rgc.get_default_tag("test_incomplete_genome", "fasta")
        assert tag == "default"
