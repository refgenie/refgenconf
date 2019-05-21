""" Test suite shared objects and setup """

import os
import pytest
import yaml
from refgenconf import RefGenomeConfiguration

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


@pytest.fixture
def rgc():
    """ Provide test case with the RGC parsed from the repo root's config. """
    repo_root = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(repo_root, "refgenie.yaml"), 'r') as f:
        return RefGenomeConfiguration(yaml.load(f, yaml.SafeLoader))
