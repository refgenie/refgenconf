""" Basic RGC asset tests """

from collections import OrderedDict
import pytest
from refgenconf.const import CFG_GENOMES_KEY
from yacman.exceptions import UndefinedAliasError

__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"


class ListTest:
    @pytest.mark.parametrize("gname", [None])
    def test_length(self, ro_rgc, all_genomes, gname):
        """
        Verify asset dict is larger if no genome specified than ones that
        are returned for a specific genome
        """
        for g in all_genomes:
            assert len(ro_rgc.list(genome=gname)) > len(ro_rgc.list(genome=g))

    def test_multiple_genomes(self, ro_rgc, all_genomes):
        """ Verify asset dict works with multiple genomes and returns all of them """
        assert sorted(ro_rgc.list(genome=all_genomes).keys()) == sorted(
            ro_rgc.list().keys()
        )


class ListByGenomeTest:
    def test_returns_entire_mapping_when_no_genonome_specified(self, my_rgc):
        assert my_rgc.list_assets_by_genome() == my_rgc.list()

    def test_returns_list(self, my_rgc):
        for g in my_rgc[CFG_GENOMES_KEY].keys():
            assert isinstance(my_rgc.list_assets_by_genome(genome=g), list)

    @pytest.mark.parametrize("gname", ["nonexistent", "genome"])
    def test_exception_on_nonexistent_genome(self, ro_rgc, gname):
        with pytest.raises(UndefinedAliasError):
            ro_rgc.list_assets_by_genome(genome=gname)
