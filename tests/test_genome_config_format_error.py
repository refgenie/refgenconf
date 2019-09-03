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
    (CFG_ARCHIVE_CHECKSUM_KEY, "dummy-checksum")]


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

