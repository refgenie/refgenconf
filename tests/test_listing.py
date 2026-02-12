"""Basic RGC asset tests"""

import pytest
from yacman import UndefinedAliasError

from refgenconf.const import CFG_GENOMES_KEY

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
        """Verify asset dict works with multiple genomes and returns all of them"""
        assert sorted(ro_rgc.list(genome=all_genomes).keys()) == sorted(
            ro_rgc.list().keys()
        )

    def test_no_asset_section(self, ro_rgc):
        """
        Verify listing works even if the 'assets' section is missing in the config.
        This situation may occur after setting genome identity for nonexistent genome.
        """
        # get the original genomes count
        ori_genomes_count = len(ro_rgc[CFG_GENOMES_KEY])
        # set test alias, which will create an empty genome section
        ro_rgc.set_genome_alias(
            genome="test_alias",
            digest="test_digest",
            create_genome=True,
        )
        # check if list works and skips the empty genome
        assert len(ro_rgc.list().keys()) == ori_genomes_count
        # clean up
        ro_rgc.remove_genome_aliases(digest="test_digest")
        from yacman import write_lock

        with write_lock(ro_rgc) as r:
            del r["genomes"].data["test_digest"]
            r.write()


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


class ListSeekKeysValuesTest:
    def test_asset_without_seek_keys(self, ro_rgc):
        """Verify list_seek_keys_values handles assets without seek_keys gracefully.

        This tests the fix for issue #133 where a child asset's parent may lack
        the seek_keys field, causing a TypeError when iterating over None.
        """
        from refgenconf.const import CFG_ASSETS_KEY, CFG_ASSET_TAGS_KEY
        from yacman import write_lock

        # Pick a genome and create a test asset without seek_keys
        genome_digest = list(ro_rgc[CFG_GENOMES_KEY].keys())[0]

        with write_lock(ro_rgc) as r:
            r[CFG_GENOMES_KEY][genome_digest][CFG_ASSETS_KEY]["no_seek_keys_asset"] = {
                CFG_ASSET_TAGS_KEY: {
                    "default": {
                        "asset_path": "/tmp/test",
                        "asset_digest": "abc123",
                        # Note: no seek_keys field here
                    }
                },
                "default_tag": "default",
            }
            r.write()

        try:
            # This should not raise TypeError
            result = ro_rgc.list_seek_keys_values(
                genomes=genome_digest, assets="no_seek_keys_asset"
            )

            # The result should have an empty dict for this asset's tag
            assert genome_digest in result
            assert "no_seek_keys_asset" in result[genome_digest]
            assert "default" in result[genome_digest]["no_seek_keys_asset"]
            assert result[genome_digest]["no_seek_keys_asset"]["default"] == {}
        finally:
            # Clean up
            with write_lock(ro_rgc) as r:
                del r[CFG_GENOMES_KEY][genome_digest][CFG_ASSETS_KEY][
                    "no_seek_keys_asset"
                ]
                r.write()
