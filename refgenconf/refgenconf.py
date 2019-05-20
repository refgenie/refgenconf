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

    def assets_str(self, offset_text="  ", asset_sep="; ",
                   genome_assets_delim=": "):
        """
        Create a block of text representing genome-to-asset mapping.

        :param str offset_text: text that begins each line of the text
            representation that's produced
        :param str asset_sep: the delimiter between names of types of assets,
            within each genome line
        :param str genome_assets_delim: the delimiter to place between
            reference genome assembly name and its list of asset names
        :return str: text representing genome-to-asset mapping
        """
        def make_line(gen, assets):
            return offset_text + "{}{}{}".format(
                gen, genome_assets_delim, asset_sep.join(list(assets)))
        return "\n".join([make_line(g, am) for g, am in self.genomes.items()])

    def list_assets_by_genome(self, genome=None):
        """
        List types/names of assets that are available for one--or all--genomes.

        :param str | NoneType genome: reference genome assembly ID, optional;
            if omitted, the full mapping from genome to asset names
        :return Iterable[str] | Mapping[str, Iterable[str]]: collection of
            asset type names available for particular reference assembly if
            one is provided, else the full mapping between assembly ID and
            collection available asset type names
        """
        return self.assets_dict() if genome is None else list(self.genomes[genome].keys())

    def list_genomes_by_asset(self, asset=None):
        """
        List assemblies for which a particular asset is available.

        :param str | NoneType asset: name of type of asset of interest, optional
        :return Iterable[str] | Mapping[str, Iterable[str]]: collection of
            assemblies for which the given asset is available; if asset
            argument is omitted, the full mapping from name of asset type to
            collection of assembly names for which the asset key is available
            will be returned.
        """
        return self._invert_genomes() \
            if not asset else [g for g, am in self.genomes if asset in am]

    def _invert_genomes(self):
        """ Map each asset type/kind/name to a collection of assemblies.

        A configuration file encodes assets by genome, but in some use cases
        it's helpful to invert the direction of this mapping. The value of the
        asset key/name may differ by genome, so that information is
        necessarily lost in this inversion, but we can collect genome IDs by
        asset ID.

        :return Mapping[str, Iterable[str]] binding between asset kind/key/name
            and collection of reference genome assembly names for which the
            asset type is available
        """
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

