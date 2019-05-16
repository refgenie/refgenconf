#!/usr/bin/env python

import yacman

CONFIG_ENV_VARS = ["REFGENIE"]
CONFIG_NAME = "genome configuration"

class RefGenomeConfiguration(yacman.YacAttMap):

    def get_asset(self, genome_name, asset_name):
        # is this even helpful? Just use RGC.genome_name.asset_name...
        if not genome_name in self.genomes:
            msg = "Your genomes do not include {}".format(genome_name)
            raise MissingGenomeError(msg)

        if not asset_name in self.genomes[genome_name]:
            msg = "Genome {} exists, but index {} is missing".format(genome_name, asset_name)
            raise MissingAssetError(msg)

            return self.genomes[genome_name][asset_name]

    def genomes_list(self):
        return list(self.genomes.keys())

    def genomes_str(self):
        return ", ".join(self.genomes_list())

    def assets_dict(self):
        return {i: self.genomes[i].keys() for i in [i for i in self.genomes]}

    def assets_str(self):
        string = ""
        for genome, values in self.genomes.items():
            string += "  {}: {}\n".format(genome, "; ".join(list(values)))
        return string

    def list_assets_by_genome(self, genome):
        return list(self["genome"].keys())


def select_genome_config(filename):
    return yacman.select_config(filename, CONFIG_ENV_VARS, CONFIG_NAME)

