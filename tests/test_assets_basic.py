""" Basic RGC asset tests """

from collections import OrderedDict
import pytest
__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"


class AssetDictTest:
    @pytest.mark.parametrize("gname", ["nonexistent", None])
    def test_with_nonexistent_genome(self, ro_rgc, gname):
        """ Verify asset dict is always returned, even if the requested genome does not exist """
        assert isinstance(ro_rgc.list(genome=gname), OrderedDict)

    @pytest.mark.parametrize("gname", ["nonexistent", None])
    def test_length(self, ro_rgc, all_genomes, gname):
        """ Verify asset dict is larger if nonexistent or no genome specified than ones that are
        returned for a specific genome"""
        for g in all_genomes:
            assert len(ro_rgc.list(genome=gname)) > len(ro_rgc.list(genome=g))

    def test_multiple_genomes(self, ro_rgc, all_genomes):
        """ Verify asset dict works with multiple genomes and returns all of them """
        assert sorted(ro_rgc.list(genome=all_genomes).keys()) == sorted(ro_rgc.list().keys())


class ListAssetsByGenomeTest:
    def test_returns_entire_mapping_when_no_genonome_specified(self, ro_rgc):
        assert ro_rgc.list_assets_by_genome() == ro_rgc.list()

    def test_returns_list(self, ro_rgc, all_genomes):
        for g in all_genomes:
            assert isinstance(ro_rgc.list_assets_by_genome(g), list)

    @pytest.mark.parametrize("gname", ["nonexistent", "genome"])
    def test_exception_on_nonexistent_genome(self, ro_rgc, gname):
        with pytest.raises(KeyError):
            ro_rgc.list_assets_by_genome(genome=gname)
