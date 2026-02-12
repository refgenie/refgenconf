import binascii
import hashlib
import logging
from gzip import open as gzopen
from typing import Any

_LOGGER = logging.getLogger(__name__)

NAME_KEY = "name"
SEQ_KEY = "sequence"
LEN_KEY = "length"

# Serialization delimiters (must match original Henge schema serialization)
DELIM_ATTR = ">"  # separating attributes in an item
DELIM_ITEM = ","  # separating items in a collection


def trunc512_digest(seq: str, offset: int = 24) -> str:
    digest = hashlib.sha512(seq.encode()).digest()
    hex_digest = binascii.hexlify(digest[:offset])
    return hex_digest.decode()


def _serialize_asd(asd: dict[str, Any]) -> str:
    """Serialize an annotated sequence digest to a string.

    Property order must be: name, length, sequence (matching the original
    schema's properties key order used by Henge's build_attr_string).
    """
    return DELIM_ATTR.join([str(asd[k]) for k in [NAME_KEY, LEN_KEY, SEQ_KEY]])


def fasta_seqcol_digest(
    fa_file: str, skip_seq: bool = False, gzipped: bool = False
) -> tuple[str, list[dict[str, Any]]]:
    """Compute a sequence collection digest from a FASTA file.

    Args:
        fa_file: Path to the FASTA file to parse.
        skip_seq: Whether to disregard the actual sequences, load
            just the names and lengths.
        gzipped: Whether the FASTA file is gzipped.

    Returns:
        A tuple of (collection_digest, list of annotated sequence dicts).
    """
    seq = ""
    name = ""
    init = False
    aslist = []
    openfun = gzopen if gzipped else open
    with openfun(fa_file, "rt") as f:
        for line in f:
            line = line.strip("\n")
            if line.startswith(">"):
                if not init:
                    name = line.replace(">", "")
                else:
                    aslist.append(
                        {
                            NAME_KEY: name,
                            LEN_KEY: len(seq),
                            SEQ_KEY: "" if skip_seq else trunc512_digest(seq),
                        }
                    )
                    name = line.replace(">", "")
                seq = ""
                continue
            init = True
            seq = seq + line
        aslist.append(
            {
                NAME_KEY: name,
                LEN_KEY: len(seq),
                SEQ_KEY: "" if skip_seq else trunc512_digest(seq),
            }
        )

    item_digests = [trunc512_digest(_serialize_asd(asd)) for asd in aslist]
    collection_digest = trunc512_digest(DELIM_ITEM.join(item_digests))
    _LOGGER.info(f"Computed seqcol digest ({len(aslist)} sequences)")
    return collection_digest, aslist
