"""Tests for querying available reference genome assembly names"""

from refgenconf.const import CFG_GENOMES_KEY

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


def test_genomes_list(my_rgc):
    """List of available genomes is as expected."""
    listed_aliases = my_rgc.genomes_list()
    digests = my_rgc[CFG_GENOMES_KEY].keys()
    aliases = sorted([my_rgc.get_genome_alias(digest=d) for d in digests])
    assert aliases == listed_aliases


def test_genomes_str(my_rgc):
    """Text of available genomes is as expected."""
    listed_aliases = my_rgc.genomes_str()
    digests = my_rgc[CFG_GENOMES_KEY].keys()
    aliases = sorted([my_rgc.get_genome_alias(digest=d) for d in digests])
    assert ", ".join(aliases) == listed_aliases
