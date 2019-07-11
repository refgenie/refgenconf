""" Tests for querying available reference genome assembly names """

from tests.conftest import get_conf_genomes

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


def test_genomes_list(rgc):
    """ List of available genomes is as expected. """
    assert get_conf_genomes() == rgc.genomes_list()


def test_genomes_str(rgc):
    """ Text of available genomes is as expected. """
    assert ", ".join(get_conf_genomes()) == rgc.genomes_str()
