""" Tests for genome config format exception """

import pytest
from refgenconf import *
from refgenconf.const import CFG_ASSETS_KEY
from refgenconf.exceptions import DOC_URL
from tests.conftest import bind_to_assets
from ubiquerg import powerset

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


FIXED_KV_PAIRS = [
    (CFG_ASSET_SIZE_KEY, "1G"), (CFG_ARCHIVE_SIZE_KEY, "2G"),
    (CFG_CHECKSUM_KEY, "dummy-checksum")]


@pytest.fixture
def base_rgc_data(tmpdir):
    return {CFG_FOLDER_KEY: tmpdir.strpath, CFG_SERVER_KEY: DEFAULT_SERVER}


@pytest.fixture
def rgc(base_rgc_data):
    return RefGenConf(base_rgc_data)


@pytest.mark.parametrize(
    ["msg", "exp"], [(".", ". "), ("?", "? "), ("a", "a; ")])
@pytest.mark.parametrize(
    "check", [lambda m, e: m.startswith(e), lambda m, _: m.endswith(DOC_URL)])
def test_config_format_error_message_formatting(msg, exp, check):
    """ Check config format error message formatting and docs URL inclusion. """
    msg = str(GenomeConfigFormatError(msg))
    assert check(msg, exp)


@pytest.mark.parametrize("genome", ["dm3", "mm10", "hg38"])
@pytest.mark.parametrize("asset", ["bowtie2_index", "chrom_sizes", "epilog"])
@pytest.mark.parametrize(
    ["data", "message_content"],
    [("just_text_no_path", "has raw string value")] +
    [(dict(c),"lacks a '{}' entry".format(CFG_ASSET_PATH_KEY))
     for c in powerset(FIXED_KV_PAIRS, nonempty=True)])
@pytest.mark.parametrize("check_exist", [None, False, True])
def test_genome_config_format_raising_is_sensitive(
        rgc, genome, asset, data, message_content, check_exist):
    """ Check that config format error occurs in expected cases. """
    rgc[CFG_GENOMES_KEY][genome] = {CFG_ASSETS_KEY: {asset: data}}
    with pytest.raises(GenomeConfigFormatError) as err_ctx:
        rgc.get_asset(genome, asset, strict_exists=check_exist)
    assert message_content in str(err_ctx.value)
