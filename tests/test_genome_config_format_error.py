""" Tests for genome config format exception """

import pytest
from refgenconf import *
from refgenconf.exceptions import DOC_URL

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


@pytest.mark.parametrize(
    ["msg", "exp"], [(".", ". "), ("?", "? "), ("a", "a; ")])
@pytest.mark.parametrize(
    "check", [lambda m, e: m.startswith(e), lambda m, _: m.endswith(DOC_URL)])
def test_config_format_error_message_formatting(msg, exp, check):
    """ Check config format error message formatting and docs URL inclusion. """
    msg = str(GenomeConfigFormatError(msg))
    assert check(msg, exp)


@pytest.mark.skip("not implemented")
def test_genome_config_format_raising_is_sensitive():
    """ Check that config format error occurs in expected cases. """
    pass
