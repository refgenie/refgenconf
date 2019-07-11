"""
Config file structure determination for the refgenie suite of packages

These values are defined here in refgenconf and use some within this package,
but they're also integral to both refgenie and to refgenieserver.
"""
# config file structure related consts

CFG_NAME = "genome configuration"
CFG_ENV_VARS = ["REFGENIE"]
CFG_CONST = ["CFG_NAME", "CFG_ENV_VARS"]
DEFAULT_SERVER = "http://refgenomes.databio.org"

CFG_FOLDER_KEY = "genome_folder"
CFG_SERVER_KEY = "genome_server"
CFG_ARCHIVE_KEY = "genome_archive"
CFG_VERSION_KEY = "config_version"
CFG_GENOMES_KEY = "genomes"

CFG_GENOME_DESC_KEY = "genome_description"
CFG_ASSETS_KEY = "assets"

CFG_ASSET_PATH_KEY = "path"
CFG_ASSET_SIZE_KEY = "asset_size"
CFG_ASSET_DESC_KEY = "asset_description"
CFG_ARCHIVE_SIZE_KEY = "archive_size"
CFG_CHECKSUM_KEY = "archive_checksum"

CFG_TOP_LEVEL_KEYS = [
    CFG_FOLDER_KEY, CFG_SERVER_KEY, CFG_ARCHIVE_KEY, CFG_GENOMES_KEY, CFG_VERSION_KEY]
CFG_GENOME_KEYS = [
    CFG_GENOME_DESC_KEY, CFG_ASSETS_KEY]
CFG_SINGLE_ASSET_SECTION_KEYS = [
    CFG_ASSET_PATH_KEY, CFG_ASSET_DESC_KEY, CFG_ASSET_SIZE_KEY, CFG_ARCHIVE_SIZE_KEY, CFG_CHECKSUM_KEY]

CFG_KEY_NAMES = [
    "CFG_FOLDER_KEY", "CFG_SERVER_KEY", "CFG_GENOMES_KEY",
    "CFG_ASSET_PATH_KEY", "CFG_ASSET_DESC_KEY", "CFG_ARCHIVE_KEY", "CFG_ARCHIVE_SIZE_KEY",
    "CFG_ASSET_SIZE_KEY", "CFG_CHECKSUM_KEY", "CFG_VERSION_KEY"]


"""
# example genome configuration structure
{version}: 0.2
{folder}: $GENOMES
{server}: http://localhost
{archive}: /path/to/archives

{genomes}:
  hg38:
    {desc_genome}: Reference assembly GRCh38, released in Dec 2013
    {checksum}: mm20349234n20349280345df5035
    {assets}:
        bowtie2:
          {path}: indexed_bowtie2
          {desc_asset}: Genome index for bowtie2, produced with bowtie2-build
          {checksum}: mm20349234n20349280345mv2035
          {asset_size}: 32G
          {archive_size}: 7G
""".format(folder=CFG_FOLDER_KEY, server=CFG_SERVER_KEY, version=CFG_VERSION_KEY, assets=CFG_ASSETS_KEY,
           archive=CFG_ARCHIVE_KEY, genomes=CFG_GENOMES_KEY, desc_genome=CFG_GENOME_DESC_KEY,
           path=CFG_ASSET_PATH_KEY, desc_asset=CFG_ASSET_DESC_KEY, checksum=CFG_CHECKSUM_KEY,
           asset_size=CFG_ASSET_SIZE_KEY, archive_size=CFG_ARCHIVE_SIZE_KEY)

# other consts
REQ_CFG_VERSION = 0.2

__all__ = CFG_CONST + CFG_KEY_NAMES + ["DEFAULT_SERVER", "CFG_KEY_NAMES", "CFG_GENOME_DESC_KEY", "REQ_CFG_VERSION", "CFG_ASSETS_KEY"]
