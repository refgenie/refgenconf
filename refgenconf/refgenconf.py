#!/usr/bin/env python

from collections import Iterable, Mapping
from inspect import getfullargspec as finspect
import logging
import os
import shutil
from urllib.error import HTTPError
import urllib.request
import warnings
from attmap import PathExAttMap as PXAM
from ubiquerg import is_url
import yacman
from .const import *
from .exceptions import *


_LOGGER = logging.getLogger(__name__)


__all__ = ["RefGenConf"]


class RefGenConf(yacman.YacAttMap):
    """ A sort of oracle of available reference genome assembly assets """

    def __init__(self, entries=None):
        super(RefGenConf, self).__init__(entries)
        self.setdefault(CFG_GENOMES_KEY, PXAM())


    def assets_dict(self):
        """
        Map each assembly name to a list of available asset names.

        :return Mapping[str, Iterable[str]]: mapping from assembly name to
            collection of available asset names.
        """
        return {g: list(assets.keys()) for g, assets in self.genomes.items()}

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

    def get_asset(self, genome_name, asset_name, strict_exists=True,
                  check_exist=lambda p: os.path.exists(p) or is_url(p)):
        """
        Get an asset for a particular assembly.

        :param str genome_name: name of a reference genome assembly of interest
        :param str asset_name: name of the particular asset to fetch
        :param bool | NoneType strict_exists: how to handle case in which
            path doesn't exist; True to raise IOError, False to raise
            RuntimeWarning, and None to do nothing at all
        :param function(callable) -> bool check_exist: how to check for
            asset/path existence
        :return str: path to the asset
        :raise TypeError: if the existence check is not a one-arg function
        :raise refgenconf.MissingGenomeError: if the named assembly isn't known
            to this configuration instance
        :raise refgenconf.MissingAssetError: if the names assembly is known to
            this configuration instance, but the requested asset is unknown
        """
        if not callable(check_exist) or len(finspect(check_exist).args) != 1:
            raise TypeError("Asset existence check must be a one-arg function.")
        # is this even helpful? Just use RGC.genome_name.asset_name...
        try:
            genome = self.genomes[genome_name]
        except KeyError:
            raise MissingGenomeError(
                "Your genomes do not include {}".format(genome_name))
        try:
            path = genome[asset_name]
        except KeyError:
            raise MissingAssetError(
                "Genome {} exists, but index {} is missing".
                format(genome_name, asset_name))
        if strict_exists is not None and not check_exist(path):
            msg = "Asset may not exist: {}".format(path)
            for ext in [".tar.gz", ".tar"]:
                p_prime = path + ext
                if check_exist(p_prime):
                    msg += "; {} does exist".format(p_prime)
                    break
            if strict_exists:
                raise IOError(msg)
            else:
                warnings.warn(msg, RuntimeWarning)
        return path

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
            if not asset else [g for g, am in self.genomes.items() if asset in am]

    def pull_asset(self, genome, assets, genome_config, unpack=True):
        """
        Download and possibly unpack one or more assets for a given ref gen.

        :param str genome: name of a reference genome assembly of interest
        :param str assets: name(s) of particular asset(s) to fetch
        :param str genome_config: path to genome configuration file to update
        :param bool unpack: whether to unpack a tarball
        :return Iterable[(str, str | NoneType)]: collection of pairs of asset
            name and folder name (key-value pair with which genome config file
            is updated) if pull succeeds, else asset key and a null value.
        """
        if isinstance(assets, str):
            assets = [assets]
        elif not isinstance(assets, Iterable):
            raise TypeError("Assets to pull should be single name or collection "
                            "of names; got {} ({})".format(assets, type(assets)))
        return [self._pull_asset(genome, a, genome_config, unpack) for a in assets]

    def _pull_asset(self, genome, asset, genome_config, unpack=True):

        _LOGGER.info("Starting pull for {}: {}".format(genome, asset))

        def raise_unpack_error():
            raise NotImplementedError("Tarball preservation isn't yet supported.")

        unpack or raise_unpack_error()

        # local file to save as
        outdir = os.path.join(self.genome_folder, genome)
        filepath = os.path.join(outdir, asset + ".tar")

        try:
            if not os.path.exists(outdir):
                _LOGGER.debug("Creating directory: {}".format(outdir))
                os.makedirs(outdir)
        except FileNotFoundError as e:
            _LOGGER.error(str(e))
            _LOGGER.error("Missing genomes folder? {}".format(self.genome_folder))
            return asset, None

        url = "{base}/asset/{g}/{a}/archive".format(
            base=self.genome_server, g=genome, a=asset)
        # Download the file from `url` and save it locally under `filepath`:
        _LOGGER.info("Downloading URL: {}".format(url))
        try:
            _download_url_to_file(url, filepath)
        except HTTPError as e:
            _LOGGER.error("File not found on server: {}".format(e))
            return asset, None
        except ConnectionRefusedError as e:
            _LOGGER.error(str(e))
            _LOGGER.error("Server {} refused download. Check your internet settings".
                          format(self.genome_server))
            return asset, None
        else:
            _LOGGER.info("Download complete: {}".format(filepath))

        # successfully downloaded and moved tarball; untar it
        # TODO: Make this a CLI option.
        if unpack:
            if filepath.endswith(".tar") or filepath.endswith(".tgz"):
                import tarfile
                with tarfile.open(filepath) as tf:
                    tf.extractall(path=outdir)
            _LOGGER.debug("Unpackaged archive into: {}".format(outdir))

            # Write to config file
            # TODO: Figure out how we want to handle the asset_key to folder_name
            # mapping. Do we want to require that asset == folder_name?
            # I guess we allow it to differ, but we keep it that way within refgenie?
            # Right now they are identical:
            folder_name = asset
            _LOGGER.info("Writing genome config file: {}".format(genome_config))
            # use the asset attribute 'path' instead of 'folder_name' here; the asset attributes need to be pulled first.
            # see issue: https://github.com/databio/refgenie/issues/23
            self.update_genomes(genome, asset, {CFG_ASSET_PATH_KEY: folder_name})
            self.write(genome_config)
            return asset, folder_name
        else:
            raise_unpack_error()

    def update_genomes(self, genome, asset=None, data=None):
        """
        Updates the genomes in RefGenConf object at any level.
        If a requested genome-asset mapping is missing, it will be created

        :param str genome: genome to be added/updated
        :param str asset: asset to be added/updated
        :param Mapping data: data to be added/updated
        :return RefGenConf: updated object
        """
        def check(obj, datatype, name):
            if obj is None:
                return False
            if not isinstance(obj, datatype):
                raise TypeError("{} must be {}; got {}".format(
                    name, datatype.__name__, type(obj).__name__))
            return True

        if check(genome, str, "genome"):
            self[CFG_GENOMES_KEY].setdefault(genome, PXAM())
            if check(asset, str, "asset"):
                self[CFG_GENOMES_KEY][genome].setdefault(asset, PXAM())
                if check(data, Mapping, "data"):
                    self[CFG_GENOMES_KEY][genome][asset].update(data)
        return self

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
                genomes.setdefault(a, []).append(g)
        return genomes


def _download_url_to_file(url, filepath):
    """
    Download asset at given URL to given filepath.

    :param str url: URL to download
    :param str filepath: path to file to save download
    """
    with urllib.request.urlopen(url) as response, open(filepath, 'wb') as outf:
        shutil.copyfileobj(response, outf)
