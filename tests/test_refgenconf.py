import pytest

from refgenconf import load_yaml, RefGenomeConfiguration

def test_rgc():
	rgc = RefGenomeConfiguration(load_yaml("refgenie.yaml"))
	print(rgc.genomes)

