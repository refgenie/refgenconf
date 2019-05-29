import refgenconf


def test_rgc():
	rgc = refgenconf.RefGenConf("refgenie.yaml")
	print(rgc.genomes)
