""" config file structure determination for the refgenie project """

CFG_ENV_VARS = ["REFGENIE"]
CFG_NAME = "genome configuration"
CFG_GENOMES_KEY = "genomes"
CFG_SERVER_KEY = "genome_server"
CFG_ASSET_PATH_KEY = "path"
CFG_ARCHIVE_KEY = "genome_archive"
CFG_FOLDER_KEY = "genome_folder"
CFG_ARCHIVE_SIZE_KEY = "archive_size"
CFG_ASSET_SIZE_KEY = "asset_size"
CFG_CHECKSUM_KEY = "archive_checksum"

CFG_KEY_NAMES = ["CFG_GENOMES_KEY", "CFG_ASSET_PATH_KEY", "CFG_ARCHIVE_KEY", "CFG_FOLDER_KEY", "CFG_ARCHIVE_SIZE_KEY",
                 "CFG_ASSET_SIZE_KEY", "CFG_CHECKSUM_KEY"]
CFG_CONST = ["CFG_ENV_VARS", "CFG_NAME"]

"""
# example genome configuration structure

CFG_FOLDER_KEY: $GENOMES
CFG_SERVER_KEY: http://localhost
CFG_ARCHIVE_KEY: /path/to/archives

CFG_GENOMES_KEY:
  hg38:
    bowtie2:
      CFG_ASSET_PATH_KEY: indexed_bowtie2
      CFG_CHECKSUM_KEY: mm20349234n20349280345mv2035
      CFG_ASSET_SIZE_KEY: 32G
      CFG_ARCHIVE_SIZE_KEY: 7G
"""