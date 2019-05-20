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
        """
        Map each assembly name to a list of available asset names.

        :return Mapping[str, Iterable[str]]: mapping from assembly name to
            collection of available asset names.
        """
        return {g: list(self.genomes[g].keys()) for g in self.genomes}

    def assets_str(self):
        """

        :return:
        """
        string = ""
        for genome, values in self.genomes.items():
            string += "  {}: {}\n".format(genome, "; ".join(list(values)))
        return string

    def list_assets_by_genome(self, genome=None):
        return self.assets_dict() if genome is None else list(self.genomes[genome].keys())

    def list_genomes_by_asset(self, asset=None):
        return self._invert_genomes() \
            if not asset else [g for g, am in self.genomes if asset in am]

    def _invert_genomes(self):
        genomes = {}
        for g, am in self.genomes.items():
            for a in am.keys():
                genomes[a].setdefault(a, []).append(g)
        return genomes


def select_genome_config(filename, conf_env_vars=None, conf_name=CONFIG_NAME):
    """
    Get path to genome configuration file.

    :param str filename: name/path of genome configuration file
    :param Iterable[str] conf_env_vars: names of environment variables to
        consider; basically, a prioritized search list
    :param str conf_name: name of the kind of configuration file to request
    :return str: path to genome configuration file
    """
    return yacman.select_config(
        filename, conf_env_vars or CONFIG_ENV_VARS, conf_name)

