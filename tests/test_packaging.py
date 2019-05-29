""" Validate what's available directly on the top-level import. """

import pytest
from inspect import isclass
from refgenconf.exceptions import RefgenconfError

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


@pytest.mark.parametrize(
    ["obj_name", "typecheck"],
    [("RefGenConf", isclass),
     ("MissingAssetError", lambda obj: issubclass(obj, RefgenconfError)),
     ("MissingGenomeError", lambda obj: issubclass(obj, RefgenconfError))])
def test_top_level_exports(obj_name, typecheck):
    """ At package level, validate object availability and type. """
    import refgenconf
    try:
        obj = getattr(refgenconf, obj_name)
    except AttributeError:
        pytest.fail("Unavailable on {}: {}".format(refgenconf.__name__, obj_name))
    else:
        assert typecheck(obj)
