""" Basic RGC asset tests """

from collections import OrderedDict
import pytest
__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"


class AssetDictTest:
    @pytest.mark.parametrize("gname", ["nonexistent", None])
    def test_with_nonexistent_genome(self, my_rgc, gname):
        """ Verify asset dict is always returned, even if the requested genome does not exist """
        assert isinstance(my_rgc.assets_dict(genome=gname), OrderedDict)

    @pytest.mark.parametrize("gname", ["nonexistent", None])
    def test_length(self, my_rgc, all_genomes, gname):
        """ Verify asset dict is larger if nonexistent or no genome specified than ones that are
        returned for a specific genome"""
        for g in all_genomes:
            assert len(my_rgc.assets_dict(genome=gname)) > len(my_rgc.assets_dict(genome=g))

    def test_multiple_genomes(self, my_rgc, all_genomes):
        """ Verify asset dict works with multiple genomes and returns all of them """
        assert my_rgc.assets_dict(genome=all_genomes).keys() == my_rgc.assets_dict().keys()


class ListAssetsByGenomeTest:
    def test_returns_entire_mapping_when_no_genonome_specified(self, my_rgc):
        assert my_rgc.list_assets_by_genome() == my_rgc.assets_dict()

    def test_returns_list(self, my_rgc, all_genomes):
        for g in all_genomes:
            assert isinstance(my_rgc.list_assets_by_genome(g), list)

    @pytest.mark.parametrize("gname", ["nonexistent", "genome"])
    def test_exception_on_nonexistent_genome(self, my_rgc, gname):
        with pytest.raises(KeyError):
            my_rgc.list_assets_by_genome(genome=gname)