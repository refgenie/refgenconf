""" config file structure determination for the refgenie project """

CFG_ENV_VARS = ["REFGENIE"]
CFG_NAME = "genome configuration"

CFG_FOLDER_KEY = "genome_folder"
CFG_SERVER_KEY = "genome_server"
CFG_GENOMES_KEY = "genomes"

CFG_ASSET_PATH_KEY = "path"
CFG_ASSET_SIZE_KEY = "asset_size"
CFG_ARCHIVE_KEY = "genome_archive"
CFG_ARCHIVE_SIZE_KEY = "archive_size"
CFG_CHECKSUM_KEY = "archive_checksum"
CFG_SINGLE_ASSET_SECTION_KEYS = [
    CFG_ASSET_PATH_KEY, CFG_ASSET_SIZE_KEY, CFG_ARCHIVE_KEY,
    CFG_ARCHIVE_SIZE_KEY, CFG_CHECKSUM_KEY]

CFG_KEY_NAMES = [
    "CFG_FOLDER_KEY", "CFG_SERVER_KEY", "CFG_GENOMES_KEY",
    "CFG_ASSET_PATH_KEY", "CFG_ARCHIVE_KEY", "CFG_ARCHIVE_SIZE_KEY",
    "CFG_ASSET_SIZE_KEY", "CFG_CHECKSUM_KEY"]
CFG_CONST = ["CFG_ENV_VARS", "CFG_NAME"]

DEFAULT_SERVER = "http://refgenomes.databio.org"

"""
# example genome configuration structure

{folder}: $GENOMES
{server}: http://localhost
{archive}: /path/to/archives

{genomes}:
  hg38:
    bowtie2:
      {path}: indexed_bowtie2
      {checksum}: mm20349234n20349280345mv2035
      {asset_size}: 32G
      {archive_size}: 7G
""".format(folder=CFG_FOLDER_KEY, server=CFG_SERVER_KEY,
           archive=CFG_ARCHIVE_KEY, genomes=CFG_GENOMES_KEY,
           path=CFG_ASSET_PATH_KEY, checksum=CFG_CHECKSUM_KEY,
           asset_size=CFG_ASSET_SIZE_KEY, archive_size=CFG_ARCHIVE_SIZE_KEY)
