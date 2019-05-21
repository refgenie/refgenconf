import refgenconf


def test_rgc():
	rgc = refgenconf.RefGenomeConfiguration("refgenie.yaml")
	print(rgc.genomes)
