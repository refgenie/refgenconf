"""
Config file structure determination for the refgenie suite of packages

These values are defined here in refgenconf and use some within this package,
but they're also integral to both refgenie and to refgenieserver.
"""

import os
from string import ascii_letters, digits

CFG_NAME = "genome configuration"
CFG_ENV_VARS = ["REFGENIE"]
CFG_CONST = ["CFG_NAME", "CFG_ENV_VARS"]
DEFAULT_SERVER = "http://refgenomes.databio.org"  # "http://rg.databio.org"
TAG_NAME_CHAR_WHITELIST = ascii_letters + digits + "-._~"
API_VERSION = "v3"
API_VERSION_2 = "v2"
DEFAULT_TAG = "default"
DEFAULT_CONFIG_SCHEMA = os.path.join(
    os.path.dirname(__file__), "schemas", "genome_config_schema.yaml"
)
DEFAULT_ASSET_CLASS_SCHEMA = os.path.join(
    os.path.dirname(__file__), "schemas", "asset_class_schema.yaml"
)
DEFAULT_RECIPE_SCHEMA = os.path.join(
    os.path.dirname(__file__), "schemas", "recipe_schema.yaml"
)

# file or dir names
TEMPLATE_RECIPE_INPUTS_JSON = "build_inputs_{}__{}.json"
TEMPLATE_RECIPE_JSON = "build_recipe_{}__{}.json"
TEMPLATE_TARGET = "{}_{}__{}.flag"
TEMPLATE_LOG = "build_log_{}__{}.md"
TEMPLATE_ASSET_DIR_CONTENTS = "asset_dir_contents_{}__{}.json"
TEMPLATE_RECIPE_YAML = "{}_asset_recipe.yaml"
TEMPLATE_ASSET_CLASS_YAML = "{}_asset_class.yaml"
ORI_LOG_NAME_REGEX = "*_log.md"
BUILD_STATS_DIR = "_refgenie_build"
LOCKED_BUILD_MAP_CFG = "_locked_map_build.yaml"
LOCKED_ARCHIVE_MAP_CFG = "_locked_map_archive.yaml"
BUILD_MAP_CFG = "_map_build.yaml"
ARCHIVE_MAP_CFG = "_map_archive.yaml"
ALIAS_DIR = "alias"
DATA_DIR = "data"

FILE_DIR_NAMES = [
    "TEMPLATE_RECIPE_INPUTS_JSON",
    "TEMPLATE_RECIPE_JSON",
    "TEMPLATE_RECIPE_YAML",
    "TEMPLATE_ASSET_CLASS_YAML",
    "TEMPLATE_TARGET",
    "TEMPLATE_LOG",
    "TEMPLATE_ASSET_DIR_CONTENTS",
    "ORI_LOG_NAME_REGEX",
    "BUILD_STATS_DIR",
    "BUILD_MAP_CFG",
    "LOCKED_BUILD_MAP_CFG",
    "ARCHIVE_MAP_CFG",
    "LOCKED_ARCHIVE_MAP_CFG",
    "ALIAS_DIR",
    "DATA_DIR",
]

# project-wide definition of the endpoint IDs. They are used to establish the
# way of communication between the server and the client so that changes of
# endpoint function names OR endpoints themselves do not influence the connection
CUSTOM_PFX = "custom_Id"
API_ID_ALIAS_ALIAS = CUSTOM_PFX + "_alias_alias"
API_ID_ALIAS_DIGEST = CUSTOM_PFX + "_alias_digest"
API_ID_ALIASES_DICT = CUSTOM_PFX + "_aliases_dict"
API_ID_ASSETS = CUSTOM_PFX + "_assets"
API_ID_ARCHIVE = CUSTOM_PFX + "_archive"
API_ID_DEFAULT_TAG = CUSTOM_PFX + "_default_tag"
API_ID_ASSET_ATTRS = CUSTOM_PFX + "_asset_attrs"
API_ID_GENOME_ATTRS = CUSTOM_PFX + "_genome_attrs"
API_ID_DIGEST = CUSTOM_PFX + "_asset_digest"
API_ID_RECIPE = CUSTOM_PFX + "_asset_recipe"
API_ID_LOG = CUSTOM_PFX + "_asset_log"
API_ID_ASSET_FILE = CUSTOM_PFX + "_asset_file"
API_ID_ASSET_PATH = CUSTOM_PFX + "_asset_path"
API_ID_ARCHIVE_DIGEST = CUSTOM_PFX + "_asset_archive_digest"
API_ID_SPLASH = CUSTOM_PFX + "_asset_splash"
API_ID_GENOMES_DICT = CUSTOM_PFX + "_genomes_dict"
API_ID_CONTENTS = CUSTOM_PFX + "_asset_dir_contents"
API_ID_BUILD_INPUTS = CUSTOM_PFX + "_build_inputs"
API_ID_RECIPE_CONTENTS = CUSTOM_PFX + "_recipe_contents"
API_ID_RECIPE_ATTRS = CUSTOM_PFX + "_recipe_attrs"
API_ID_ASSET_CLASS_ATTRS = CUSTOM_PFX + "_asset_class_attrs"
API_ID_ASSET_CLASS_CONTENTS = CUSTOM_PFX + "_asset_class_contents"
API_ID_RECIPES_DICT = CUSTOM_PFX + "_recipes_dict"
API_ID_ASSET_CLASSES_DICT = CUSTOM_PFX + "_asset_classes_dict"

PRIVATE_API = "_private_api"

# this dictionary groups the operationIds so that they can be accessed as
# modules for systematic links generation in the splash pages
OPERATION_IDS = {
    "asset": {
        API_ID_ARCHIVE: "archive",
        API_ID_ASSET_ATTRS: "attributes",
        API_ID_DIGEST: "asset digest",
        API_ID_ARCHIVE_DIGEST: "archive digest",
        API_ID_RECIPE: "build recipe",
        API_ID_LOG: "build log",
    },
    "v3_asset": {
        API_VERSION + API_ID_ARCHIVE: "archive",
        API_VERSION + API_ID_ASSET_ATTRS: "attributes",
        API_VERSION + API_ID_DIGEST: "asset digest",
        API_VERSION + API_ID_ARCHIVE_DIGEST: "archive digest",
        API_VERSION + API_ID_RECIPE: "build recipe",
        API_VERSION + API_ID_LOG: "build log",
        API_VERSION + API_ID_CONTENTS: "asset directory contents",
        API_VERSION + API_ID_BUILD_INPUTS: "build inputs",
    },
    "v3_recipe": {
        API_VERSION + API_ID_RECIPE_CONTENTS: "contents",
        API_VERSION + API_ID_RECIPE_ATTRS: "attributes",
    },
    "v3_asset_class": {
        API_VERSION + API_ID_ASSET_CLASS_CONTENTS: "contents",
        API_VERSION + API_ID_ASSET_CLASS_ATTRS: "attributes",
    },
}

API_IDS = [
    "API_ID_ASSETS",
    "API_ID_ARCHIVE",
    "API_ID_DEFAULT_TAG",
    "API_ID_LOG",
    "API_ID_CONTENTS",
    "API_ID_BUILD_INPUTS",
    "API_ID_ASSET_FILE",
    "API_ID_ASSET_PATH",
    "API_ID_DIGEST",
    "API_ID_RECIPE",
    "API_ID_ASSET_ATTRS",
    "API_ID_SPLASH",
    "API_ID_ALIASES_DICT",
    "API_ID_ARCHIVE_DIGEST",
    "API_ID_ALIAS_ALIAS",
    "API_ID_ALIAS_DIGEST",
    "API_ID_GENOME_ATTRS",
    "API_ID_GENOMES_DICT",
    "API_ID_RECIPES_DICT",
    "API_ID_RECIPE_CONTENTS",
    "API_ID_RECIPE_ATTRS",
    "API_ID_ASSET_CLASS_CONTENTS",
    "API_ID_ASSET_CLASS_ATTRS",
    "API_ID_ASSET_CLASSES_DICT",
]

CFG_FOLDER_KEY = "genome_folder"
CFG_RECIPE_FOLDER_KEY = "recipe_folder"
CFG_ASSET_CLASS_FOLDER_KEY = "asset_class_folder"
CFG_SERVERS_KEY = "genome_servers"
CFG_SERVER_KEY = "genome_server"
CFG_ARCHIVE_KEY = "genome_archive_folder"
CFG_ARCHIVE_KEY_OLD = "genome_archive"
CFG_ARCHIVE_CONFIG_KEY = "genome_archive_config"
CFG_REMOTE_URL_BASE_KEY = "remote_url_base"
CFG_VERSION_KEY = "config_version"
CFG_GENOMES_KEY = "genomes"
CFG_ALIASES_KEY = "aliases"
CFG_RECIPES_KEY = "recipes"
CFG_ASSET_CLASSES_KEY = "asset_classes"

CFG_CHECKSUM_KEY = "genome_digest"
CFG_GENOME_DESC_KEY = "genome_description"
CFG_ASSETS_KEY = "assets"

CFG_GENOME_MASK_KEY = "genome_mask"
CFG_ASSET_PATH_KEY = "asset_path"
CFG_ASSET_SIZE_KEY = "asset_size"
CFG_ASSET_DESC_KEY = "asset_description"
CFG_ASSET_DATE_KEY = "date_built"
CFG_ASSET_CUSTOM_PROPS_KEY = "custom_properties"
CFG_ARCHIVE_SIZE_KEY = "archive_size"
CFG_ARCHIVE_CHECKSUM_KEY = "archive_digest"
CFG_SEEK_KEYS_KEY = "seek_keys"
CFG_ASSET_PARENTS_KEY = "asset_parents"
CFG_ASSET_CHILDREN_KEY = "asset_children"
CFG_ASSET_DEFAULT_TAG_KEY = "default_tag"
CFG_ASSET_CLASS_KEY = "asset_class"
CFG_ASSET_TAGS_KEY = "tags"
CFG_ASSET_CHECKSUM_KEY = "asset_digest"
CFG_TAG_DESC_KEY = "tag_description"

CFG_ASSET_RELATIVES_KEYS = [CFG_ASSET_CHILDREN_KEY, CFG_ASSET_PARENTS_KEY]

CFG_TOP_LEVEL_KEYS = [
    CFG_FOLDER_KEY,
    CFG_RECIPE_FOLDER_KEY,
    CFG_ASSET_CLASS_FOLDER_KEY,
    CFG_SERVER_KEY,
    CFG_SERVERS_KEY,
    CFG_ARCHIVE_KEY,
    CFG_GENOMES_KEY,
    CFG_ASSET_CLASSES_KEY,
    CFG_RECIPES_KEY,
    CFG_ALIASES_KEY,
    CFG_VERSION_KEY,
    CFG_ARCHIVE_CONFIG_KEY,
    CFG_ARCHIVE_KEY_OLD,
    CFG_REMOTE_URL_BASE_KEY,
]
CFG_GENOME_KEYS = [CFG_GENOME_DESC_KEY, CFG_ASSETS_KEY, CFG_CHECKSUM_KEY]
CFG_GENOME_ATTRS_KEYS = [CFG_GENOME_DESC_KEY, CFG_CHECKSUM_KEY]
CFG_SINGLE_ASSET_SECTION_KEYS = [
    CFG_ASSET_PATH_KEY,
    CFG_ASSET_DESC_KEY,
    CFG_ASSET_DATE_KEY,
    CFG_ASSET_CUSTOM_PROPS_KEY,
    CFG_ASSET_SIZE_KEY,
    CFG_ARCHIVE_SIZE_KEY,
    CFG_ARCHIVE_CHECKSUM_KEY,
    CFG_SEEK_KEYS_KEY,
    CFG_GENOME_MASK_KEY,
]

RGC_REQ_KEYS = [
    CFG_SERVERS_KEY,
    CFG_FOLDER_KEY,
    CFG_GENOMES_KEY,
    CFG_ASSET_CLASSES_KEY,
    CFG_RECIPES_KEY,
    CFG_VERSION_KEY,
    CFG_RECIPE_FOLDER_KEY,
    CFG_ASSET_CLASS_FOLDER_KEY,
]

CFG_KEY_NAMES = [
    "CFG_FOLDER_KEY",
    "CFG_RECIPE_FOLDER_KEY",
    "CFG_ASSET_CLASS_FOLDER_KEY",
    "CFG_SERVER_KEY",
    "CFG_SERVERS_KEY",
    "CFG_GENOMES_KEY",
    "CFG_ASSET_CLASSES_KEY",
    "CFG_RECIPES_KEY",
    "CFG_GENOME_MASK_KEY",
    "CFG_ALIASES_KEY",
    "CFG_ASSET_PATH_KEY",
    "CFG_ASSET_DESC_KEY",
    "CFG_ASSET_DATE_KEY",
    "CFG_ASSET_CUSTOM_PROPS_KEY",
    "CFG_ARCHIVE_KEY",
    "CFG_ARCHIVE_SIZE_KEY",
    "CFG_SEEK_KEYS_KEY",
    "CFG_ASSET_SIZE_KEY",
    "CFG_CHECKSUM_KEY",
    "CFG_ARCHIVE_CHECKSUM_KEY",
    "CFG_VERSION_KEY",
    "CFG_ASSET_PARENTS_KEY",
    "CFG_ASSET_CHILDREN_KEY",
    "CFG_TAG_DESC_KEY",
    "CFG_ASSET_CHECKSUM_KEY",
    "CFG_ASSET_TAGS_KEY",
    "CFG_ASSET_RELATIVES_KEYS",
    "CFG_ARCHIVE_CONFIG_KEY",
    "CFG_ARCHIVE_KEY_OLD",
    "CFG_REMOTE_URL_BASE_KEY",
]

# hook identifiers
PRE_UPDATE_HOOK = "pre_update"
POST_UPDATE_HOOK = "post_update"
PRE_PULL_HOOK = "pre_pull"
POST_PULL_HOOK = "post_pull"
PRE_TAG_HOOK = "pre_tag"
POST_TAG_HOOK = "post_tag"
PRE_LIST_HOOK = "pre_list"
POST_LIST_HOOK = "post_list"
# HOOKS is a list of all available plugin entry points
HOOK_NAMES = [
    "PRE_LIST_HOOK",
    "PRE_PULL_HOOK",
    "PRE_TAG_HOOK",
    "PRE_UPDATE_HOOK",
    "POST_TAG_HOOK",
    "POST_LIST_HOOK",
    "POST_PULL_HOOK",
    "POST_UPDATE_HOOK",
]
HOOKS = [eval(x) for x in HOOK_NAMES]

# other consts
REQ_CFG_VERSION = 0.5
REFGENIE_BY_CFG = {"0.5": "0.13.0", "0.4": "0.10.0", "0.3": "0.7.0", "0.2": "0.6.0"}
CFG_UPGRADE = {"0.3": ["0.4"], "0.4": ["0.5"]}
ATTRS_COPY_PULL = [
    CFG_ASSET_DESC_KEY,
    CFG_ASSET_DATE_KEY,
    CFG_ASSET_CUSTOM_PROPS_KEY,
    CFG_SEEK_KEYS_KEY,
    CFG_ASSET_PARENTS_KEY,
    CFG_ASSET_PATH_KEY,
    CFG_ASSET_CHECKSUM_KEY,
    CFG_TAG_DESC_KEY,
]
REQ_TAG_ATTRS = [CFG_ASSET_PATH_KEY, CFG_SEEK_KEYS_KEY]
CUSTOM_BAR_FMT = "{desc}{percentage:3.0f}%|{bar}| {n_fmt} [{elapsed}<{remaining} {rate_fmt}{postfix}]"

__all__ = (
    [
        "DEFAULT_SERVER",
        "CFG_ASSET_DEFAULT_TAG_KEY",
        "CFG_ASSET_CLASS_KEY",
        "CFG_KEY_NAMES",
        "CFG_GENOME_DESC_KEY",
        "REQ_CFG_VERSION",
        "CFG_ASSETS_KEY",
        "CFG_GENOME_ATTRS_KEYS",
        "REFGENIE_BY_CFG",
        "CFG_UPGRADE",
        "DEFAULT_TAG",
        "ATTRS_COPY_PULL",
        "RGC_REQ_KEYS",
        "REQ_TAG_ATTRS",
        "CUSTOM_BAR_FMT",
        "API_VERSION",
        "API_VERSION_2",
        "TAG_NAME_CHAR_WHITELIST",
        "CONF_STRUCTURE",
        "OPERATION_IDS",
        "CUSTOM_PFX",
        "PRIVATE_API",
        "HOOKS",
        "DEFAULT_CONFIG_SCHEMA",
        "DEFAULT_ASSET_CLASS_SCHEMA",
    ]
    + FILE_DIR_NAMES
    + CFG_CONST
    + CFG_KEY_NAMES
    + API_IDS
    + HOOK_NAMES
)

CONF_STRUCTURE = """
# example genome configuration structure
{version}: {v}
{folder}: $GENOMES
{recipe_folder}: $GENOMES/recipes
{asset_class_folder}: $GENOMES/asset_classes
{server}: http://localhost
{archive}: /path/to/archives

{genomes}:
    fcdd62cb90e86d03e45dcd05efa70d8bdc9577d5c6259cf5:
        {aliases}: ['hg38']
        {desc_genome}: Reference assembly GRCh38, released in Dec 2013
        {assets}:
            fasta:
                {default}: tag_name
                {asset_class}: fasta
                {desc_asset}: DNA sequences in the FASTA format, indexed FASTA (produced with samtools index) and chromosome sizes file
                {tags}:
                    tag_name:
                        {asset_path}: fasta
                        {archive_digest}: 35ae9a42c36c126f9d8ef6d938a122d0
                        {asset_digest}: 3aff393d290884336945534ea709d30e
                        {asset_size}: 3.0GB
                        {archive_size}: 938.3MB
                        {custom_props}:
                            prop1: value1
                        {date_asset}: 2020-02-02
                        {asset_parents}:[]
                        {asset_children}: []
                        {seek_keys}:
                            fasta: fcdd62cb90e86d03e45dcd05efa70d8bdc9577d5c6259cf5.fa.gz
                            fai: fcdd62cb90e86d03e45dcd05efa70d8bdc9577d5c6259cf5.fa.fai
                            chrom_sizes: fcdd62cb90e86d03e45dcd05efa70d8bdc9577d5c6259cf5.chrom.sizes

{recipes}:
    fasta:
        version: 0.1.0
        source: 'self-added'
{asset_classes}:
    fasta:
        version: 0.1.0
        source: 'self-added'

""".format(
    folder=CFG_FOLDER_KEY,
    recipe_folder=CFG_RECIPE_FOLDER_KEY,
    asset_class_folder=CFG_ASSET_CLASS_FOLDER_KEY,
    server=CFG_SERVERS_KEY,
    version=CFG_VERSION_KEY,
    assets=CFG_ASSETS_KEY,
    archive=CFG_ARCHIVE_KEY,
    digest=CFG_CHECKSUM_KEY,
    genomes=CFG_GENOMES_KEY,
    recipes=CFG_RECIPES_KEY,
    asset_classes=CFG_ASSET_CLASSES_KEY,
    aliases=CFG_ALIASES_KEY,
    desc_genome=CFG_GENOME_DESC_KEY,
    asset_path=CFG_ASSET_PATH_KEY,
    desc_asset=CFG_ASSET_DESC_KEY,
    date_asset=CFG_ASSET_DATE_KEY,
    custom_props=CFG_ASSET_CUSTOM_PROPS_KEY,
    archive_digest=CFG_ARCHIVE_CHECKSUM_KEY,
    asset_size=CFG_ASSET_SIZE_KEY,
    archive_size=CFG_ARCHIVE_SIZE_KEY,
    seek_keys=CFG_SEEK_KEYS_KEY,
    asset_parents=CFG_ASSET_PARENTS_KEY,
    asset_children=CFG_ASSET_CHILDREN_KEY,
    default=CFG_ASSET_DEFAULT_TAG_KEY,
    asset_class=CFG_ASSET_CLASS_KEY,
    tags=CFG_ASSET_TAGS_KEY,
    asset_digest=CFG_ASSET_CHECKSUM_KEY,
    tag_description=CFG_TAG_DESC_KEY,
    v=REQ_CFG_VERSION,
)
