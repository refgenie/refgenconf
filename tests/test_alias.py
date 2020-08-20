import pytest
import os
from yacman import UndefinedAliasError


class TestAliasSetting:
    @pytest.mark.parametrize(["alias", "digest"],
                             [(["human_repeats", "rCRSd"], None)])
    def test_set_genome_alias_server_more_than_1(self, my_rgc, alias, digest):
        """ Multi digest lookup is not implemented """
        with pytest.raises(NotImplementedError):
            my_rgc.set_genome_alias(genome=alias, digest=digest)

    @pytest.mark.parametrize(["alias", "digest"], [("human_repeats", None)])
    @pytest.mark.xfail
    def test_set_genome_alias_server(self, my_rgc, alias, digest):
        """ Lookup aliases for a single digest """
        my_rgc.set_genome_alias(genome=alias, digest=digest)
        assert alias in my_rgc.get_genome_alias(digest=digest, all_aliases=True)

    @pytest.mark.parametrize(["alias", "digest"], [(["hr"], "b03e6360748bf6c876363537ca5a9e0b0de2cd059133bd2d"),
                                                    (["hr", "h_r"], "b03e6360748bf6c876363537ca5a9e0b0de2cd059133bd2d")])
    def test_set_genome_alias(self, my_rgc, alias, digest):
        """
        Set aliases, check whether all exist in the object and as
        directories on disk and remove
        """
        my_rgc.set_genome_alias(genome=alias, digest=digest)
        assert all([a in my_rgc.get_genome_alias(digest=digest, all_aliases=True) for a in alias])
        assert all([os.path.exists(os.path.join(my_rgc.alias_dir, a)) for a in alias])
        my_rgc.remove_genome_aliases(digest=digest, aliases=alias)

    @pytest.mark.parametrize(["alias", "digest"], [(["hr"], "b03e6360748bf6c876363537ca5a9e0b0de2cd059133bd2d"),
                                                    (["hr", "h_r"], "b03e6360748bf6c876363537ca5a9e0b0de2cd059133bd2d")])
    def test_set_genome_alias_reset(self, my_rgc, alias, digest):
        """
        Get original aliases, wipe out all current aliases and set new ones,
        check whether all exist in the object and as
        directories on disk and remove and bring the original state back
        """
        ori_state = my_rgc.get_genome_alias(digest=digest, all_aliases=True)
        my_rgc.set_genome_alias(genome=alias, digest=digest, reset_digest=True)
        assert all([a in my_rgc.get_genome_alias(digest=digest, all_aliases=True) for a in alias])
        assert all([os.path.exists(os.path.join(my_rgc.alias_dir, a)) for a in alias])
        assert len(my_rgc.get_genome_alias(digest=digest, all_aliases=True)) == len(alias)
        my_rgc.set_genome_alias(genome=ori_state, digest=digest, reset_digest=True)


class TestAliasGetting:
    @pytest.mark.parametrize("digest", ["b03e6360748bf6c876363537ca5a9e0b0de2cd059133bd2d"])
    def test_get_genome_alias_basic(self, my_rgc, digest):
        """ Get a single alias, first from the list, if multiple """
        assert isinstance(my_rgc.get_genome_alias(digest=digest), str)

    @pytest.mark.parametrize("digest", ["b03e6360748bf6c876363537ca5a9e0b0de2cd059133bd2d"])
    def test_get_genome_alias_multi(self, my_rgc, digest):
        """ Get muliple single aliases, result is always a list """
        assert isinstance(my_rgc.get_genome_alias(digest=digest, all_aliases=True), list)

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