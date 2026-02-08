"""Validate what's available directly on the top-level import."""

from inspect import isclass, isfunction

import pytest

from refgenconf.exceptions import RefgenconfError

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


def _is_custom_error(obj):
    return isinstance(obj, type) and issubclass(obj, RefgenconfError)


@pytest.mark.parametrize(
    ["obj_name", "typecheck"],
    [
        ("RefGenConf", isclass),
        ("select_genome_config", isfunction),
        ("DownloadJsonError", _is_custom_error),
        ("GenomeConfigFormatError", _is_custom_error),
        ("MissingAssetError", _is_custom_error),
        ("MissingConfigDataError", _is_custom_error),
        ("MissingGenomeError", _is_custom_error),
        ("MissingSeekKeyError", _is_custom_error),
        ("MissingTagError", _is_custom_error),
        ("ConfigNotCompliantError", _is_custom_error),
        ("UnboundEnvironmentVariablesError", _is_custom_error),
    ],
)
def test_top_level_exports(obj_name, typecheck):
    """At package level, validate object availability and type."""
    import refgenconf

    try:
        obj = getattr(refgenconf, obj_name)
    except AttributeError:
        pytest.fail("Unavailable on {}: {}".format(refgenconf.__name__, obj_name))
    else:
        assert typecheck(obj)
