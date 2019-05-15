#!/usr/bin/env python

import yacman

CONFIG_ENV_VARS = ["REFGENIE"]
CONFIG_NAME = "genome configuration"

class RefGenomeConfiguration(yacman.YacAttMap):

    def get_index(self, genome_name, index_name):
        if not genome_name in self.genomes:
            msg = "Your genomes do not include {}".format(genome_name)
            raise MissingGenomeError(msg)

        if not index_name in self.genomes[genome_name]:
            msg = "Genome {} exists, but index {} is missing".format(genome_name, index_name)
            raise MissingIndexError(msg)

            return self.genomes[genome_name][index_name]

    def list_genomes(self):
        return list(self.genomes.keys())


    def list_assets(self):
        string = ""
        for genome, values in self.genomes.items():
            string += "  {}: {}\n".format(genome, "; ".join(list(values)))
        return string

    def idx(self):
        retval = {}
        for genome, values in self.genomes.items():
            retval[genome] = list(values)

        return retval



def load_genome_config(filename):
    return yacman.select_load_config(filename, CONFIG_ENV_VARS, CONFIG_NAME)


