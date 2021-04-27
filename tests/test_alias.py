import os
from shutil import rmtree

import pytest
from yacman import UndefinedAliasError

from refgenconf.const import CFG_ALIASES_KEY, CFG_GENOMES_KEY

DEMO_FILES = ["demo.fa.gz", "demo2.fa", "demo3.fa", "demo4.fa", "demo5.fa.gz"]


class TestAliasSetting:
    @pytest.mark.parametrize(["alias", "digest"], [(["human_repeats", "rCRSd"], None)])
    def test_set_genome_alias_server_more_than_1(self, my_rgc, alias, digest):
        """Multi digest lookup is not implemented"""
        with pytest.raises(NotImplementedError):
            my_rgc.set_genome_alias(genome=alias, digest=digest)

    @pytest.mark.parametrize(["alias", "digest"], [("human_repeats", None)])
    @pytest.mark.xfail
    def test_set_genome_alias_server(self, my_rgc, alias, digest):
        """Lookup aliases for a single digest"""
        my_rgc.set_genome_alias(genome=alias, digest=digest)
        assert alias in my_rgc.get_genome_alias(digest=digest, all_aliases=True)

    @pytest.mark.parametrize(
        ["alias", "digest"],
        [
            (["hr"], "7319f9237651755047bc40d7f7a9770d42a537e840f4e105"),
            (["hr", "h_r"], "7319f9237651755047bc40d7f7a9770d42a537e840f4e105"),
        ],
    )
    def test_set_genome_alias(self, my_rgc, alias, digest):
        """
        Set aliases, check whether all exist in the object and as
        directories on disk and remove
        """
        my_rgc.set_genome_alias(genome=alias, digest=digest)
        assert all(
            [
                a in my_rgc.get_genome_alias(digest=digest, all_aliases=True)
                for a in alias
            ]
        )
        assert all([os.path.exists(os.path.join(my_rgc.alias_dir, a)) for a in alias])
        my_rgc.remove_genome_aliases(digest=digest, aliases=alias)

    @pytest.mark.parametrize(
        ["alias", "digest"],
        [
            (["hr"], "7319f9237651755047bc40d7f7a9770d42a537e840f4e105"),
            (["hr", "h_r"], "7319f9237651755047bc40d7f7a9770d42a537e840f4e105"),
        ],
    )
    def test_set_genome_alias_reset(self, my_rgc, alias, digest):
        """
        Get original aliases, wipe out all current aliases and set new ones,
        check whether all exist in the object and as
        directories on disk and remove and bring the original state back
        """
        ori_state = my_rgc.get_genome_alias(digest=digest, all_aliases=True)
        my_rgc.set_genome_alias(genome=alias, digest=digest, reset_digest=True)
        assert all(
            [
                a in my_rgc.get_genome_alias(digest=digest, all_aliases=True)
                for a in alias
            ]
        )
        assert all([os.path.exists(os.path.join(my_rgc.alias_dir, a)) for a in alias])
        assert len(my_rgc.get_genome_alias(digest=digest, all_aliases=True)) == len(
            alias
        )
        my_rgc.set_genome_alias(genome=ori_state, digest=digest, reset_digest=True)


class TestAliasGetting:
    @pytest.mark.parametrize(
        "digest", ["7319f9237651755047bc40d7f7a9770d42a537e840f4e105"]
    )
    def test_get_genome_alias_basic(self, my_rgc, digest):
        """
        Get a single alias, first from the list, if multiple and then use
        the result to get the digest back
        """
        alias = my_rgc.get_genome_alias(digest=digest)
        assert isinstance(alias, str)
        assert my_rgc.get_genome_alias_digest(alias=alias) == digest
        # test fallback
        assert my_rgc.get_genome_alias_digest(alias=digest, fallback=True) == digest

    @pytest.mark.parametrize(
        "digest", ["7319f9237651755047bc40d7f7a9770d42a537e840f4e105"]
    )
    def test_get_genome_alias_multi(self, my_rgc, digest):
        """Get muliple single aliases, result is always a list"""
        assert isinstance(
            my_rgc.get_genome_alias(digest=digest, all_aliases=True), list
        )

    @pytest.mark.parametrize("digest", ["human_repeats"])
    def test_get_genome_alias_no_fallback(self, my_rgc, digest):
        """
        If an alias instead of digest is provided, an appropriate
        exception is risen
        """
        with pytest.raises(UndefinedAliasError):
            my_rgc.get_genome_alias(digest=digest)

    @pytest.mark.parametrize("digest", ["human_repeats", "rCRSd", "mouse_chrM2x"])
    def test_get_genome_alias_fallback(self, my_rgc, digest):
        """
        If an alias instead of digest is provided, an appropriate
        exception is risen
        """
        assert isinstance(my_rgc.get_genome_alias(digest=digest, fallback=True), str)

    @pytest.mark.parametrize("digest", ["human_repeats_bogus", "nonexistent"])
    def test_get_genome_alias_fallback_nomatch(self, my_rgc, digest):
        """
        If an alias instead of digest is provided, an appropriate
        exception is risen
        """
        with pytest.raises(UndefinedAliasError):
            my_rgc.get_genome_alias(digest=digest, fallback=True)


class TestAliasRemoval:
    @pytest.mark.parametrize(
        "digest", ["7319f9237651755047bc40d7f7a9770d42a537e840f4e105"]
    )
    def test_remove_genome_alias_all(self, my_rgc, digest):
        """
        Save original aliases state, remove all, check that aliases have
        been removed from the object and disk, bring back the original state
        """
        ori_state = my_rgc.get_genome_alias(digest=digest)
        my_rgc.set_genome_alias(digest=digest, genome=ori_state)
        my_rgc.remove_genome_aliases(digest=digest)
        with pytest.raises(UndefinedAliasError):
            my_rgc.get_genome_alias(digest=digest)
        assert all(
            [not os.path.exists(os.path.join(my_rgc.alias_dir, a)) for a in ori_state]
        )
        my_rgc.set_genome_alias(digest=digest, genome=ori_state)
        assert isinstance(
            my_rgc.get_genome_alias(digest=digest, all_aliases=True), list
        )

    @pytest.mark.parametrize(
        ["alias", "digest"],
        [
            (["hr"], "7319f9237651755047bc40d7f7a9770d42a537e840f4e105"),
            (["hr", "h_r"], "7319f9237651755047bc40d7f7a9770d42a537e840f4e105"),
        ],
    )
    def test_remove_genome_alias_specific(self, my_rgc, digest, alias):
        """
        Set selected aliases and an additional one remove the selected ones,
        verify the additional one exists
        """
        my_rgc.set_genome_alias(digest=digest, genome=alias + ["human_repeats"])
        my_rgc.remove_genome_aliases(digest=digest, aliases=alias)
        assert "human_repeats" in my_rgc.get_genome_alias(
            digest=digest, all_aliases=True
        )


class TestInitializeGenome:
    @pytest.mark.parametrize("fasta_name", DEMO_FILES)
    def test_initialize_genome(self, my_rgc, fasta_name, fasta_path):
        """
        Save original aliases state, remove all, check that aliases have
        been removed from the object and disk, bring back the original state
        """
        d, asds = my_rgc.initialize_genome(
            fasta_path=os.path.join(fasta_path, fasta_name),
            alias=fasta_name,
            fasta_unzipped=not fasta_name.endswith(".gz"),
        )
        assert d in my_rgc[CFG_GENOMES_KEY]
        assert fasta_name in my_rgc[CFG_GENOMES_KEY][d][CFG_ALIASES_KEY]
        with my_rgc as r:
            del r[CFG_GENOMES_KEY][d]
        rmtree(os.path.join(my_rgc.alias_dir, fasta_name))
