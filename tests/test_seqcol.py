import os

import pytest

from refgenconf.seqcol import fasta_seqcol_digest, trunc512_digest

EXPECTED_DIGESTS = [
    ("demo.fa.gz", "d24aef468c774f9648fe0b65a87d641cc6d3357567736a40"),
    ("demo2.fa", "cf92cb36628154be6148dffe4497f3055c1418ae43fed4a6"),
    ("demo3.fa", "e2db4b89150696f09df4e357bb23c56a09faef60df91306e"),
    ("demo4.fa", "4182c2a1f78418764abf2923de03cabc26a106b73d63027c"),
    ("demo5.fa.gz", "d24aef468c774f9648fe0b65a87d641cc6d3357567736a40"),
]


class TestDigestPinning:
    @pytest.mark.parametrize(["fasta_name", "expected_digest"], EXPECTED_DIGESTS)
    def test_fasta_digest_value(self, fasta_name, expected_digest, fasta_path):
        f = os.path.join(fasta_path, fasta_name)
        d, _ = fasta_seqcol_digest(f, gzipped=fasta_name.endswith(".gz"))
        assert d == expected_digest

    def test_trunc512_digest(self):
        assert (
            trunc512_digest("test")
            == "ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f"
        )
