#!/usr/bin/env python

from __future__ import annotations

import itertools
import json
import logging
import os
import shutil
import signal
import sys
import urllib.request
import warnings
from collections.abc import Callable, Mapping
from functools import partial
from importlib.metadata import entry_points
from inspect import getfullargspec as finspect
from tempfile import TemporaryDirectory
from types import FrameType
from typing import Any
from urllib.error import ContentTooShortError, HTTPError

import yacman
from attmap import PathExAttMap as PXAM
from tqdm import tqdm
from ubiquerg import checksum, is_url, is_writable, query_yes_no, untar
from ubiquerg import parse_registry_path as prp

from .const import *
from .exceptions import *
from .helpers import (
    asciify_json_dict,
    block_iter_repr,
    get_dir_digest,
    select_genome_config,
    unbound_env_vars,
)

_LOGGER = logging.getLogger(__name__)

__all__ = ["_RefGenConfV03"]


def _handle_sigint(filepath: str) -> Callable[[int, FrameType | None], None]:
    def handle(sig: int, frame: FrameType | None) -> None:
        _LOGGER.warning("\nThe download was interrupted: {}".format(filepath))
        try:
            os.remove(filepath)
        except OSError:
            _LOGGER.debug("'{}' not found, can't remove".format(filepath))
        else:
            _LOGGER.info("Incomplete file '{}' was removed".format(filepath))
        sys.exit(0)

    return handle


class _RefGenConfV03(yacman.YacAttMap):
    """A sort of oracle of available reference genome assembly assets."""

    def __init__(
        self,
        filepath: str | None = None,
        entries: str | Mapping | None = None,
        writable: bool = False,
        wait_max: int = 60,
        skip_read_lock: bool = False,
    ) -> None:
        """Create the config instance by with a filepath or key-value pairs.

        Args:
            filepath: A path to the YAML file to read.
            entries: Config filepath or collection of key-value pairs.
            writable: Whether to create the object with write capabilities.
            wait_max: How long to wait for creating an object when the
                file that data will be read from is locked.
            skip_read_lock: Whether the file should not be locked for
                reading when object is created in read only mode.

        Raises:
            refgenconf.MissingConfigDataError: If a required configuration
                item is missing.
            ValueError: If entries is given as a string and is not a file.
        """

        def _missing_key_msg(key: str, value: Any) -> None:
            _LOGGER.debug("Config lacks '{}' key. Setting to: {}".format(key, value))

        super(_RefGenConfV03, self).__init__(
            filepath=filepath,
            entries=entries,
            writable=writable,
            wait_max=wait_max,
            skip_read_lock=skip_read_lock,
        )
        genomes = self.setdefault(CFG_GENOMES_KEY, PXAM())
        if not isinstance(genomes, PXAM):
            if genomes:
                _LOGGER.warning(
                    "'{k}' value is a {t_old}, not a {t_new}; setting to empty {t_new}".format(
                        k=CFG_GENOMES_KEY,
                        t_old=type(genomes).__name__,
                        t_new=PXAM.__name__,
                    )
                )
            self[CFG_GENOMES_KEY] = PXAM()
        if CFG_FOLDER_KEY not in self:
            self[CFG_FOLDER_KEY] = (
                os.path.dirname(entries) if isinstance(entries, str) else os.getcwd()
            )
            _missing_key_msg(CFG_FOLDER_KEY, self[CFG_FOLDER_KEY])
        try:
            version = self[CFG_VERSION_KEY]
        except KeyError:
            _missing_key_msg(CFG_VERSION_KEY, REQ_CFG_VERSION)
            self[CFG_VERSION_KEY] = REQ_CFG_VERSION
        else:
            try:
                version = float(version)
            except ValueError:
                _LOGGER.warning(
                    "Cannot parse config version as numeric: {}".format(version)
                )
            else:
                if version < 0.3:
                    msg = (
                        "This genome config (v{}) is not compliant with v{} standards."
                        " To use it, please downgrade refgenie: "
                        "'pip install refgenie=={}'.".format(
                            self[CFG_VERSION_KEY],
                            str(REQ_CFG_VERSION),
                            REFGENIE_BY_CFG[str(version)],
                        )
                    )
                    raise ConfigNotCompliantError(msg)
                else:
                    _LOGGER.debug("Config version is compliant: {}".format(version))
        if CFG_SERVERS_KEY not in self and CFG_SERVER_KEY in self:
            # backwards compatibility after server config key change
            self[CFG_SERVERS_KEY] = self[CFG_SERVER_KEY]
            del self[CFG_SERVER_KEY]
            _LOGGER.debug(
                "Moved servers list from '{}' to '{}'".format(
                    CFG_SERVER_KEY, CFG_SERVERS_KEY
                )
            )
        try:
            if isinstance(self[CFG_SERVERS_KEY], list):
                tmp_list = [
                    server_url.rstrip("/") for server_url in self[CFG_SERVERS_KEY]
                ]
                self[CFG_SERVERS_KEY] = tmp_list
            else:  # Logic in pull_asset expects a list, even for a single server
                self[CFG_SERVERS_KEY] = self[CFG_SERVERS_KEY].rstrip("/")
                self[CFG_SERVERS_KEY] = [self[CFG_SERVERS_KEY]]
        except KeyError:
            _missing_key_msg(CFG_SERVERS_KEY, str([DEFAULT_SERVER]))
            self[CFG_SERVERS_KEY] = [DEFAULT_SERVER]

    def __bool__(self) -> bool:
        minkeys = set(self.keys()) == set(RGC_REQ_KEYS)
        return not minkeys or bool(self[CFG_GENOMES_KEY])

    __nonzero__ = __bool__

    @property
    def plugins(self) -> dict[str, dict[str, Any]]:
        """Plugins registered by entry points in the current Python env.

        Returns:
            Dict whose keys are names of all possible hooks and values are
            dicts mapping registered function names to their values.
        """
        return {
            h: {ep.name: ep.load() for ep in entry_points(group="refgenie.hooks." + h)}
            for h in HOOKS
        }

    @property
    def file_path(self) -> str | None:
        """Path to the genome configuration file.

        Returns:
            Path to the genome configuration file.
        """
        return self[yacman.IK][yacman.FILEPATH_KEY]

    def initialize_config_file(self, filepath: str | None = None) -> str:
        """Initialize genome configuration file on disk.

        Args:
            filepath: A valid path where the configuration file should
                be initialized.

        Returns:
            The filepath the file was initialized at.

        Raises:
            OSError: If the file could not be initialized due to
                insufficient permissions or pre-existence.
            TypeError: If no valid filepath can be determined.
        """

        def _write_fail_err(reason: str) -> None:
            raise OSError("Can't initialize, {}: {} ".format(reason, filepath))

        filepath = select_genome_config(filepath, check_exist=False)
        if not isinstance(filepath, str):
            raise TypeError(
                "Could not determine a valid path to "
                "initialize a configuration file: {}".format(str(filepath))
            )
        if os.path.exists(filepath):
            _write_fail_err("file exists")
        if not is_writable(filepath, check_exist=False):
            _write_fail_err("insufficient permissions")
        self.make_writable(filepath)
        self.write()
        self.make_readonly()
        _LOGGER.info("Initialized genome configuration file: {}".format(filepath))
        return filepath

    def list(
        self,
        genome: str | list[str] | None = None,
        order: Callable[..., Any] | None = None,
        include_tags: bool = False,
    ) -> dict[str, list[str]]:
        """List local assets; map each namespace to a list of available asset names.

        Args:
            genome: Genomes that the assets should be found for.
            order: How to key genome IDs for sort.
            include_tags: Whether asset tags should be included in the
                returned dict.

        Returns:
            Mapping from assembly name to collection of available asset
            names.
        """
        self.run_plugins(PRE_LIST_HOOK)
        refgens = _select_genomes(
            sorted(self[CFG_GENOMES_KEY].keys(), key=order), genome
        )
        if include_tags:
            self.run_plugins(POST_LIST_HOOK)
            return dict(
                [
                    (
                        g,
                        sorted(
                            _make_asset_tags_product(
                                self[CFG_GENOMES_KEY][g][CFG_ASSETS_KEY], ":"
                            ),
                            key=order,
                        ),
                    )
                    for g in refgens
                ]
            )
        self.run_plugins(POST_LIST_HOOK)
        return dict(
            [
                (
                    g,
                    sorted(
                        list(self[CFG_GENOMES_KEY][g][CFG_ASSETS_KEY].keys()), key=order
                    ),
                )
                for g in refgens
            ]
        )

    def assets_str(
        self,
        offset_text: str = "  ",
        asset_sep: str = ", ",
        genome_assets_delim: str = "/ ",
        genome: str | list[str] | None = None,
        order: Callable[..., Any] | None = None,
    ) -> str:
        """Create a block of text representing genome-to-asset mapping.

        Args:
            offset_text: Text that begins each line of the text
                representation that's produced.
            asset_sep: The delimiter between names of types of assets,
                within each genome line.
            genome_assets_delim: The delimiter to place between reference
                genome assembly name and its list of asset names.
            genome: Genomes that the assets should be found for.
            order: How to key genome IDs and asset names for sort.

        Returns:
            Text representing genome-to-asset mapping.
        """
        refgens = _select_genomes(
            sorted(self[CFG_GENOMES_KEY].keys(), key=order), genome
        )
        make_line = partial(
            _make_genome_assets_line,
            offset_text=offset_text,
            genome_assets_delim=genome_assets_delim,
            asset_sep=asset_sep,
            order=order,
        )
        return "\n".join(
            [make_line(g, self[CFG_GENOMES_KEY][g][CFG_ASSETS_KEY]) for g in refgens]
        )

    def add(
        self,
        path: str,
        genome: str,
        asset: str,
        tag: str | None = None,
        seek_keys: dict[str, str] | None = None,
        force: bool = False,
    ) -> bool:
        """Add an external asset to the config.

        Args:
            path: A path to the asset to add; must exist and be relative
                to the genome_folder.
            genome: Genome name.
            asset: Asset name.
            tag: Tag name.
            seek_keys: Seek keys to add.
            force: Whether to force existing asset overwrite.
        """
        tag = tag or self.get_default_tag(genome, asset)
        abspath = os.path.join(self[CFG_FOLDER_KEY], path)
        remove = False
        if not os.path.exists(abspath) or not os.path.isabs(abspath):
            raise OSError(
                "Provided path must exist and be relative to the"
                " genome_folder: {}".format(self[CFG_FOLDER_KEY])
            )
        try:
            _assert_gat_exists(self[CFG_GENOMES_KEY], genome, asset, tag)
        except Exception:
            pass
        else:
            if not force and not query_yes_no(
                "'{}/{}:{}' exists. Do you want to overwrite?".format(
                    genome, asset, tag
                )
            ):
                _LOGGER.info("Aborted by a user, asset no added")
                return False
            remove = True
            _LOGGER.info("Will remove existing to overwrite")
        tag_data = {
            CFG_ASSET_PATH_KEY: path,
            CFG_ASSET_CHECKSUM_KEY: get_dir_digest(path) or "",
        }
        msg = "Added asset: {}/{}:{} {}".format(
            genome,
            asset,
            tag,
            "" if not seek_keys else "with seek keys: {}".format(seek_keys),
        )
        if not self.file_path:
            if remove:
                self.cfg_remove_assets(genome, asset, tag)
            self.update_tags(genome, asset, tag, tag_data)
            self.update_seek_keys(genome, asset, tag, seek_keys or {asset: "."})
            self.set_default_pointer(genome, asset, tag)
            _LOGGER.info(msg)
            return True
        with self as rgc:
            if remove:
                rgc.cfg_remove_assets(genome, asset, tag)
            rgc.update_tags(genome, asset, tag, tag_data)
            rgc.update_seek_keys(genome, asset, tag, seek_keys or {asset: "."})
            rgc.set_default_pointer(genome, asset, tag)
            _LOGGER.info(msg)
            return True

    def filepath(
        self, genome: str, asset: str, tag: str, ext: str = ".tgz", dir: bool = False
    ) -> str:
        """Determine path to a particular asset for a particular genome.

        Args:
            genome: Reference genome ID.
            asset: Asset name.
            tag: Tag name.
            ext: File extension.
            dir: Whether to return the enclosing directory instead of
                the file.

        Returns:
            Path to asset for given genome and asset kind/name.
        """
        tag_dir = os.path.join(self[CFG_FOLDER_KEY], genome, asset, tag)
        return os.path.join(tag_dir, asset + "__" + tag + ext) if not dir else tag_dir

    def genomes_list(self, order: Callable[..., Any] | None = None) -> list[str]:
        """Get a list of this configuration's reference genome assembly IDs.

        Returns:
            List of this configuration's reference genome assembly IDs.
        """
        return sorted(list(self[CFG_GENOMES_KEY].keys()), key=order)

    def genomes_str(self, order: Callable[..., Any] | None = None) -> str:
        """Get as single string this configuration's reference genome assembly IDs.

        Args:
            order: How to key genome IDs for sort.

        Returns:
            Single string that lists this configuration's known
            reference genome assembly IDs.
        """
        return ", ".join(self.genomes_list(order))

    def seek(
        self,
        genome_name: str,
        asset_name: str,
        tag_name: str | None = None,
        seek_key: str | None = None,
        strict_exists: bool | None = None,
        enclosing_dir: bool = False,
        check_exist: Callable[[str], bool] = lambda p: os.path.exists(p) or is_url(p),
    ) -> str:
        """Seek path to a specified genome-asset-tag.

        Args:
            genome_name: Name of a reference genome assembly of interest.
            asset_name: Name of the particular asset to fetch.
            tag_name: Name of the particular asset tag to fetch.
            seek_key: Name of the particular subasset to fetch.
            strict_exists: How to handle case in which path doesn't
                exist; True to raise IOError, False to raise
                RuntimeWarning, and None to do nothing at all.
                Default: None (do not check).
            enclosing_dir: Whether a path to the entire enclosing
                directory should be returned, e.g. for a fasta asset
                that has 3 seek_keys pointing to 3 files in an asset
                dir, that asset dir is returned.
            check_exist: How to check for asset/path existence.

        Returns:
            Path to the asset.

        Raises:
            TypeError: If the existence check is not a one-arg function.
            refgenconf.MissingGenomeError: If the named assembly isn't
                known to this configuration instance.
            refgenconf.MissingAssetError: If the named assembly is known
                to this configuration instance, but the requested asset
                is unknown.
        """
        tag_name = tag_name or self.get_default_tag(genome_name, asset_name)
        _LOGGER.debug(
            "getting asset: '{}/{}.{}:{}'".format(
                genome_name, asset_name, seek_key, tag_name
            )
        )
        if not callable(check_exist) or len(finspect(check_exist).args) != 1:
            raise TypeError("Asset existence check must be a one-arg function.")
        # 3 'path' key options supported
        # option1: absolute path
        # get just the saute path value from the config
        path_val = _genome_asset_path(
            self[CFG_GENOMES_KEY],
            genome_name,
            asset_name,
            tag_name,
            enclosing_dir=True,
            no_tag=True,
            seek_key=None,
        )
        _LOGGER.debug("Trying absolute path: {}".format(path_val))
        if seek_key:
            path = os.path.join(path_val, seek_key)
        else:
            path = path_val
        if os.path.isabs(path) and check_exist(path):
            return path
        # option2: relative to genome_folder/{genome} (default, canonical)
        path = _genome_asset_path(
            self[CFG_GENOMES_KEY],
            genome_name,
            asset_name,
            tag_name,
            seek_key,
            enclosing_dir,
        )
        fullpath = os.path.join(self[CFG_FOLDER_KEY], genome_name, path)
        _LOGGER.debug(
            "Trying relative to genome_folder/genome ({}/{}): {}".format(
                self[CFG_FOLDER_KEY], genome_name, fullpath
            )
        )
        if check_exist(fullpath):
            return fullpath
        # option3: relative to the genome_folder (if option2 does not exist)
        gf_relpath = os.path.join(
            self[CFG_FOLDER_KEY],
            _genome_asset_path(
                self[CFG_GENOMES_KEY],
                genome_name,
                asset_name,
                tag_name,
                seek_key,
                enclosing_dir,
                no_tag=True,
            ),
        )
        _LOGGER.debug(
            "Trying path relative to genome_folder ({}): {}".format(
                self[CFG_FOLDER_KEY], gf_relpath
            )
        )
        if check_exist(gf_relpath):
            return gf_relpath

        msg = "For genome '{}' the asset '{}.{}:{}' doesn't exist; tried: {}".format(
            genome_name,
            asset_name,
            seek_key,
            tag_name,
            ",".join([path, gf_relpath, fullpath]),
        )
        # return option2 if existence not enforced
        if strict_exists is None:
            _LOGGER.debug(msg)
        elif strict_exists is True:
            raise OSError(msg)
        else:
            warnings.warn(msg, RuntimeWarning)
        return fullpath

    def get_default_tag(
        self, genome: str, asset: str, use_existing: bool = True
    ) -> str:
        """Determine the asset tag to use as default.

        The one indicated by the 'default_tag' key in the asset section is
        returned. If no 'default_tag' key is found, by default the first listed
        tag is returned with a RuntimeWarning. This behavior can be turned off
        with use_existing=False.

        Args:
            genome: Name of a reference genome assembly of interest.
            asset: Name of the particular asset of interest.
            use_existing: Whether the first tag in the config should be
                returned in case there is no default tag defined for an
                asset.

        Returns:
            Name of the tag to use as the default one.
        """
        try:
            _assert_gat_exists(self[CFG_GENOMES_KEY], genome, asset)
        except RefgenconfError:
            _LOGGER.info(
                "Using '{}' as the default tag for '{}/{}'".format(
                    DEFAULT_TAG, genome, asset
                )
            )
            return DEFAULT_TAG
        try:
            return self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][
                CFG_ASSET_DEFAULT_TAG_KEY
            ]
        except KeyError:
            alt = (
                self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][
                    CFG_ASSET_TAGS_KEY
                ].keys()[0]
                if use_existing
                else DEFAULT_TAG
            )
            if isinstance(alt, str):
                if alt != DEFAULT_TAG:
                    warnings.warn(
                        "Could not find the '{}' key for asset '{}/{}'. "
                        "Used the first one in the config instead: '{}'. "
                        "Make sure it does not corrupt your workflow.".format(
                            CFG_ASSET_DEFAULT_TAG_KEY, genome, asset, alt
                        ),
                        RuntimeWarning,
                    )
                else:
                    warnings.warn(
                        "Could not find the '{}' key for asset '{}/{}'. "
                        "Returning '{}' instead. Make sure it does not corrupt your workflow.".format(
                            CFG_ASSET_DEFAULT_TAG_KEY, genome, asset, alt
                        ),
                        RuntimeWarning,
                    )
                return alt
        except TypeError:
            _raise_not_mapping(
                self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset], "Asset section "
            )

    def set_default_pointer(
        self, genome: str, asset: str, tag: str, force: bool = False
    ) -> None:
        """Point to the selected tag by default.

        Args:
            genome: Name of a reference genome assembly of interest.
            asset: Name of the particular asset of interest.
            tag: Name of the particular asset tag to point to by
                default.
            force: Whether the default tag change should be forced
                (even if it exists).
        """
        _assert_gat_exists(self[CFG_GENOMES_KEY], genome, asset, tag)
        if (
            CFG_ASSET_DEFAULT_TAG_KEY
            not in self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset]
            or len(
                self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][
                    CFG_ASSET_DEFAULT_TAG_KEY
                ]
            )
            == 0
            or force
        ):
            self.update_assets(genome, asset, {CFG_ASSET_DEFAULT_TAG_KEY: tag})
            _LOGGER.info(
                "Default tag for '{}/{}' set to: {}".format(genome, asset, tag)
            )

    def list_assets_by_genome(
        self,
        genome: str | None = None,
        order: Callable[..., Any] | None = None,
        include_tags: bool = False,
    ) -> list[str] | dict[str, list[str]]:
        """List types/names of assets that are available for one--or all--genomes.

        Args:
            genome: Reference genome assembly ID, optional; if omitted,
                the full mapping from genome to asset names.
            order: How to key genome IDs and asset names for sort.
            include_tags: Whether asset tags should be included in the
                returned dict.

        Returns:
            Collection of asset type names available for particular
            reference assembly if one is provided, else the full mapping
            between assembly ID and collection of available asset type
            names.
        """
        return (
            self.list(genome, order, include_tags=include_tags)[genome]
            if genome is not None
            else self.list(order, include_tags=include_tags)
        )

    def list_genomes_by_asset(
        self, asset: str | None = None, order: Callable[..., Any] | None = None
    ) -> dict[str, list[str]] | list[str]:
        """List assemblies for which a particular asset is available.

        Args:
            asset: Name of type of asset of interest, optional.
            order: How to key genome IDs and asset names for sort.

        Returns:
            Collection of assemblies for which the given asset is
            available; if asset argument is omitted, the full mapping
            from name of asset type to collection of assembly names for
            which the asset key is available will be returned.
        """
        return (
            self._invert_genomes(order)
            if not asset
            else sorted(
                [
                    g
                    for g, data in self[CFG_GENOMES_KEY].items()
                    if asset in data.get(CFG_ASSETS_KEY)
                ],
                key=order,
            )
        )

    def get_local_data_str(
        self,
        genome: str | list[str] | None = None,
        order: Callable[..., Any] | None = None,
    ) -> tuple[str, str]:
        """List locally available reference genome IDs and assets by ID.

        Args:
            genome: Genomes that the assets should be found for.
            order: How to key genome IDs and asset names for sort.

        Returns:
            Text representations of locally available genomes and assets.
        """
        exceptions = []
        if genome is not None:
            if isinstance(genome, str):
                genome = [genome]
            for g in genome:
                try:
                    _assert_gat_exists(self[CFG_GENOMES_KEY], g)
                except MissingGenomeError as e:
                    exceptions.append(e)
            if exceptions:
                raise MissingGenomeError(", ".join(map(str, exceptions)))
        genomes_str = (
            self.genomes_str(order=order)
            if genome is None
            else ", ".join(
                _select_genomes(sorted(self[CFG_GENOMES_KEY].keys(), key=order), genome)
            )
        )
        return genomes_str, self.assets_str(genome=genome, order=order)

    def get_remote_data_str(
        self,
        genome: str | list[str] | None = None,
        order: Callable[..., Any] | None = None,
        get_url: Callable[[str, str], str] = lambda server, id: construct_request_url(
            server, id
        ),
    ) -> dict[str, Any]:
        """List genomes and assets available remotely.

        Args:
            genome: Genomes that the assets should be found for.
            order: How to key genome IDs and asset names for sort.
            get_url: How to determine URL request, given RefGenConf
                instance.

        Returns:
            Text representations of remotely available genomes and
            assets.
        """
        warnings.warn(
            "Please use listr method instead; get_remote_data_str will be "
            "removed in the next release.",
            category=DeprecationWarning,
        )
        return self.listr(genome, order, get_url)

    def listr(
        self,
        genome: str | list[str] | None = None,
        order: Callable[..., Any] | None = None,
        get_url: Callable[[str, str], str] = lambda server, id: construct_request_url(
            server, id
        ),
        as_str: bool = False,
    ) -> dict[str, Any]:
        """List genomes and assets available remotely on all servers the object subscribes to.

        Args:
            genome: Genomes that the assets should be found for.
            order: How to key genome IDs and asset names for sort.
            get_url: How to determine URL request, given RefGenConf
                instance.
            as_str: Whether to return the data as a string.

        Returns:
            Remotely available genomes and assets keyed by genome keyed
            by source server endpoint.
        """
        data_by_server = {}
        for url in self[CFG_SERVERS_KEY]:
            url = get_url(url, API_ID_ASSETS)
            data_by_server[url] = _list_remote(url, genome, order, as_str=as_str)
        return data_by_server

    def tag(
        self, genome: str, asset: str, tag: str, new_tag: str, files: bool = True
    ) -> None:
        """Retag the asset selected by the tag with the new_tag.

        Prompts if default already exists and overrides upon confirmation.
        This method does not override the original asset entry in the RefGenConf
        object. It creates its copy and tags it with the new_tag.
        Additionally, if the retagged asset has any children their parent will
        be retagged as new_tag that was introduced upon this method execution.
        By default, the files on disk will be also renamed to reflect the
        genome configuration file changes.

        Args:
            genome: Name of a reference genome assembly of interest.
            asset: Name of particular asset of interest.
            tag: Name of the tag that identifies the asset of interest.
            new_tag: Name of the new tag.
            files: Whether the asset files on disk should be renamed.

        Returns:
            A logical indicating whether the tagging was successful.

        Raises:
            ValueError: When the original tag is not specified.
        """
        self.run_plugins(PRE_TAG_HOOK)
        ori_path = self.seek(genome, asset, tag, enclosing_dir=True, strict_exists=True)
        new_path = os.path.abspath(os.path.join(ori_path, os.pardir, new_tag))
        if self.file_path:
            with self as r:
                if not r.cfg_tag_asset(genome, asset, tag, new_tag):
                    sys.exit(0)
        else:
            if not self.cfg_tag_asset(genome, asset, tag, new_tag):
                sys.exit(0)
        if not files:
            self.run_plugins(POST_TAG_HOOK)
            return
        try:
            if os.path.exists(new_path):
                _remove(new_path)
            os.rename(ori_path, new_path)
        except FileNotFoundError:
            _LOGGER.warning(
                "Could not rename original asset tag directory '{}'"
                " to the new one '{}'".format(ori_path, new_path)
            )
        else:
            if self.file_path:
                with self as r:
                    r.cfg_remove_assets(genome, asset, tag, relationships=False)
            else:
                self.cfg_remove_assets(genome, asset, tag, relationships=False)
            _LOGGER.debug(
                "Asset '{}/{}' tagged with '{}' has been removed from"
                " the genome config".format(genome, asset, tag)
            )
            _LOGGER.debug(
                "Original asset has been moved from '{}' to '{}'".format(
                    ori_path, new_path
                )
            )
        self.run_plugins(POST_TAG_HOOK)

    def cfg_tag_asset(
        self, genome: str, asset: str, tag: str | None, new_tag: str
    ) -> bool | None:
        """Retag the asset selected by the tag with the new_tag.

        Prompts if default already exists and overrides upon confirmation.
        This method does not override the original asset entry in the RefGenConf
        object. It creates its copy and tags it with the new_tag. Additionally,
        if the retagged asset has any children their parent will be retagged as
        new_tag that was introduced upon this method execution.

        Args:
            genome: Name of a reference genome assembly of interest.
            asset: Name of particular asset of interest.
            tag: Name of the tag that identifies the asset of interest.
            new_tag: Name of the new tag.

        Returns:
            A logical indicating whether the tagging was successful.

        Raises:
            ValueError: When the original tag is not specified.
        """
        _assert_gat_exists(self[CFG_GENOMES_KEY], genome, asset, tag)
        asset_mapping = self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset]
        if tag is None:
            raise ValueError(
                "You must explicitly specify the tag of the asset "
                "you want to reassign. Currently defined "
                "tags for '{}/{}' are: {}".format(
                    genome, asset, ", ".join(get_asset_tags(asset_mapping))
                )
            )
        if new_tag in asset_mapping[CFG_ASSET_TAGS_KEY]:
            if not query_yes_no(
                "You already have a '{}' asset tagged as '{}', do you wish to override?".format(
                    asset, new_tag
                )
            ):
                _LOGGER.info("Tag action aborted by the user")
                return
        children = []
        parents = []
        if CFG_ASSET_CHILDREN_KEY in asset_mapping[CFG_ASSET_TAGS_KEY][tag]:
            children = asset_mapping[CFG_ASSET_TAGS_KEY][tag][CFG_ASSET_CHILDREN_KEY]
        if CFG_ASSET_PARENTS_KEY in asset_mapping[CFG_ASSET_TAGS_KEY][tag]:
            parents = asset_mapping[CFG_ASSET_TAGS_KEY][tag][CFG_ASSET_PARENTS_KEY]
        if len(children) > 0 or len(parents) > 0:
            if not query_yes_no(
                "The asset '{}/{}:{}' has {} children and {} parents. Refgenie will update the "
                "relationship data. Do you want to proceed?".format(
                    genome, asset, tag, len(children), len(parents)
                )
            ):
                _LOGGER.info("Tag action aborted by the user")
                return False
            # updates children's parents
            self._update_relatives_tags(
                genome, asset, tag, new_tag, children, update_children=False
            )
            # updates parents' children
            self._update_relatives_tags(
                genome, asset, tag, new_tag, parents, update_children=True
            )
        self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][CFG_ASSET_TAGS_KEY][
            new_tag
        ] = asset_mapping[CFG_ASSET_TAGS_KEY][tag]
        if (
            CFG_ASSET_DEFAULT_TAG_KEY in asset_mapping
            and asset_mapping[CFG_ASSET_DEFAULT_TAG_KEY] == tag
        ):
            self.set_default_pointer(genome, asset, new_tag, force=True)
        self.cfg_remove_assets(genome, asset, tag)
        return True

    def _update_relatives_tags(
        self,
        genome: str,
        asset: str,
        tag: str,
        new_tag: str,
        relatives: list[str],
        update_children: bool,
    ) -> None:
        """Update tags in the 'asset_parents' section in the list of children.

        Args:
            genome: Name of a reference genome assembly of interest.
            asset: Name of particular asset of interest.
            tag: Name of the tag that identifies the asset of interest.
            new_tag: Name of the new tag.
            relatives: Relatives to be updated. Format:
                ["asset_name:tag", "asset_name1:tag1"].
            update_children: Whether the children of the selected
                relatives should be updated.
        """
        relative_key = (
            CFG_ASSET_CHILDREN_KEY if update_children else CFG_ASSET_PARENTS_KEY
        )
        for r in relatives:
            _LOGGER.debug(
                "updating {} in '{}'".format(
                    "children" if update_children else "parents", r
                )
            )
            r_data = prp(r)
            try:
                self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][r_data["item"]][
                    CFG_ASSET_TAGS_KEY
                ][r_data["tag"]]
            except KeyError:
                _LOGGER.warning(
                    "The {} asset of '{}/{}' does not exist: {}".format(
                        "parent" if update_children else "child", genome, asset, r
                    )
                )
                continue
            updated_relatives = []
            if (
                relative_key
                in self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][r_data["item"]][
                    CFG_ASSET_TAGS_KEY
                ][r_data["tag"]]
            ):
                relatives = self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][
                    r_data["item"]
                ][CFG_ASSET_TAGS_KEY][r_data["tag"]][relative_key]
                for relative in relatives:
                    ori_relative_data = prp(relative)
                    if (
                        ori_relative_data["item"] == asset
                        and ori_relative_data["tag"] == tag
                    ):
                        ori_relative_data["tag"] = new_tag
                        updated_relatives.append(
                            "{}/{}:{}".format(genome, asset, new_tag)
                        )
                    else:
                        updated_relatives.append(
                            "{}/{}:{}".format(
                                ori_relative_data["namespace"],
                                ori_relative_data["item"],
                                ori_relative_data["tag"],
                            )
                        )
            self.update_relatives_assets(
                genome,
                r_data["item"],
                r_data["tag"],
                updated_relatives,
                update_children,
            )
            self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][r_data["item"]][
                CFG_ASSET_TAGS_KEY
            ][r_data["tag"]][relative_key] = updated_relatives

    def pull(
        self,
        genome: str,
        asset: str,
        tag: str | None,
        unpack: bool = True,
        force: bool | None = None,
        force_large: bool | None = None,
        size_cutoff: int | float = 10,
        get_json_url: Callable[[str, str], str] = lambda server,
        operation_id: construct_request_url(server, operation_id),
        build_signal_handler: Callable[[str], Callable[..., Any]] = _handle_sigint,
    ) -> tuple[list[str], dict[str, Any] | None, str | None] | None:
        """Download and possibly unpack one or more assets for a given ref gen.

        Args:
            genome: Name of a reference genome assembly of interest.
            asset: Name of particular asset to fetch.
            tag: Name of particular tag to fetch.
            unpack: Whether to unpack a tarball.
            force: How to handle case in which asset path already
                exists; None for prompt (on a per-asset basis), False to
                effectively auto-reply No to the prompt to replace
                existing file, and True to auto-reply Yes for existing
                asset replacement.
            force_large: How to handle case in which a large (> 5GB)
                asset is to be pulled; None for prompt (on a per-asset
                basis), False to effectively auto-reply No to the
                prompt, and True to auto-reply Yes.
            size_cutoff: Maximum archive file size to download with no
                prompt.
            get_json_url: How to build URL from genome server URL base,
                genome, and asset.
            build_signal_handler: How to create a signal handler to use
                during the download; the single argument to this
                function factory is the download filepath.

        Returns:
            A tuple of a list of genome, asset, tag names and a
            key-value pair with which genome config file should be
            updated if pull succeeds, else asset key and a null value.

        Raises:
            refgenconf.UnboundEnvironmentVariablesError: If genome
                folder path contains any env. var. that's unbound.
            refgenconf.RefGenConfError: If the object update is
                requested in a non-writable state.
        """
        self.run_plugins(PRE_PULL_HOOK)
        missing_vars = unbound_env_vars(self[CFG_FOLDER_KEY])
        if missing_vars:
            raise UnboundEnvironmentVariablesError(", ".join(missing_vars))

        def _null_return() -> tuple[list[str], None, None]:
            self.run_plugins(POST_PULL_HOOK)
            return gat, None, None

        def _raise_unpack_error() -> None:
            raise NotImplementedError(
                "Option to not extract tarballs is not yet supported."
            )

        num_servers = 0
        bad_servers = []
        no_asset_json = []
        if CFG_SERVERS_KEY not in self or self[CFG_SERVERS_KEY] is None:
            _LOGGER.error("You are not subscribed to any asset servers")
            return _null_return()
        for server_url in self[CFG_SERVERS_KEY]:
            num_servers += 1
            try:
                determined_tag = (
                    _download_json(
                        get_json_url(server_url, API_ID_DEFAULT_TAG).format(
                            genome=genome, asset=asset
                        )
                    )
                    if tag is None
                    else tag
                )
            except DownloadJsonError:
                _LOGGER.warning("Could not retrieve JSON from: {}".format(server_url))
                bad_servers.append(server_url)
                continue
            else:
                determined_tag = str(determined_tag)
                _LOGGER.debug("Determined tag: {}".format(determined_tag))
                unpack or _raise_unpack_error()
            gat = [genome, asset, determined_tag]
            url_asset_attrs = get_json_url(server_url, API_ID_ASSET_ATTRS).format(
                genome=genome, asset=asset
            )
            url_genome_attrs = get_json_url(server_url, API_ID_GENOME_ATTRS).format(
                genome=genome
            )
            url_archive = get_json_url(server_url, API_ID_ARCHIVE).format(
                genome=genome, asset=asset
            )

            try:
                archive_data = _download_json(
                    url_asset_attrs, params={"tag": determined_tag}
                )
            except DownloadJsonError:
                no_asset_json.append(server_url)
                if num_servers == len(self[CFG_SERVERS_KEY]):
                    _LOGGER.error(
                        "Asset '{}/{}:{}' not available on any of the following servers: {}".format(
                            genome,
                            asset,
                            determined_tag,
                            ", ".join(self[CFG_SERVERS_KEY]),
                        )
                    )
                    return _null_return()
                continue
            else:
                _LOGGER.debug("Determined server URL: {}".format(server_url))
                genome_archive_data = _download_json(url_genome_attrs)

            if sys.version_info[0] == 2:
                archive_data = asciify_json_dict(archive_data)

            # local directory that the asset data will be stored in
            tag_dir = os.path.dirname(self.filepath(*gat))
            # local directory the downloaded archive will be temporarily saved in
            genome_dir_path = os.path.join(self[CFG_FOLDER_KEY], genome)
            # local path to the temporarily saved archive
            filepath = os.path.join(
                genome_dir_path, asset + "__" + determined_tag + ".tgz"
            )
            # check if the genome/asset:tag exists and get request user decision
            if os.path.exists(tag_dir):

                def preserve() -> tuple[list[str], None, None]:
                    _LOGGER.info("Preserving existing: {}".format(tag_dir))
                    return _null_return()

                if force is False:
                    return preserve()
                elif force is None:
                    if not query_yes_no("Replace existing ({})?".format(tag_dir), "no"):
                        return preserve()
                    else:
                        _LOGGER.debug("Overwriting: {}".format(tag_dir))
                else:
                    _LOGGER.debug("Overwriting: {}".format(tag_dir))

            # check asset digests local-server match for each parent
            [
                self._chk_digest_if_avail(genome, x, server_url)
                for x in archive_data[CFG_ASSET_PARENTS_KEY]
                if CFG_ASSET_PARENTS_KEY in archive_data
            ]

            bundle_name = "{}/{}:{}".format(*gat)
            archsize = archive_data[CFG_ARCHIVE_SIZE_KEY]
            _LOGGER.debug("'{}' archive size: {}".format(bundle_name, archsize))

            if not force_large and _is_large_archive(archsize, size_cutoff):
                if force_large is False:
                    _LOGGER.info(
                        "Skipping pull of {}/{}:{}; size: {}".format(*gat, archsize)
                    )
                    return _null_return()
                if not query_yes_no(
                    "This archive exceeds the size cutoff ({} > {:.1f}GB) "
                    "Do you want to proceed?".format(archsize, size_cutoff)
                ):
                    _LOGGER.info(
                        "Skipping pull of {}/{}:{}; size: {}".format(*gat, archsize)
                    )
                    return _null_return()

            if not os.path.exists(genome_dir_path):
                _LOGGER.debug("Creating directory: {}".format(genome_dir_path))
                os.makedirs(genome_dir_path)

            # Download the file from `url` and save it locally under `filepath`:
            _LOGGER.info("Downloading URL: {}".format(url_archive))
            try:
                signal.signal(signal.SIGINT, build_signal_handler(filepath))
                _download_url_progress(
                    url_archive, filepath, bundle_name, params={"tag": determined_tag}
                )
            except HTTPError:
                _LOGGER.error(
                    "Asset archive '{}/{}:{}' is missing on the server: {s}".format(
                        *gat, s=server_url
                    )
                )
                if server_url == self[CFG_SERVERS_KEY][-1]:
                    # it this was the last server on the list, return
                    return _null_return()
                else:
                    _LOGGER.info("Trying next server")
                    # set the tag value back to what user requested
                    determined_tag = tag
                    continue
            except ConnectionRefusedError as e:
                _LOGGER.error(str(e))
                _LOGGER.error(
                    "Server {}/{} refused download. "
                    "Check your internet settings".format(server_url, API_VERSION_2)
                )
                return _null_return()
            except ContentTooShortError as e:
                _LOGGER.error(str(e))
                _LOGGER.error("'{}' download incomplete".format(bundle_name))
                return _null_return()
            else:
                _LOGGER.info("Download complete: {}".format(filepath))

            new_checksum = checksum(filepath)
            old_checksum = archive_data and archive_data.get(CFG_ARCHIVE_CHECKSUM_KEY)
            if old_checksum and new_checksum != old_checksum:
                _LOGGER.error(
                    "Downloaded archive ('{}') checksum mismatch: ({}, {})".format(
                        filepath, new_checksum, old_checksum
                    )
                )
                return _null_return()
            else:
                _LOGGER.debug("Matched checksum: '{}'".format(old_checksum))
            # successfully downloaded and moved tarball; untar it
            if unpack and filepath.endswith(".tgz"):
                _LOGGER.info(
                    "Extracting asset tarball and saving to: {}".format(tag_dir)
                )
                with TemporaryDirectory(dir=genome_dir_path) as tmpdir:
                    # here we suspect the unarchived asset to be an asset-named
                    # directory with the asset data inside and we transfer it
                    # to the tag-named subdirectory
                    untar(filepath, tmpdir)
                    if os.path.isdir(tag_dir):
                        shutil.rmtree(tag_dir)
                        _LOGGER.info("Removed existing directory: {}".format(tag_dir))
                    shutil.move(os.path.join(tmpdir, asset), tag_dir)
                if os.path.isfile(filepath):
                    os.remove(filepath)

            if self.file_path:
                with self as rgc:
                    [
                        rgc.chk_digest_update_child(
                            gat[0], x, "{}/{}:{}".format(*gat), server_url
                        )
                        for x in archive_data[CFG_ASSET_PARENTS_KEY]
                        if CFG_ASSET_PARENTS_KEY in archive_data
                    ]
                    rgc.update_tags(
                        *gat,
                        data={
                            attr: archive_data[attr]
                            for attr in ATTRS_COPY_PULL
                            if attr in archive_data
                        },
                    )
                    rgc.set_default_pointer(*gat)
                    rgc.update_genomes(genome=genome, data=genome_archive_data)
            else:
                [
                    self.chk_digest_update_child(
                        gat[0], x, "{}/{}:{}".format(*gat), server_url
                    )
                    for x in archive_data[CFG_ASSET_PARENTS_KEY]
                    if CFG_ASSET_PARENTS_KEY in archive_data
                ]
                self.update_tags(
                    *gat,
                    data={
                        attr: archive_data[attr]
                        for attr in ATTRS_COPY_PULL
                        if attr in archive_data
                    },
                )
                self.set_default_pointer(*gat)
                self.update_genomes(genome=genome, data=genome_archive_data)
            self.run_plugins(POST_PULL_HOOK)
            return gat, archive_data, server_url

    def remove_asset_from_relatives(self, genome: str, asset: str, tag: str) -> None:
        """Remove any relationship links associated with the selected asset.

        Args:
            genome: Genome to be removed from its relatives' relatives
                list.
            asset: Asset to be removed from its relatives' relatives
                list.
            tag: Tag to be removed from its relatives' relatives list.
        """
        to_remove = "{}/{}:{}".format(genome, asset, tag)
        for rel_type in CFG_ASSET_RELATIVES_KEYS:
            tmp = CFG_ASSET_RELATIVES_KEYS[
                len(CFG_ASSET_RELATIVES_KEYS)
                - 1
                - CFG_ASSET_RELATIVES_KEYS.index(rel_type)
            ]
            tag_data = self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][
                CFG_ASSET_TAGS_KEY
            ][tag]
            if rel_type not in tag_data:
                continue
            for rel in tag_data[rel_type]:
                parsed = prp(rel)
                _LOGGER.debug("Removing '{}' from '{}' {}".format(to_remove, rel, tmp))
                try:
                    self[CFG_GENOMES_KEY][parsed["namespace"] or genome][
                        CFG_ASSETS_KEY
                    ][parsed["item"]][CFG_ASSET_TAGS_KEY][parsed["tag"]][tmp].remove(
                        to_remove
                    )
                except (KeyError, ValueError):
                    pass

    def update_relatives_assets(
        self,
        genome: str,
        asset: str,
        tag: str | None = None,
        data: list[str] | None = None,
        children: bool = False,
    ) -> None:
        """Update the asset relatives of an asset.

        A convenience method which wraps the update assets and uses it to
        update the asset relatives of an asset.

        Args:
            genome: Genome to be added/updated.
            asset: Asset to be added/updated.
            tag: Tag to be added/updated.
            data: Asset parents to be added/updated.
            children: A logical indicating whether the relationship to
                be added is 'children'.

        Returns:
            Updated object.
        """
        tag = tag or self.get_default_tag(genome, asset)
        relationship = CFG_ASSET_CHILDREN_KEY if children else CFG_ASSET_PARENTS_KEY
        if _check_insert_data(data, list, "data"):
            # creates/asserts the genome/asset:tag combination
            self.update_tags(genome, asset, tag)
            self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][CFG_ASSET_TAGS_KEY][
                tag
            ].setdefault(relationship, list())
            self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][CFG_ASSET_TAGS_KEY][
                tag
            ][relationship] = _extend_unique(
                self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][
                    CFG_ASSET_TAGS_KEY
                ][tag][relationship],
                data,
            )

    def update_seek_keys(
        self,
        genome: str,
        asset: str,
        tag: str | None = None,
        keys: Mapping | None = None,
    ) -> _RefGenConfV03:
        """Update the seek keys for a tagged asset.

        A convenience method which wraps the update assets and uses it to
        update the seek keys for a tagged asset.

        Args:
            genome: Genome to be added/updated.
            asset: Asset to be added/updated.
            tag: Tag to be added/updated.
            keys: Seek keys to be added/updated.

        Returns:
            Updated object.
        """
        tag = tag or self.get_default_tag(genome, asset)
        if _check_insert_data(keys, Mapping, "keys"):
            self.update_tags(genome, asset, tag)
            asset = self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset]
            _safe_setdef(asset[CFG_ASSET_TAGS_KEY][tag], CFG_SEEK_KEYS_KEY, PXAM())
            asset[CFG_ASSET_TAGS_KEY][tag][CFG_SEEK_KEYS_KEY].update(keys)
        return self

    def update_tags(
        self,
        genome: str,
        asset: str | None = None,
        tag: str | None = None,
        data: Mapping | None = None,
    ) -> _RefGenConfV03:
        """Update the genomes in RefGenConf object at any level.

        If a requested genome-asset-tag mapping is missing, it will be created.

        Args:
            genome: Genome to be added/updated.
            asset: Asset to be added/updated.
            tag: Tag to be added/updated.
            data: Data to be added/updated.

        Returns:
            Updated object.
        """
        if _check_insert_data(genome, str, "genome"):
            _safe_setdef(self[CFG_GENOMES_KEY], genome, PXAM())
            if _check_insert_data(asset, str, "asset"):
                _safe_setdef(self[CFG_GENOMES_KEY][genome], CFG_ASSETS_KEY, PXAM())
                _safe_setdef(
                    self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY], asset, PXAM()
                )
                if _check_insert_data(tag, str, "tag"):
                    _safe_setdef(
                        self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset],
                        CFG_ASSET_TAGS_KEY,
                        PXAM(),
                    )
                    _safe_setdef(
                        self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][
                            CFG_ASSET_TAGS_KEY
                        ],
                        tag,
                        PXAM(),
                    )
                    if _check_insert_data(data, Mapping, "data"):
                        self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][
                            CFG_ASSET_TAGS_KEY
                        ][tag].update(data)
        return self

    def update_assets(
        self, genome: str, asset: str | None = None, data: Mapping | None = None
    ) -> _RefGenConfV03:
        """Update the genomes in RefGenConf object at any level.

        If a requested genome-asset mapping is missing, it will be created.

        Args:
            genome: Genome to be added/updated.
            asset: Asset to be added/updated.
            data: Data to be added/updated.

        Returns:
            Updated object.
        """
        if _check_insert_data(genome, str, "genome"):
            _safe_setdef(self[CFG_GENOMES_KEY], genome, PXAM())
            if _check_insert_data(asset, str, "asset"):
                _safe_setdef(self[CFG_GENOMES_KEY][genome], CFG_ASSETS_KEY, PXAM())
                _safe_setdef(
                    self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY], asset, PXAM()
                )
                if _check_insert_data(data, Mapping, "data"):
                    self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset].update(data)
        return self

    def remove(
        self,
        genome: str,
        asset: str,
        tag: str | None = None,
        relationships: bool = True,
        files: bool = True,
        force: bool = False,
    ) -> _RefGenConfV03 | None:
        """Remove data associated with a specified genome:asset:tag combination.

        If no tags are specified, the entire asset is removed from the genome.
        If no more tags are defined for the selected genome:asset after tag
        removal, the parent asset will be removed as well. If no more assets
        are defined for the selected genome after asset removal, the parent
        genome will be removed as well.

        Args:
            genome: Genome to be removed.
            asset: Asset package to be removed.
            tag: Tag to be removed.
            relationships: Whether the asset being removed should be
                removed from its relatives as well.
            files: Whether the asset files from disk should be removed.
            force: Whether the removal prompts should be skipped.

        Returns:
            Updated object.

        Raises:
            TypeError: If genome argument type is not a list or str.
        """
        tag = tag or self.get_default_tag(genome, asset, use_existing=False)
        if files:
            req_dict = {"genome": genome, "asset": asset, "tag": tag}
            _LOGGER.debug("Attempting removal: {}".format(req_dict))
            if not force and not query_yes_no(
                "Remove '{genome}/{asset}:{tag}'?".format(**req_dict)
            ):
                _LOGGER.info("Action aborted by the user")
                return
            removed = []
            asset_path = self.seek(
                genome, asset, tag, enclosing_dir=True, strict_exists=False
            )
            if os.path.exists(asset_path):
                removed.append(_remove(asset_path))
                if self.file_path:
                    with self as r:
                        r.cfg_remove_assets(genome, asset, tag, relationships)
                else:
                    self.cfg_remove_assets(genome, asset, tag, relationships)
            else:
                _LOGGER.warning(
                    "Selected asset does not exist on disk ({}). "
                    "Removing from genome config.".format(asset_path)
                )
                if self.file_path:
                    with self as r:
                        r.cfg_remove_assets(genome, asset, tag, relationships)
                        return
                else:
                    self.cfg_remove_assets(genome, asset, tag, relationships)
                    return
            try:
                self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset]
            except (KeyError, TypeError):
                asset_dir = os.path.abspath(os.path.join(asset_path, os.path.pardir))
                _entity_dir_removal_log(asset_dir, "asset", req_dict, removed)
                try:
                    self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY]
                except (KeyError, TypeError):
                    genome_dir = os.path.abspath(
                        os.path.join(asset_dir, os.path.pardir)
                    )
                    _entity_dir_removal_log(genome_dir, "genome", req_dict, removed)
                    try:
                        if self.file_path:
                            with self as r:
                                del r[CFG_GENOMES_KEY][genome]
                        else:
                            del self[CFG_GENOMES_KEY][genome]
                    except (KeyError, TypeError):
                        _LOGGER.debug(
                            "Could not remove genome '{}' from the config; it "
                            "does not exist".format(genome)
                        )
            _LOGGER.info(f"Successfully removed entities:{block_iter_repr(remove)})")
        else:
            if self.file_path:
                with self as r:
                    r.cfg_remove_assets(genome, asset, tag, relationships)
            else:
                self.cfg_remove_assets(genome, asset, tag, relationships)

    def cfg_remove_assets(
        self,
        genome: str,
        asset: str,
        tag: str | None = None,
        relationships: bool = True,
    ) -> _RefGenConfV03:
        """Remove data associated with a specified genome:asset:tag combination.

        If no tags are specified, the entire asset is removed from the genome.
        If no more tags are defined for the selected genome:asset after tag
        removal, the parent asset will be removed as well. If no more assets
        are defined for the selected genome after asset removal, the parent
        genome will be removed as well.

        Args:
            genome: Genome to be removed.
            asset: Asset package to be removed.
            tag: Tag to be removed.
            relationships: Whether the asset being removed should be
                removed from its relatives as well.

        Returns:
            Updated object.

        Raises:
            TypeError: If genome argument type is not a list or str.
        """

        def _del_if_empty(obj: Any, attr: str, alt: list[Any] | None = None) -> None:
            """Delete a Mapping attribute if its length is zero.

            Args:
                obj: An object to check.
                attr: Mapping attribute of interest.
                alt: A list of length 2 that indicates alternative
                    Mapping-attribute combination to remove.
            """
            if attr in obj and len(obj[attr]) == 0:
                if alt is None:
                    del obj[attr]
                else:
                    if alt[1] in alt[0]:
                        del alt[0][alt[1]]

        tag = tag or self.get_default_tag(genome, asset)
        if _check_insert_data(genome, str, "genome"):
            if _check_insert_data(asset, str, "asset"):
                if _check_insert_data(tag, str, "tag"):
                    if relationships:
                        self.remove_asset_from_relatives(genome, asset, tag)
                    del self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][
                        CFG_ASSET_TAGS_KEY
                    ][tag]
                    _del_if_empty(
                        self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset],
                        CFG_ASSET_TAGS_KEY,
                        [self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY], asset],
                    )
                    _del_if_empty(self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY], asset)
                    _del_if_empty(
                        self[CFG_GENOMES_KEY][genome],
                        CFG_ASSETS_KEY,
                        [self[CFG_GENOMES_KEY], genome],
                    )
                    _del_if_empty(self[CFG_GENOMES_KEY], genome)
                    try:
                        default_tag = self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][
                            asset
                        ][CFG_ASSET_DEFAULT_TAG_KEY]
                    except KeyError:
                        pass
                    else:
                        if default_tag == tag:
                            del self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][
                                CFG_ASSET_DEFAULT_TAG_KEY
                            ]
                    if len(self[CFG_GENOMES_KEY]) == 0:
                        self[CFG_GENOMES_KEY] = None
        return self

    def update_genomes(
        self, genome: str, data: Mapping | None = None
    ) -> _RefGenConfV03:
        """Update the genomes in RefGenConf object at any level.

        If a requested genome is missing, it will be added.

        Args:
            genome: Genome to be added/updated.
            data: Data to be added/updated.

        Returns:
            Updated object.
        """
        if _check_insert_data(genome, str, "genome"):
            _safe_setdef(self[CFG_GENOMES_KEY], genome, PXAM({CFG_ASSETS_KEY: PXAM()}))
            if _check_insert_data(data, Mapping, "data"):
                self[CFG_GENOMES_KEY][genome].update(data)
        return self

    def _update_genome_servers(self, url: str | list[str], reset: bool = False) -> None:
        """Update the list of genome_servers.

        Use reset argument to overwrite the current list. Otherwise the current
        one will be appended to.

        Args:
            url: URL(s) to update the genome_servers list with.
            reset: Whether the current list should be overwritten.
        """
        urls = _make_list_of_str(url)
        if CFG_SERVERS_KEY in self:
            if reset:
                self[CFG_SERVERS_KEY] = _extend_unique([], urls)
            else:
                self[CFG_SERVERS_KEY] = _extend_unique(self[CFG_SERVERS_KEY], urls)
        else:
            raise GenomeConfigFormatError(
                "The '{}' is missing. Can't update the server list".format(
                    CFG_SERVERS_KEY
                )
            )

    def subscribe(self, urls: list[str], reset: bool = False) -> None:
        """Add URLs to the list of genome_servers.

        Use reset argument to overwrite the current list. Otherwise the current
        one will be appended to.

        Args:
            urls: URLs to update the genome_servers list with.
            reset: Whether the current list should be overwritten.
        """
        if self.file_path:
            with self as r:
                r._update_genome_servers(url=urls, reset=reset)
        else:
            self._update_genome_servers(url=urls, reset=reset)
        _LOGGER.info("Subscribed to: {}".format(", ".join(urls)))

    def unsubscribe(self, urls: list[str]) -> None:
        """Remove URLs from the list of genome_servers.

        Args:
            urls: URLs to remove from the genome_servers list.
        """
        unsub_list = []
        ori_servers = self[CFG_SERVERS_KEY]
        for s in urls:
            try:
                ori_servers.remove(s)
                unsub_list.append(s)
            except ValueError:
                _LOGGER.warning(
                    "URL '{}' not in genome_servers list: {}".format(s, ori_servers)
                )
        if self.file_path:
            with self as r:
                r._update_genome_servers(ori_servers, reset=True)
        else:
            self._update_genome_servers(ori_servers, reset=True)
        if unsub_list:
            _LOGGER.info("Unsubscribed from: {}".format(", ".join(unsub_list)))

    def getseq(self, genome: str, locus: str, as_str: bool = False) -> Any:
        """Return the sequence found in a selected range and chromosome.

        Something like the refget protocol.

        Args:
            genome: Name of the sequence identifier.
            locus: Coordinates of desired sequence, e.g. 'chr1:1-10'.
            as_str: Whether to convert the returned object to string
                and return just the sequence.

        Returns:
            The selected sequence.
        """
        import pyfaidx

        fa = pyfaidx.Fasta(self.seek(genome, "fasta", strict_exists=True))
        locus_split = locus.split(":")
        chr = fa[locus_split[0]]
        if len(locus_split) == 1:
            return str(chr) if as_str else chr
        start, end = locus_split[1].split("-")
        _LOGGER.debug(
            "chr: '{}', start: '{}', end: '{}'".format(locus_split[0], start, end)
        )
        return str(chr[int(start) : int(end)]) if as_str else chr[int(start) : int(end)]

    def get_genome_attributes(self, genome: str) -> dict[str, Any]:
        """Get the dictionary attributes, like checksum, contents, description.

        Does not return the assets.

        Args:
            genome: Genome to get the attributes dict for.

        Returns:
            Available genome attributes.
        """
        return {
            k: self[CFG_GENOMES_KEY][genome][k]
            for k in CFG_GENOME_ATTRS_KEYS
            if k in self[CFG_GENOMES_KEY][genome]
        }

    def is_asset_complete(self, genome: str, asset: str, tag: str) -> bool:
        """Check whether all required tag attributes are defined in the RefGenConf object.

        This is the way we determine tag completeness.

        Args:
            genome: Genome to be checked.
            asset: Asset package to be checked.
            tag: Tag to be checked.

        Returns:
            Whether the asset is complete.
        """
        tag_data = self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][
            CFG_ASSET_TAGS_KEY
        ][tag]
        return all([r in tag_data for r in REQ_TAG_ATTRS])

    def _invert_genomes(
        self, order: Callable[..., Any] | None = None
    ) -> dict[str, list[str]]:
        """Map each asset type/kind/name to a collection of assemblies.

        A configuration file encodes assets by genome, but in some use cases
        it's helpful to invert the direction of this mapping. The value of the
        asset key/name may differ by genome, so that information is
        necessarily lost in this inversion, but we can collect genome IDs by
        asset ID.

        Args:
            order: How to key genome IDs and asset names for sort.

        Returns:
            Binding between asset kind/key/name and collection of
            reference genome assembly names for which the asset type is
            available.
        """
        genomes = {}
        for g, am in self[CFG_GENOMES_KEY].items():
            for a in am[CFG_ASSETS_KEY].keys():
                genomes.setdefault(a, []).append(g)
        assets = sorted(genomes.keys(), key=order)
        return dict([(a, sorted(genomes[a], key=order)) for a in assets])

    def _chk_digest_if_avail(
        self, genome: str, remote_asset_name: str, server_url: str
    ) -> None:
        """Check local asset digest against the remote one.

        Populate children of the asset with the provided asset:tag. In case the
        local asset does not exist, the config is populated with the remote
        asset digest and children data.

        Args:
            genome: Name of the genome to check the asset digests for.
            remote_asset_name: Asset and tag names, formatted like:
                asset:tag.
            server_url: Address of the server to query for the digests.

        Raises:
            RefgenconfError: If the local digest does not match its
                remote counterpart.
        """
        remote_asset_data = prp(remote_asset_name)
        asset = remote_asset_data["item"]
        tag = remote_asset_data["tag"]
        asset_digest_url = construct_request_url(server_url, API_ID_DIGEST).format(
            genome=genome, asset=asset, tag=tag
        )
        try:
            remote_digest = _download_json(asset_digest_url)
        except DownloadJsonError:
            _LOGGER.warning(
                "Parent asset ({}/{}:{}) not found on the server. The asset provenance was not verified.".format(
                    genome, asset, tag
                )
            )
            return
        try:
            local_digest = self.id(genome, asset, tag)
            if remote_digest != local_digest:
                raise RemoteDigestMismatchError(asset, local_digest, remote_digest)
        except RefgenconfError:
            _LOGGER.debug(
                "Could not find '{}/{}:{}' digest. Digest for this parent will be populated "
                "with the server one after the pull".format(genome, asset, tag)
            )
            return

    def chk_digest_update_child(
        self, genome: str, remote_asset_name: str, child_name: str, server_url: str
    ) -> None:
        """Check local asset digest against the remote one and update children.

        Populate children of the asset with the provided asset:tag. In case the
        local asset does not exist, the config is populated with the remote
        asset digest and children data.

        Args:
            genome: Name of the genome to check the asset digests for.
            remote_asset_name: Asset and tag names, formatted like:
                asset:tag.
            child_name: Name to be appended to the children of the
                parent.
            server_url: Address of the server to query for the digests.

        Raises:
            RefgenconfError: If the local digest does not match its
                remote counterpart.
        """
        remote_asset_data = prp(remote_asset_name)
        asset = remote_asset_data["item"]
        tag = remote_asset_data["tag"]
        asset_digest_url = construct_request_url(server_url, API_ID_DIGEST).format(
            genome=genome, asset=asset, tag=tag
        )
        try:
            remote_digest = _download_json(asset_digest_url)
        except DownloadJsonError:
            return
        try:
            # we need to allow for missing seek_keys section so that the digest is respected even from the previously
            # populated 'incomplete asset' from the server
            _assert_gat_exists(
                self[CFG_GENOMES_KEY],
                genome,
                asset,
                tag,
                allow_incomplete=not self.is_asset_complete(genome, asset, tag),
            )
        except (KeyError, MissingAssetError, MissingGenomeError, MissingSeekKeyError):
            self.update_tags(
                genome, asset, tag, {CFG_ASSET_CHECKSUM_KEY: remote_digest}
            )
            _LOGGER.info(
                "Could not find '{}/{}:{}' digest. Populating with server data".format(
                    genome, asset, tag
                )
            )
        else:
            local_digest = self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset][
                CFG_ASSET_TAGS_KEY
            ][tag][CFG_ASSET_CHECKSUM_KEY]
            if remote_digest != local_digest:
                raise RemoteDigestMismatchError(asset, local_digest, remote_digest)
        finally:
            self.update_relatives_assets(
                genome, asset, tag, [child_name], children=True
            )

    def id(self, genome: str, asset: str, tag: str | None = None) -> str:
        """Return the digest for the specified asset.

        The defined default tag will be used if not provided as an argument.

        Args:
            genome: Genome identifier.
            asset: Asset identifier.
            tag: Tag identifier.

        Returns:
            Asset digest for the tag.
        """
        _assert_gat_exists(self[CFG_GENOMES_KEY], genome, asset, tag)
        tag = tag or self.get_default_tag(genome, asset)
        a = self[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][asset]
        if CFG_ASSET_CHECKSUM_KEY in a[CFG_ASSET_TAGS_KEY][tag]:
            return a[CFG_ASSET_TAGS_KEY][tag][CFG_ASSET_CHECKSUM_KEY]
        raise MissingConfigDataError(
            "Digest does not exist for: {}/{}:{}".format(genome, asset, tag)
        )

    def run_plugins(self, hook: str) -> None:
        """Run all installed plugins for the specified hook.

        Args:
            hook: Hook identifier.
        """
        for name, func in self.plugins[hook].items():
            _LOGGER.debug("Running {} plugin: {}".format(hook, name))
            func(self)

    def write(self, filepath: str | None = None) -> str:
        """Write the contents to a file.

        If pre- and post-update plugins are defined, they will be executed
        automatically.

        Args:
            filepath: A file path to write to.

        Returns:
            The path to the created file.

        Raises:
            OSError: When the object has been created in a read only
                mode or other process has locked the file, or when the
                write is called on an object with no write capabilities
                or when writing to a file that is locked by a different
                object.
            TypeError: When the filepath cannot be determined. This
                takes place only if YacAttMap initialized with a Mapping
                as an input, not read from file.
        """
        self.run_plugins(PRE_UPDATE_HOOK)
        path = super(_RefGenConfV03, self).write(filepath=filepath)
        self.run_plugins(POST_UPDATE_HOOK)
        return path


class DownloadProgressBar(tqdm):
    """Progress bar for downloads, from tqdm hooks and callbacks."""

    def update_to(self, b: int = 1, bsize: int = 1, tsize: int | None = None) -> None:
        """Update the progress bar.

        Args:
            b: Number of blocks transferred so far.
            bsize: Size of each block (in tqdm units).
            tsize: Total size (in tqdm units).
        """
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def _download_json(url: str, params: dict[str, Any] | None = None) -> Any:
    """Safely connect to the provided API endpoint and download JSON data.

    Args:
        url: Server API endpoint.
        params: Query parameters.

    Returns:
        Served data.
    """
    import requests

    _LOGGER.debug("Downloading JSON data; querying URL: '{}'".format(url))
    resp = requests.get(url, params=params)
    if resp.ok:
        return resp.json()
    elif resp.status_code == 404:
        resp = None
    raise DownloadJsonError(resp)


def _download_url_progress(
    url: str, output_path: str, name: str, params: dict[str, Any] | None = None
) -> None:
    """Download asset at given URL to given filepath, show progress along the way.

    Args:
        url: Server API endpoint.
        output_path: Path to file to save download.
        name: Name to display in front of the progress bar.
        params: Query parameters to be added to the request.
    """
    url = url if params is None else url + "?{}".format(urllib.parse.urlencode(params))
    with DownloadProgressBar(
        unit_scale=True, desc=name, unit="B", bar_format=CUSTOM_BAR_FMT, leave=False
    ) as dpb:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=dpb.update_to)


def _genome_asset_path(
    genomes: Mapping,
    gname: str,
    aname: str,
    tname: str,
    seek_key: str | None,
    enclosing_dir: bool,
    no_tag: bool = False,
) -> str:
    """Retrieve the raw path value for a particular asset for a particular genome.

    Args:
        genomes: Nested collection of key-value pairs, keyed at top
            level on genome ID, then by asset name, then by asset
            attribute.
        gname: Top level key to query -- genome ID, e.g. mm10.
        aname: Second-level key to query -- asset name, e.g. fasta.
        tname: Third-level key to query -- tag name, e.g. default.
        seek_key: Fourth-level key to query -- seek key name, e.g.
            chrom_sizes.
        enclosing_dir: Whether a path to the entire enclosing directory
            should be returned, e.g. for a fasta asset that has 3
            seek_keys pointing to 3 files in an asset dir, that asset
            dir is returned.
        no_tag: Whether to exclude the tag from the path.

    Returns:
        Raw path value for a particular asset for a particular genome.

    Raises:
        MissingGenomeError: If the given key-value pair collection does
            not contain as a top-level key the given genome ID.
        MissingAssetError: If the given key-value pair collection does
            contain the given genome ID, but that key's mapping doesn't
            contain the given asset name as a key.
        GenomeConfigFormatError: If it's discovered during the query
            that the structure of the given genomes mapping suggests
            that it was parsed from an improperly formatted/structured
            genome config file.
    """
    _assert_gat_exists(genomes, gname, aname, tname)
    asset_tag_data = genomes[gname][CFG_ASSETS_KEY][aname][CFG_ASSET_TAGS_KEY][tname]
    if enclosing_dir:
        if no_tag:
            return asset_tag_data[CFG_ASSET_PATH_KEY]
        return os.path.join(asset_tag_data[CFG_ASSET_PATH_KEY], tname)
    if seek_key is None:
        if aname in asset_tag_data[CFG_SEEK_KEYS_KEY]:
            seek_key = aname
        else:
            if no_tag:
                return asset_tag_data[CFG_ASSET_PATH_KEY]
            return os.path.join(asset_tag_data[CFG_ASSET_PATH_KEY], tname)
    try:
        seek_key_value = asset_tag_data[CFG_SEEK_KEYS_KEY][seek_key]
    except KeyError:
        raise MissingSeekKeyError(
            "genome/asset:tag bundle '{}/{}:{}' exists, but seek_key '{}' is missing".format(
                gname, aname, tname, seek_key
            )
        )
    else:
        if no_tag:
            return os.path.join(asset_tag_data[CFG_ASSET_PATH_KEY], seek_key_value)
        return os.path.join(asset_tag_data[CFG_ASSET_PATH_KEY], tname, seek_key_value)


def _assert_gat_exists(
    genomes: Mapping,
    gname: str,
    aname: str | None = None,
    tname: str | None = None,
    allow_incomplete: bool = False,
) -> None:
    """Ensure the genome/asset:tag combination exists in the provided mapping.

    Also checks that seek keys are defined. Seek keys are required for asset
    completeness.

    Args:
        genomes: Nested collection of key-value pairs, keyed at top
            level on genome ID, then by asset name, then by asset
            attribute.
        gname: Top level key to query -- genome ID, e.g. mm10.
        aname: Second-level key to query -- asset name, e.g. fasta.
        tname: Third-level key to query -- tag name, e.g. default.
        allow_incomplete: Whether to allow assets without seek keys.

    Raises:
        MissingGenomeError: If the given key-value pair collection does
            not contain as a top-level key the given genome ID.
        MissingAssetError: If the given key-value pair collection does
            contain the given genome ID, but that key's mapping doesn't
            contain the given asset name as a key.
        GenomeConfigFormatError: If it's discovered during the query
            that the structure of the given genomes mapping suggests
            that it was parsed from an improperly formatted/structured
            genome config file.
    """
    _LOGGER.debug("checking existence of: {}/{}:{}".format(gname, aname, tname))
    try:
        genome = genomes[gname]
    except KeyError:
        raise MissingGenomeError("Your genomes do not include '{}'".format(gname))
    if aname is not None:
        try:
            asset_data = genome[CFG_ASSETS_KEY][aname]
        except KeyError:
            raise MissingAssetError(
                "Genome '{}' exists, but asset '{}' is missing".format(gname, aname)
            )
        except TypeError:
            _raise_not_mapping(asset_data, "Asset section ")
        if tname is not None:
            try:
                tag_data = asset_data[CFG_ASSET_TAGS_KEY][tname]
            except KeyError:
                raise MissingTagError(
                    "genome/asset bundle '{}/{}' exists, but tag '{}' is missing".format(
                        gname, aname, tname
                    )
                )
            except TypeError:
                _raise_not_mapping(asset_data, "Asset section ")
            try:
                tag_data[CFG_SEEK_KEYS_KEY]
            except KeyError:
                if not allow_incomplete:
                    raise MissingSeekKeyError(
                        "Asset incomplete. No seek keys are defined for '{}/{}:{}'. "
                        "Build or pull the asset again.".format(gname, aname, tname)
                    )


def _is_large_archive(size: str, cutoff: int | float = 10) -> bool:
    """Determine if the file is large based on a string formatted as follows: 15.4GB.

    Args:
        size: Size string.
        cutoff: Size cutoff in GB.

    Returns:
        Whether the archive exceeds the size cutoff.
    """

    def _str2float(x: str) -> float:
        """Remove any letters from the file size string and cast the remainder to float."""
        return float("".join(c for c in x if c in "0123456789."))

    _LOGGER.debug("Checking archive size: '{}'".format(size))
    if size.endswith("MB"):
        # convert to gigs
        size = "{0:f}GB".format(_str2float(size) / 1000)
    if size.endswith("KB"):
        # convert to gigs
        size = "{0:f}GB".format(_str2float(size) / 1000**2)
    return size.endswith("TB") or (size.endswith("GB") and _str2float(size) > cutoff)


def _list_remote(
    url: str,
    genome: str | list[str] | None,
    order: Callable[..., Any] | None = None,
    as_str: bool = True,
) -> tuple[str, str] | tuple[None, None] | dict[str, list[str]]:
    """List genomes and assets available remotely.

    Args:
        url: Location or ref genome config data.
        genome: Genome filter.
        order: How to key genome IDs and asset names for sort.
        as_str: Whether to return the data as strings.

    Returns:
        Text representations of remotely available genomes and assets.
    """
    genomes_data = _read_remote_data(url)
    refgens = _select_genomes(
        sorted(genomes_data.keys(), key=order), genome, strict=True
    )
    if not refgens:
        return None, None if as_str else dict()
    filtered_genomes_data = dict(
        [(rg, sorted(genomes_data[rg], key=order)) for rg in refgens]
    )
    if not as_str:
        return filtered_genomes_data
    asset_texts = [
        "{}/   {}".format(g.rjust(20), ", ".join(a))
        for g, a in filtered_genomes_data.items()
    ]
    return ", ".join(refgens), "\n".join(asset_texts)


def _make_genome_assets_line(
    gen: str,
    assets: Mapping,
    offset_text: str = "  ",
    genome_assets_delim: str = "/ ",
    asset_sep: str = ", ",
    order: Callable[..., Any] | None = None,
    asset_tag_delim: str = ":",
) -> str:
    """Build a line of text for display of assets by genome.

    Args:
        gen: Reference assembly ID, e.g. hg38.
        assets: Collection of asset names for the given genome.
        offset_text: Prefix for the line, e.g. a kind of whitespace.
        genome_assets_delim: Delimiter between a genome ID and text
            showing names of assets for that genome.
        asset_sep: Delimiter between asset names.
        order: How to key asset names for sort.
        asset_tag_delim: Delimiter between asset name and tag.

    Returns:
        Text representation of a single assembly's name and assets.
    """
    tagged_assets = asset_sep.join(
        sorted(_make_asset_tags_product(assets, asset_tag_delim), key=order)
    )
    return "{}{}{}{}".format(
        gen.rjust(20), genome_assets_delim, offset_text, tagged_assets
    )


def _make_asset_tags_product(
    assets: Mapping, asset_tag_delim: str = ":", asset_sk_delim: str = "."
) -> list[str]:
    """Make a product of assets and tags available in the provided mapping.

    Args:
        assets: The assets for a selected genome.
        asset_tag_delim: How to represent the asset-tag link.
        asset_sk_delim: How to represent the asset-seek_key link.

    Returns:
        List representation of tagged assets.
    """
    tagged_assets = []
    for aname, asset in assets.items():
        for tname, tag in asset[CFG_ASSET_TAGS_KEY].items():
            sk_assets = []
            seek_keys = get_tag_seek_keys(tag)
            # proceed only if asset is 'complete' -- has seek_keys
            if seek_keys is not None:
                # add seek_keys if exist and different from the asset name, otherwise just the asset name
                sk_assets.extend(
                    [
                        asset_sk_delim.join([aname, sk]) if sk != aname else aname
                        for sk in seek_keys
                    ]
                )
            # add tags to the asset.seek_key list
            tagged_assets.extend(
                [asset_tag_delim.join(i) for i in itertools.product(sk_assets, [tname])]
            )
    return tagged_assets


def _read_remote_data(url: str) -> Any:
    """Read JSON data from a URL request response.

    Args:
        url: Data request URL.

    Returns:
        JSON parsed from the response from given URL request.
    """
    with urllib.request.urlopen(url) as response:
        encoding = response.info().get_content_charset("utf8")
        return json.loads(response.read().decode(encoding))


def _check_insert_data(obj: Any, datatype: type, name: str) -> bool:
    """Check validity of an object."""
    if obj is None:
        return False
    if not isinstance(obj, datatype):
        raise TypeError(
            "{} must be {}; got {}".format(name, datatype.__name__, type(obj).__name__)
        )
    return True


def _make_list_of_str(arg: str | list[str]) -> list[str]:
    """Convert a str to list of str or ensure a list is a list of str.

    Args:
        arg: String or a list of strings to listify.

    Returns:
        List of strings.

    Raises:
        TypeError: If a faulty argument was provided.
    """

    def _raise_faulty_arg() -> None:
        raise TypeError(
            "Provided argument has to be a list[str] or a str, got '{}'".format(
                arg.__class__.__name__
            )
        )

    if isinstance(arg, str):
        return [arg]
    elif isinstance(arg, list):
        if not all(isinstance(i, str) for i in arg):
            _raise_faulty_arg()
        else:
            return arg
    else:
        _raise_faulty_arg()


def _extend_unique(l1: list[Any], l2: list[Any]) -> list[Any]:
    """Extend a list with no duplicates.

    Args:
        l1: Original list.
        l2: List with items to add.

    Returns:
        An extended list.
    """
    return l1 + list(set(l2) - set(l1))


def _select_genomes(
    genomes: list[str], genome: str | list[str] | None = None, strict: bool = False
) -> list[str] | None:
    """Safely select a subset of genomes.

    Args:
        genomes: Full list of available genomes.
        genome: Genomes that the assets should be found for.
        strict: Whether a non-existent genome should lead to a warning.
            Specific genome request is disregarded otherwise.

    Returns:
        Selected subset of genomes.

    Raises:
        TypeError: If genome argument type is not a list or str.
    """
    if genome:
        genome = _make_list_of_str(genome)
    else:
        return genomes
    if strict:
        missing = []
        filtered = []
        for g in genome:
            if g in genomes:
                filtered.append(g)
            else:
                missing.append(g)
        if missing:
            _LOGGER.warning("Genomes do not include: {}".format(", ".join(missing)))
        return None if not filtered else filtered
    return genomes if not all(x in genomes for x in genome) else genome


def get_asset_tags(asset: Mapping) -> list[str]:
    """Return a list of asset tags.

    These need an accession function since under the tag name key there are
    not only tag names, but also the default tag pointer.

    Args:
        asset: A single asset part of the RefGenConf.

    Returns:
        Asset tags.
    """
    return [t for t in asset[CFG_ASSET_TAGS_KEY]]


def get_tag_seek_keys(tag: Mapping) -> list[str] | None:
    """Return a list of tag seek keys.

    Args:
        tag: A single tag part of the RefGenConf.

    Returns:
        Tag seek keys.
    """
    return [s for s in tag[CFG_SEEK_KEYS_KEY]] if CFG_SEEK_KEYS_KEY in tag else None


def construct_request_url(server_url: str, operation_id: str) -> str:
    """Create a request URL based on an openAPI description.

    Args:
        server_url: Server URL.
        operation_id: The operationId of the endpoint.

    Returns:
        A complete URL for the request.
    """
    try:
        return server_url + _get_server_endpoints_mapping(server_url)[operation_id]
    except KeyError as e:
        _LOGGER.error(
            "'{}' is not a compatible refgenieserver instance. "
            "Could not determine API endpoint defined by ID: {}".format(server_url, e)
        )
        sys.exit(1)


def _get_server_endpoints_mapping(url: str) -> dict[str, str]:
    """Establish the API with the server using operationId field in the openAPI JSON description.

    Args:
        url: Server URL.

    Returns:
        Endpoints mapped by their operationIds.
    """
    json = _download_json(url + "/openapi.json")
    return map_paths_by_id(
        asciify_json_dict(json) if sys.version_info[0] == 2 else json
    )


def map_paths_by_id(json_dict: dict[str, Any]) -> dict[str, str]:
    # check the required input dict characteristics to construct the mapping
    if (
        "openapi" not in json_dict
        or not isinstance(json_dict["openapi"], str)
        or "paths" not in json_dict
        or not isinstance(json_dict["paths"], dict)
    ):
        raise ValueError(
            "The provided mapping is not a valid representation of a JSON openAPI description"
        )
    return {
        values["get"]["operationId"]: endpoint
        for endpoint, values in json_dict["paths"].items()
    }


def _remove(path: str) -> str:
    """Remove asset if it is a dir or a file.

    Args:
        path: Path to the entity to remove, either a file or a dir.

    Returns:
        Removed path.
    """
    from shutil import rmtree

    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        rmtree(path)
    else:
        raise ValueError("path '{}' is neither a file nor a dir.".format(path))
    return path


def _entity_dir_removal_log(
    directory: str,
    entity_class: str,
    asset_dict: dict[str, str],
    removed_entities: list[str],
) -> None:
    """Message and save removed entity data.

    Args:
        directory: Removed dir.
        entity_class: Class of the entity.
        asset_dict: Selected genome/asset:tag combination.
        removed_entities: List of the removed entities to append to.
    """
    subclass = "asset" if entity_class == "genome" else "tag"
    if os.path.basename(directory) == asset_dict[entity_class]:
        _LOGGER.info(
            "Last {sub} for {ec} '{en}' has been removed, removing {ec} directory".format(
                sub=subclass, ec=entity_class, en=asset_dict[entity_class]
            )
        )
        removed_entities.append(_remove(directory))
    else:
        _LOGGER.debug(
            "Didn't remove '{}' since it does not match the {} name: {}".format(
                directory, entity_class, asset_dict[entity_class]
            )
        )


def _safe_setdef(mapping: Any, attr: str, val: Any) -> Any:
    """Set default value for a mapping, catching type errors.

    Catches errors caused by the mapping to be updated being an object of
    incorrect type, and raises an informative error.

    Args:
        mapping: Mapping to update.
        attr: Attribute to update.
        val: Value to assign as the default.

    Returns:
        Updated mapping.

    Raises:
        GenomeConfigFormatError: If mapping is of incorrect class.
    """
    try:
        mapping.setdefault(attr, val)
    except (TypeError, AttributeError):
        _raise_not_mapping(mapping, "Cannot update; Section '{}' ".format(attr))
    return mapping


def _raise_not_mapping(mapping: Any, prefix: str = "") -> None:
    raise GenomeConfigFormatError(
        prefix
        + "is not a mapping but '{}'. This is usually a result of "
        "a previous error".format(type(mapping).__name__)
    )
