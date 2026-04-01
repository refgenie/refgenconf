"""Test get_default_tag when default_tag key is missing from asset config."""

import os
import shutil

import pytest
import yaml

from refgenconf import RefGenConf


@pytest.fixture
def rgc_missing_default_tag(data_path, tmp_path):
    """RefGenConf with an asset that has tags but no default_tag key."""
    src = os.path.join(data_path, "genomes.yaml")
    dst = str(tmp_path / "genomes_no_default_tag.yaml")
    shutil.copy(src, dst)

    with open(dst) as f:
        cfg = yaml.safe_load(f)

    # Find first genome/asset and remove its default_tag key
    genomes = cfg["genomes"]
    genome_name = next(iter(genomes))
    asset_name = next(iter(genomes[genome_name]["assets"]))
    del genomes[genome_name]["assets"][asset_name]["default_tag"]

    with open(dst, "w") as f:
        yaml.dump(cfg, f)

    return RefGenConf.from_yaml_file(dst), genome_name, asset_name


def test_get_default_tag_without_default_tag_key(rgc_missing_default_tag):
    """Asset with tags but no default_tag key returns a tag name."""
    rgc, genome, asset = rgc_missing_default_tag
    with pytest.warns(RuntimeWarning):
        tag = rgc.get_default_tag(genome, asset, use_existing=True)
    assert isinstance(tag, str)
