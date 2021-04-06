""" RGC properties tests """

import os

import pytest

from refgenconf import RefGenConf

__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"


class PropertiesTests:
    def test_genome_aliases_returns_dict(self, ro_rgc):
        assert isinstance(ro_rgc.genome_aliases, dict)

    def test_genome_aliases_returns_dict_empty(self):
        assert isinstance(RefGenConf().genome_aliases, dict)

    def test_plugins_returns_dict_of_dicts(self, ro_rgc):
        assert all([isinstance(v, dict) for k, v in ro_rgc.plugins.items()])

    @pytest.mark.parametrize("prop_name", ["file_path", "data_dir", "alias_dir"])
    def test_path_props_return_existing_paths(self, ro_rgc, prop_name):
        prop = getattr(ro_rgc, prop_name)
        assert isinstance(prop, str)
        assert os.path.exists(prop)

    @staticmethod
    def test_file_path_returns_none_if_not_bound_to_file():
        assert RefGenConf().file_path is None
