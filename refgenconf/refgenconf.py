#!/usr/bin/env python

import yacman
from .exceptions import *

CONFIG_ENV_VARS = ["REFGENIE"]
CONFIG_NAME = "genome configuration"

__all__ = ["RefGenomeConfiguration", "select_genome_config",
           "CONFIG_ENV_VARS", "CONFIG_NAME"]


class RefGenomeConfiguration(yacman.YacAttMap):
    """ A sort of oracle of available reference genome assembly assets """

    def get_asset(self, genome_name, asset_name):
        """
        Get an asset for a particular assembly.

        :param str genome_name: name of a reference genome assembly of interest
        :param str asset_name: name of the particular asset to fetch
        :return str: path to the asset
        :raise refgenconf.MissingGenomeError: if the named assembly isn't known
            to this configuration instance
        :raise refgenconf.MissingAssetError: if the names assembly is known to
            this configuration instance, but the requested asset is unknown
        """
        # is this even helpful? Just use RGC.genome_name.asset_name...
        try:
            genome = self.genomes[genome_name]
        except KeyError:
            raise MissingGenomeError(
                "Your genomes do not include {}".format(genome_name))
        try:
            return genome[asset_name]
        except KeyError:
            raise MissingAssetError(
                "Genome {} exists, but index {} is missing".
                format(genome_name, asset_name))

    def genomes_list(self):
        """
        Get a list of this configuration's reference genome assembly IDs.

        :return Iterable[str]: list of this configuration's reference genome
            assembly IDs
        """
        return list(self.genomes.keys())

    def genomes_str(self):
        """
        Get as single string this configuration's reference genome assembly IDs.

        :return str: single string that lists this configuration's known
            reference genome assembly IDs
        """
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
    """
    Choose a

    :param str filename: name/path of genome configuration file
    :return:
    """
    return yacman.select_config(filename, CONFIG_ENV_VARS, CONFIG_NAME)

