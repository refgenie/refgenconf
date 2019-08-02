#!/usr/bin/env python

from collections import Iterable, Mapping, OrderedDict
from functools import partial

# Some short-term hacks to get at least 1 working version on python 2.7
import sys
if sys.version_info >= (3, ):
    from inspect import getfullargspec as finspect
    from urllib.error import HTTPError, ContentTooShortError
else:
    from future.standard_library import install_aliases
    install_aliases()
    from inspect import getargspec as finspect
    from urllib2 import HTTPError
    from urllib.error import ContentTooShortError
    ConnectionRefusedError = Exception

import urllib.request
import itertools
import logging
import os
import signal
import warnings

from attmap import PathExAttMap as PXAM
from ubiquerg import checksum, is_url, query_yes_no
from tqdm import tqdm
import yacman

from .const import *
from .helpers import unbound_env_vars
from .exceptions import *


_LOGGER = logging.getLogger(__name__)


__all__ = ["RefGenConf"]


def _handle_sigint(filepath):
    def handle(sig, frame):
        _LOGGER.warning("\nThe download was interrupted: {}".format(filepath))
        try:
            os.remove(filepath)
        except OSError:
            _LOGGER.debug("'{}' not found, can't remove".format(filepath))
        else:
            _LOGGER.info("Incomplete file '{}' was removed".format(filepath))
        sys.exit(0)
    return handle


class RefGenConf(yacman.YacAttMap):
    """ A sort of oracle of available reference genome assembly assets """

    def __init__(self, entries=None):
        """
        Create the config instance by with a filepath or key-value pairs.

        :param str | Iterable[(str, object)] | Mapping[str, object] entries:
            config filepath or collection of key-value pairs
        :raise refgenconf.MissingConfigDataError: if a required configuration
            item is missing
        :raise ValueError: if entries is given as a string and is not a file
        """
        super(RefGenConf, self).__init__(entries)
        genomes = self.setdefault(CFG_GENOMES_KEY, PXAM())
        if not isinstance(genomes, PXAM):
            if genomes:
                _LOGGER.warning(
                    "'{k}' value is a {t_old}, not a {t_new}; setting to empty {t_new}".
                        format(k=CFG_GENOMES_KEY, t_old=type(genomes).__name__, t_new=PXAM.__name__))
            self[CFG_GENOMES_KEY] = PXAM()
        if CFG_FOLDER_KEY not in self:
            self[CFG_FOLDER_KEY] = os.path.dirname(entries) if isinstance(entries, str) else os.getcwd()
        try:
            version = self[CFG_VERSION_KEY]
        except KeyError:
            _LOGGER.warning("Config lacks version key: {}".format(CFG_VERSION_KEY))
        else:
            try:
                version = float(version)
            except ValueError:
                _LOGGER.warning("Cannot parse as numeric: {}".format(version))
            else:
                if version < REQ_CFG_VERSION:
                    msg = "This genome config (v{}) is not compliant with v{} standards. To use it, please downgrade " \
                          "refgenie: 'pip install refgenie==0.4.4'.".format(self[CFG_VERSION_KEY], str(REQ_CFG_VERSION))
                    raise ConfigNotCompliantError(msg)
                else:
                    _LOGGER.debug("Config version is compliant: {}".format(version))
        try:
            self[CFG_SERVER_KEY] = self[CFG_SERVER_KEY].rstrip("/")
        except KeyError:
            raise MissingConfigDataError(CFG_SERVER_KEY)

    def __bool__(self):
        minkeys = set(self.keys()) == {CFG_SERVER_KEY, CFG_FOLDER_KEY, CFG_GENOMES_KEY}
        return not minkeys or bool(self[CFG_GENOMES_KEY])

    __nonzero__ = __bool__

    def assets_dict(self, genome=None, order=None):
        """
        Map each assembly name to a list of available asset names.

        :param function(str) -> object order: how to key genome IDs for sort
        :param list[str] | str genome: genomes that the assets should be found for
        :return Mapping[str, Iterable[str]]: mapping from assembly name to
            collection of available asset names.
        """
        refgens = _select_genomes(sorted(self[CFG_GENOMES_KEY].keys(), key=order), genome)
        return OrderedDict([(g, sorted(list(self[CFG_GENOMES_KEY][g][CFG_ASSETS_KEY].keys()), key=order))
                            for g in refgens])

    def assets_str(self, offset_text="  ", asset_sep=", ", genome_assets_delim=": ", genome=None, order=None):
        """
        Create a block of text representing genome-to-asset mapping.

        :param str offset_text: text that begins each line of the text
            representation that's produced
        :param str asset_sep: the delimiter between names of types of assets,
            within each genome line
        :param str genome_assets_delim: the delimiter to place between
            reference genome assembly name and its list of asset names
        :param list[str] | str genome: genomes that the assets should be found for
        :param order: function(str) -> object how to key genome IDs and asset
            names for sort
        :return str: text representing genome-to-asset mapping
        """
        refgens = _select_genomes(sorted(self[CFG_GENOMES_KEY].keys(), key=order), genome)
        make_line = partial(_make_genome_assets_line, offset_text=offset_text, genome_assets_delim=genome_assets_delim,
                            asset_sep=asset_sep, order=order)
        return "\n".join([make_line(g, self[CFG_GENOMES_KEY][g][CFG_ASSETS_KEY]) for g in refgens])

    def filepath(self, genome, asset, ext=".tar"):
        """
        Determine path to a particular asset for a particular genome.

        :param str genome: reference genome ID
        :param str asset: asset name
        :param str ext: file extension
        :return str: path to asset for given genome and asset kind/name
        """
        return os.path.join(self[CFG_FOLDER_KEY], genome, asset + ext)

    def genomes_list(self, order=None):
        """
        Get a list of this configuration's reference genome assembly IDs.

        :return Iterable[str]: list of this configuration's reference genome
            assembly IDs
        """
        return sorted(list(self[CFG_GENOMES_KEY].keys()), key=order)

    def genomes_str(self, order=None):
        """
        Get as single string this configuration's reference genome assembly IDs.

        :param order: function(str) -> object how to key genome IDs for sort
        :return str: single string that lists this configuration's known
            reference genome assembly IDs
        """
        return ", ".join(self.genomes_list(order))

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
        _LOGGER.debug("Getting asset '{}' for genome '{}'".
                     format(asset_name, genome_name))
        if not callable(check_exist) or len(finspect(check_exist).args) != 1:
            raise TypeError("Asset existence check must be a one-arg function.")
        path = _genome_asset_path(self[CFG_GENOMES_KEY], genome_name, asset_name)
        if os.path.isabs(path) and check_exist(path):
            return path
        _LOGGER.debug("Relative or nonexistent path: {}".format(path))
        fullpath = os.path.join(self[CFG_FOLDER_KEY], genome_name, path)
        _LOGGER.debug("Trying path relative to genome folder: {}".format(fullpath))
        if check_exist(fullpath):
            return fullpath
        elif strict_exists is None:
            return path
        msg = "Asset '{}' for genome '{}' doesn't exist; tried {} and {}".\
            format(asset_name, genome_name, path, fullpath)
        extant = []
        for base, ext in itertools.product([path, fullpath], [".tar.gz", ".tar"]):
            # Attempt to enrich message with extra guidance.
            p_prime = base + ext
            if check_exist(p_prime):
                extant.append(p_prime)
        if extant:
            msg += ". These paths exist: {}".format(extant)
        if strict_exists is True:
            raise IOError(msg)
        else:
            warnings.warn(msg, RuntimeWarning)
        return path

    def list_assets_by_genome(self, genome=None, order=None):
        """
        List types/names of assets that are available for one--or all--genomes.

        :param str | NoneType genome: reference genome assembly ID, optional;
            if omitted, the full mapping from genome to asset names
        :param order: function(str) -> object how to key genome IDs and asset
            names for sort
        :return Iterable[str] | Mapping[str, Iterable[str]]: collection of
            asset type names available for particular reference assembly if
            one is provided, else the full mapping between assembly ID and
            collection available asset type names
        """
        return self.assets_dict(genome, order)[genome] if genome is not None else self.assets_dict(order)

    def list_genomes_by_asset(self, asset=None, order=None):
        """
        List assemblies for which a particular asset is available.

        :param str | NoneType asset: name of type of asset of interest, optional
        :param order: function(str) -> object how to key genome IDs and asset
            names for sort
        :return Iterable[str] | Mapping[str, Iterable[str]]: collection of
            assemblies for which the given asset is available; if asset
            argument is omitted, the full mapping from name of asset type to
            collection of assembly names for which the asset key is available
            will be returned.
        """
        return self._invert_genomes(order) if not asset else \
            sorted([g for g, data in self[CFG_GENOMES_KEY].items()
                    if asset in data.get(CFG_ASSETS_KEY)], key=order)

    def list_local(self, genome=None, order=None):
        """
        List locally available reference genome IDs and assets by ID.

        :param list[str] | str genome: genomes that the assets should be found for
        :param order: function(str) -> object how to key genome IDs and asset
            names for sort
        :return str, str: text reps of locally available genomes and assets
        """
        genomes_str = self.genomes_str(order=order) if genome is None \
            else ", ".join(_select_genomes(sorted(self[CFG_GENOMES_KEY].keys(), key=order), genome))
        return genomes_str, self.assets_str(genome=genome, order=order)

    def list_remote(self, get_url=lambda rgc: "{}/assets".format(rgc.genome_server), genome=None, order=None):
        """
        List genomes and assets available remotely.

        :param function(refgenconf.RefGenConf) -> str get_url: how to determine
            URL request, given RefGenConf instance
        :param list[str] | str genome: genomes that the assets should be found for
        :param order: function(str) -> object how to key genome IDs and asset
            names for sort
        :return str, str: text reps of remotely available genomes and assets
        """
        url = get_url(self)
        _LOGGER.info("Querying available assets from server: {}".format(url))
        genomes, assets = _list_remote(url, genome, order)
        return genomes, assets

    def pull_asset(self, genome, assets, genome_config, unpack=True, force=None,
                   get_json_url=lambda base, g, a: "{}/asset/{}/{}".format(base, g, a),
                   get_main_url=None, build_signal_handler=_handle_sigint):
        """
        Download and possibly unpack one or more assets for a given ref gen.

        :param str genome: name of a reference genome assembly of interest
        :param str assets: name(s) of particular asset(s) to fetch
        :param str genome_config: path to genome configuration file to update
        :param bool unpack: whether to unpack a tarball
        :param bool | NoneType force: how to handle case in which asset path
            already exists; null for prompt (on a per-asset basis), False to
            effectively auto-reply No to the prompt to replace existing file,
            and True to auto-replay Yes for existing asset replacement.
        :param function(str, str, str) -> str get_json_url: how to build URL from
            genome server URL base, genome, and asset
        :param function(str) -> str get_main_url: how to get archive URL from
            main URL
        :param function(str) -> function build_signal_handler: how to create
            a signal handler to use during the download; the single argument
            to this function factory is the download filepath
        :return Iterable[(str, str | NoneType)]: collection of pairs of asset
            name and folder name (key-value pair with which genome config file
            is updated) if pull succeeds, else asset key and a null value.
        :raise TypeError: if the assets argument is neither string nor other
            Iterable
        :raise refgenconf.UnboundEnvironmentVariablesError: if genome folder
            path contains any env. var. that's unbound
        """
        missing_vars = unbound_env_vars(self.genome_folder)
        if missing_vars:
            raise UnboundEnvironmentVariablesError(", ".join(missing_vars))
        if isinstance(assets, str):
            assets = [assets]
        elif not isinstance(assets, Iterable):
            raise TypeError("Assets to pull should be single name or collection "
                            "of names; got {} ({})".format(assets, type(assets)))
        return [self._pull_asset(genome, a, genome_config, unpack, force,
                                 get_json_url, get_main_url, build_signal_handler)
                for a in assets]

    def _pull_asset(self, genome, asset, genome_config, unpack, force,
                    get_json_url, get_main_url, build_signal_handler):
        bundle_name = '{}/{}'.format(genome, asset)
        _LOGGER.info("Starting pull for '{}'".format(bundle_name))

        def raise_unpack_error():
            raise NotImplementedError("The option for not extracting the tarballs is not yet supported.")

        unpack or raise_unpack_error()

        # local file to save as
        filepath = self.filepath(genome, asset)
        outdir = os.path.dirname(filepath)

        if os.path.exists(filepath):
            # TODO: how to best handle the result value when the asset exists?
            def preserve():
                _LOGGER.debug("Preserving existing: {}".format(filepath))
                return asset, filepath

            def msg_overwrite():
                _LOGGER.debug("Overwriting: {}".format(filepath))
            if force is False:
                return preserve()
            elif force is None:
                if not query_yes_no("Replace existing ({})?".format(filepath), "no"):
                    return preserve()
                else:
                    msg_overwrite()
            else:
                msg_overwrite()

        url_json = get_json_url(self.genome_server, genome, asset)
        url = url_json + "/archive" if get_main_url is None \
            else get_main_url(self.genome_server, genome, asset)

        archive_data = _download_json(url_json)
        if not os.path.exists(outdir):
            _LOGGER.debug("Creating directory: {}".format(outdir))
            os.makedirs(outdir)
        archsize = archive_data[CFG_ARCHIVE_SIZE_KEY]
        _LOGGER.info("'{}' archive size: {}".format(bundle_name, archsize))
        if _is_large_archive(archsize) and not \
                query_yes_no("Are you sure you want to download this large archive?"):
            _LOGGER.info("pull action aborted by user")
            return asset, None

        # Download the file from `url` and save it locally under `filepath`:
        _LOGGER.info("Downloading URL: {}".format(url))
        try:
            signal.signal(signal.SIGINT, build_signal_handler(filepath))
            _download_url_progress(url, filepath, bundle_name)
        except HTTPError as e:
            _LOGGER.error("File not found on server: {}".format(e))
            return asset, None
        except ConnectionRefusedError as e:
            _LOGGER.error(str(e))
            _LOGGER.error("Server {} refused download. Check your internet settings".
                          format(self.genome_server))
            return asset, None
        except ContentTooShortError as e:
            _LOGGER.error(str(e))
            _LOGGER.error("'{}' download incomplete".format(bundle_name))
            return asset, None
        else:
            _LOGGER.info("Download complete: {}".format(filepath))

        new_checksum = checksum(filepath)
        old_checksum = archive_data and archive_data.get(CFG_CHECKSUM_KEY)
        if old_checksum and new_checksum != old_checksum:
            _LOGGER.error(
                "Checksum mismatch: ({}, {})".format(new_checksum, old_checksum))
            return asset, None
        else:
            _LOGGER.debug("Matched checksum: '{}'".format(old_checksum))

        result = archive_data[CFG_ASSET_PATH_KEY]

        # successfully downloaded and moved tarball; untar it
        if unpack and filepath.endswith(".tar") or filepath.endswith(".tgz"):
            _LOGGER.info("Extracting: {}".format(bundle_name))
            _untar(filepath, outdir)
            _LOGGER.debug("Unpacked archive into: {}".format(outdir))
        _LOGGER.info("Writing genome config file: {}".format(genome_config))
        self.update_assets(genome, asset, {CFG_ASSET_PATH_KEY: result})
        self.write(genome_config)
        return asset, result

    def update_assets(self, genome, asset=None, data=None):
        """
        Updates the genomes in RefGenConf object at any level.
        If a requested genome-asset mapping is missing, it will be created

        :param str genome: genome to be added/updated
        :param str asset: asset to be added/updated
        :param Mapping data: data to be added/updated
        :return RefGenConf: updated object
        """
        if _check_insert_data(genome, str, "genome"):
            self[CFG_GENOMES_KEY].setdefault(genome, PXAM({CFG_ASSETS_KEY: PXAM()}))
            if _check_insert_data(asset, str, "asset"):
                self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY].setdefault(asset, PXAM())
                if _check_insert_data(data, Mapping, "data"):
                    self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset].update(data)
        return self

    def remove_assets(self, genome, assets):
        """
        Remove assets. If no more assets are defined for the selected genome after asset removal,
        the genome key will be removed as well

        :param str genome: genome to be removed
        :param str | list[str] assets: assets to be removed
        :raise TypeError: if genome argument type is not a list or str
        :return RefGenConf: updated object
        """
        assets = [assets] if isinstance(assets, str) else assets
        if not isinstance(assets, list):
            raise TypeError("assets arg has to be a str or list[str]")
        for asset in assets:
            if _check_insert_data(genome, str, "genome"):
                self[CFG_GENOMES_KEY].setdefault(genome, PXAM({CFG_ASSETS_KEY: PXAM()}))
                if _check_insert_data(asset, str, "asset"):
                    del self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset]
        if len(self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY]) == 0:
            del self[CFG_GENOMES_KEY][genome]
        return self

    def update_genomes(self, genome, data=None):
        """
        Updates the genomes in RefGenConf object at any level.
        If a requested genome is missing, it will be added

        :param str genome: genome to be added/updated
        :param Mapping data: data to be added/updated
        :return RefGenConf: updated object
        """
        if _check_insert_data(genome, str, "genome"):
            self[CFG_GENOMES_KEY].setdefault(genome, PXAM({CFG_ASSETS_KEY: PXAM()}))
            if _check_insert_data(data, Mapping, "data"):
                self[CFG_GENOMES_KEY][genome].update(data)
        return self

    def _invert_genomes(self, order=None):
        """ Map each asset type/kind/name to a collection of assemblies.

        A configuration file encodes assets by genome, but in some use cases
        it's helpful to invert the direction of this mapping. The value of the
        asset key/name may differ by genome, so that information is
        necessarily lost in this inversion, but we can collect genome IDs by
        asset ID.

        :param order: function(str) -> object how to key genome IDs and asset
            names for sort
        :return OrderedDict[str, Iterable[str]] binding between asset kind/key/name
            and collection of reference genome assembly names for which the
            asset type is available
        """
        genomes = {}
        for g, am in self[CFG_GENOMES_KEY].items():
            for a in am[CFG_ASSETS_KEY].keys():
                genomes.setdefault(a, []).append(g)
        assets = sorted(genomes.keys(), key=order)
        return OrderedDict([(a, sorted(genomes[a], key=order)) for a in assets])


class DownloadProgressBar(tqdm):
    """
    from: https://github.com/tqdm/tqdm#hooks-and-callbacks
    """
    def update_to(self, b=1, bsize=1, tsize=None):
        """
        Update the progress bar

        :param int b: number of blocks transferred so far
        :param int bsize: size of each block (in tqdm units)
        :param int tsize: total size (in tqdm units)
        """
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def _download_json(url):
    """
    Safely connect to the provided API endpoint and download JSON data.

    :param str url: server API endpoint
    :return dict: served data
    """
    import json, requests
    _LOGGER.debug("Downloading JSON data; querying URL: '{}'".format(url))
    resp = requests.get(url)
    if resp.ok:
        return json.loads(resp.content.decode())
    raise DownloadJsonError(resp)


def _download_url_progress(url, output_path, name):
    """
    Download asset at given URL to given filepath, show progress along the way.

    :param str url: server API endpoint
    :param str output_path: path to file to save download
    :param str name: name to display in front of the progress bar
    """
    with DownloadProgressBar(unit_scale=True, desc=name, unit="B") as dpb:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=dpb.update_to)


def _genome_asset_path(genomes, gname, aname):
    """
    Retrieve the raw path value for a particular asset for a particular genome.

    :param Mapping[str, Mapping[str, Mapping[str, object]]] genomes: nested
        collection of key-value pairs, keyed at top level on genome ID, then by
        asset name, then by asset attribute
    :param str gname: top level key to query -- genome ID, e.g. mm10
    :param str aname: second-level key to query -- asset name, e.g. chrom_sizes
    :return str: raw path value for a particular asset for a particular genome
    :raise MissingGenomeError: if the given key-value pair collection does not
        contain as a top-level key the given genome ID
    :raise MissingAssetError: if the given key-value pair colelction does
        contain the given genome ID, but that key's mapping doesn't contain
        the given asset name as a key
    :raise GenomeConfigFormatError: if it's discovered during the query that
        the structure of the given genomes mapping suggests that it was
        parsd from an improperly formatted/structured genome config gile.
    """
    try:
        genome = genomes[gname]
    except KeyError:
        raise MissingGenomeError("Your genomes do not include {}".format(gname))
    try:
        asset_data = genome[CFG_ASSETS_KEY][aname]
    except KeyError:
        raise MissingAssetError(
            "Genome '{}' exists, but index '{}' is missing".format(gname, aname))
    if isinstance(asset_data, str):
        raise GenomeConfigFormatError(
            "For genome '{}' asset '{}' has raw string value ('{}') "
            "rather than mapping.".format(genome, aname, asset_data))
    try:
        return asset_data[CFG_ASSET_PATH_KEY]
    except KeyError:
        raise GenomeConfigFormatError(
            "For genome '{}' asset '{}' exists but configuration lacks a "
            "'{}' entry.".format(genome, aname, CFG_ASSET_PATH_KEY))


def _is_large_archive(size):
    """
    Determines if the file is large based on a string formatted as follows: 15.4GB

    :param str size:  size string
    :return bool: the decision
    """
    _LOGGER.debug("Checking archive size: '{}'".format(size))
    return size.endswith("TB") or (size.endswith("GB") and float("".join(c for c in size if c in '0123456789.')) > 5)


def _list_remote(url, genome, order=None):
    """
    List genomes and assets available remotely.

    :param url: location or ref genome config data
    :param order: function(str) -> object how to key genome IDs and asset
        names for sort
    :return str, str: text reps of remotely available genomes and assets
    """
    genomes_data = _read_remote_data(url)
    refgens = _select_genomes(sorted(genomes_data.keys(), key=order), genome)
    asset_texts = [_make_genome_assets_line(g, genomes_data[g], order=order) for g in refgens]
    return ", ".join(refgens), "\n".join(asset_texts)


def _make_genome_assets_line(
        gen, assets, offset_text="  ", genome_assets_delim=": ", asset_sep=", ", order=None):
    """
    Build a line of text for display of assets by genome

    :param str gen: reference assembly ID, e.g. hg38
    :param Iterable[str] assets: collection of asset names for the given genome
    :param str offset_text: prefix for the line, e.g. a kind of whitespace
    :param str genome_assets_delim: delimiter between a genome ID and text
        showing names of assets for that genome
    :param str asset_sep: delimiter between asset names
    :param order: function(str) -> object how to key asset names for sort
    :return str: text representation of a single assembly's name and assets
    """
    return offset_text + "{}{}{}".format(gen, genome_assets_delim, asset_sep.join(sorted(list(assets), key=order)))


def _read_remote_data(url):
    """
    Read as JSON data from a URL request response.

    :param str url: data request
    :return dict: JSON parsed from the response from given URL request
    """
    import json
    with urllib.request.urlopen(url) as response:
        encoding = response.info().get_content_charset('utf8')
        return json.loads(response.read().decode(encoding))


def _untar(src, dst):
    """
    Unpack a path to a target folder.

    :param str src: path to unpack
    :param str dst: path to output folder
    """
    import tarfile
    with tarfile.open(src) as tf:
        tf.extractall(path=dst)


def _check_insert_data(obj, datatype, name):
    """ Checks validity of an object """
    if obj is None:
        return False
    if not isinstance(obj, datatype):
        raise TypeError("{} must be {}; got {}".format(
            name, datatype.__name__, type(obj).__name__))
    return True


def _select_genomes(genomes, genome=None):
    """
    Safely select a subset of genomes

    :param list[str] | str genome: genomes that the assets should be found for
    :raise TypeError: if genome argument type is not a list or str
    :return list: selected subset of genomes
    """
    if genome:
        if isinstance(genome, str):
            genome = [genome]
        elif not isinstance(genome, list) or not all(isinstance(i, str) for i in genome):
            raise TypeError("genome has to be a list[str] or a str, got '{}'".format(genome.__class__.__name__))
    return genomes if (genome is None or not all(x in genomes for x in genome)) else genome