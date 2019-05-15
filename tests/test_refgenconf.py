import pytest

import refgenconf

def test_rgc():
	rgc = refgenconf.RefGenomeConfiguration("refgenie.yaml")
	print(rgc.genomes)


def test_find_config():
	refgenconf.load_genome_config("refgenie.yaml")

	logging.basicConfig(level=logging.DEBUG)
	conf = refgenconf.load_genome_config(None)
	conf
