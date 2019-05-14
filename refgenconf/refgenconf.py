#!/usr/bin/env python

import attmap
import yaml

class RefGenomeConfiguration(attmap.PathExAttMap):

    def get_index(self, genome_name, index_name):
        if not genome_name in self.refgenomes:
            msg = "Your genomes do not include {}".format(genome_name)
            raise MissingGenomeError(msg)

        if not index_name in self.refgenomes[genome_name]:
            msg = "Genome {} exists, but index {} is missing".format(genome_name, index_name)
            raise MissingIndexError(msg)

            return self.refgenomes[genome_name][index_name]

    def list_genomes(self):
        return list(self.refgenomes.keys())


    def list_indexes(self):
        string = ""
        for genome, value in self.refgenomes.items():
            string += "  {}: {}\n".format(genome, "; ".join(list(value.indexes)))
        return string

    def idx(self):
        retval = {}
        for genome, value in self.refgenomes.items():
            retval[genome] = list(value.indexes)

        return retval

    def to_yaml(self):
        ## TODO: use a recursive dict function for attmap representation
        try:
            return yaml.dump(self.__dict__, default_flow_style=False)
        except yaml.representer.RepresenterError:
            print("SERIALIZED SAMPLE DATA: {}".format(self))
            raise


def load_yaml(filename):
    import yaml
    with open(filename, 'r') as f:
        data = yaml.load(f, yaml.SafeLoader)
    return data

