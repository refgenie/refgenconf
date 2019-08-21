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
DEFAULT_TAG_NAME = "default"

CFG_FOLDER_KEY = "genome_folder"
CFG_SERVER_KEY = "genome_server"
CFG_ARCHIVE_KEY = "genome_archive"
CFG_VERSION_KEY = "config_version"
CFG_GENOMES_KEY = "genomes"

CFG_CHECKSUM_KEY = "genome_checksum"
CFG_GENOME_DESC_KEY = "genome_description"
CFG_ASSETS_KEY = "asset_packages"

CFG_ASSET_PATH_KEY = "asset_path"
CFG_ASSET_SIZE_KEY = "asset_size"
CFG_ASSET_DESC_KEY = "asset_description"
CFG_ARCHIVE_SIZE_KEY = "archive_size"
CFG_ARCHIVE_CHECKSUM_KEY = "archive_checksum"
CFG_SEEK_KEYS_KEY = "seek_keys"
CFG_ASSET_PARENTS_KEY = "asset_parents"
CFG_ASSET_CHILDREN_KEY = "asset_children"


CFG_TOP_LEVEL_KEYS = [
    CFG_FOLDER_KEY, CFG_SERVER_KEY, CFG_ARCHIVE_KEY, CFG_GENOMES_KEY, CFG_VERSION_KEY]
CFG_GENOME_KEYS = [
    CFG_GENOME_DESC_KEY, CFG_ASSETS_KEY, CFG_CHECKSUM_KEY]
CFG_GENOME_ATTRS_KEYS = [CFG_GENOME_DESC_KEY, CFG_CHECKSUM_KEY]
CFG_SINGLE_ASSET_SECTION_KEYS = [CFG_ASSET_PATH_KEY, CFG_ASSET_DESC_KEY, CFG_ASSET_SIZE_KEY, CFG_ARCHIVE_SIZE_KEY, CFG_ARCHIVE_CHECKSUM_KEY, CFG_SEEK_KEYS_KEY]

CFG_KEY_NAMES = [
    "CFG_FOLDER_KEY", "CFG_SERVER_KEY", "CFG_GENOMES_KEY",
    "CFG_ASSET_PATH_KEY", "CFG_ASSET_DESC_KEY", "CFG_ARCHIVE_KEY", "CFG_ARCHIVE_SIZE_KEY", "CFG_SEEK_KEYS_KEY",
    "CFG_ASSET_SIZE_KEY", "CFG_CHECKSUM_KEY", "CFG_ARCHIVE_CHECKSUM_KEY", "CFG_VERSION_KEY", "CFG_ASSET_PARENTS_KEY",
    "CFG_ASSET_CHILDREN_KEY"]


"""
# example genome configuration structure
{version}: 0.3
{folder}: $GENOMES
{server}: http://localhost
{archive}: /path/to/archives

{genomes}:
    hg38:
        {desc_genome}: Reference assembly GRCh38, released in Dec 2013
        {checksum}: 1110349234n20349280345df5035
        {assets}:
            fasta:
                default:
                    {asset_path}: fasta
                    {desc_asset}: Genome index for bowtie2, produced with bowtie2-build
                    {archive_checksum}: 2220349234n20349280345mv2035
                    {asset_size}: 32G
                    {archive_size}: 7G
                    {asset_parents}:
                    {asset_children}: ["bowtie2_index.bowtie2_index:default"]
                    {seek_keys}:
                        fasta: hg38.fa.gz
                        fai: hg38.fa.fai
                        chrom_sizes: sizes.txt
                old_version:
                    {asset_path}: fasta
                    {desc_asset}: Genome index for bowtie2, produced with bowtie2-build
                    {archive_checksum}: 4545n49234n2034928dmasn4n5jn5
                    {asset_size}: 32G
                    {archive_size}: 7G
                    {seek_keys}:
                        fasta: hg38.fa.gz
                        fai: hg38.fa.fai
                        chrom_sizes: sizes.txt
""".format(folder=CFG_FOLDER_KEY, server=CFG_SERVER_KEY, version=CFG_VERSION_KEY, assets=CFG_ASSETS_KEY,
           archive=CFG_ARCHIVE_KEY, checksum=CFG_CHECKSUM_KEY, genomes=CFG_GENOMES_KEY,
           desc_genome=CFG_GENOME_DESC_KEY, asset_path=CFG_ASSET_PATH_KEY, desc_asset=CFG_ASSET_DESC_KEY,
           archive_checksum=CFG_ARCHIVE_CHECKSUM_KEY, asset_size=CFG_ASSET_SIZE_KEY, archive_size=CFG_ARCHIVE_SIZE_KEY,
           seek_keys=CFG_SEEK_KEYS_KEY, asset_parents=CFG_ASSET_PARENTS_KEY, asset_children=CFG_ASSET_CHILDREN_KEY)

# other consts
REQ_CFG_VERSION = 0.3
REFGENIE_BY_CFG = {"0.3": "0.6.1", "0.2": "0.6.0"}  # should probably switch to 0.7.0

__all__ = CFG_CONST + CFG_KEY_NAMES + ["DEFAULT_SERVER", "DEFAULT_TAG_NAME", "CFG_KEY_NAMES", "CFG_GENOME_DESC_KEY",
                                       "REQ_CFG_VERSION", "CFG_ASSETS_KEY", "CFG_GENOME_ATTRS_KEYS", "REFGENIE_BY_CFG"]
