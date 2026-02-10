import pytest

from refgenconf.seqcol import *

DEMO_FILES = ["demo.fa.gz", "demo2.fa", "demo3.fa", "demo4.fa", "demo5.fa.gz"]

EXPECTED_DIGESTS = [
    ("demo.fa.gz", "d24aef468c774f9648fe0b65a87d641cc6d3357567736a40"),
    ("demo2.fa", "cf92cb36628154be6148dffe4497f3055c1418ae43fed4a6"),
    ("demo3.fa", "e2db4b89150696f09df4e357bb23c56a09faef60df91306e"),
    ("demo4.fa", "4182c2a1f78418764abf2923de03cabc26a106b73d63027c"),
    ("demo5.fa.gz", "d24aef468c774f9648fe0b65a87d641cc6d3357567736a40"),
]

CMP_SETUP = [
    (
        (
            CONTENT_ALL_A_IN_B
            + CONTENT_ALL_B_IN_A
            + LENGTHS_ALL_A_IN_B
            + LENGTHS_ALL_B_IN_A
            + NAMES_ALL_A_IN_B
            + NAMES_ALL_B_IN_A
            + CONTENT_A_ORDER
            + CONTENT_B_ORDER
            + CONTENT_ANY_SHARED
            + NAMES_ANY_SHARED
            + LENGTHS_ANY_SHARED
        ),
        DEMO_FILES[1],
        DEMO_FILES[1],
    ),
    (
        (
            CONTENT_ALL_A_IN_B
            + LENGTHS_ALL_A_IN_B
            + NAMES_ALL_A_IN_B
            + CONTENT_A_ORDER
            + CONTENT_B_ORDER
            + CONTENT_ANY_SHARED
            + LENGTHS_ANY_SHARED
            + NAMES_ANY_SHARED
        ),
        DEMO_FILES[0],
        DEMO_FILES[1],
    ),
    (
        (
            LENGTHS_ALL_B_IN_A
            + CONTENT_ALL_B_IN_A
            + CONTENT_ANY_SHARED
            + LENGTHS_ANY_SHARED
            + CONTENT_A_ORDER
            + CONTENT_B_ORDER
        ),
        DEMO_FILES[2],
        DEMO_FILES[4],
    ),
]


class TestSCCGeneral:
    def test_no_schemas_required(self):
        """
        In contrast to the generic Henge object, SeqColClient does not
        require schemas as input, they are predefined in the constructor
        """
        assert isinstance(SeqColClient({}), SeqColClient)


class TestSCCFastaInserting:
    @pytest.mark.parametrize("fasta_name", DEMO_FILES)
    def test_fasta_loading_works(self, fasta_name, fasta_path):
        scc = SeqColClient({})
        f = os.path.join(fasta_path, fasta_name)
        print("Fasta file to be loaded: {}".format(f))
        res = scc.load_fasta(f, gzipped=fasta_name.endswith(".gz"))
        assert len(res) == 2  # returns digest and list of AnnotatedSequencesList


class TestSCCRetrieval:
    @pytest.mark.parametrize("fasta_name", DEMO_FILES)
    def test_retrieval_works(self, fasta_name, fasta_path):
        scc = SeqColClient({})
        f = os.path.join(fasta_path, fasta_name)
        print("Fasta file to be loaded: {}".format(f))
        d, asds = scc.load_fasta(f, gzipped=fasta_name.endswith(".gz"))
        # convert integers in the dicts to strings
        lst = [
            {k: str(v) if isinstance(v, int) else v for k, v in asd.items()}
            for asd in asds
        ]
        assert scc.retrieve(d) == lst


class TestSCCCompare:
    @pytest.mark.parametrize(["code", "fasta1", "fasta2"], CMP_SETUP)
    def test_fasta_compare(self, code, fasta1, fasta2, fasta_path):
        scc = SeqColClient({})
        d, _ = scc.load_fasta(
            os.path.join(fasta_path, fasta1), gzipped=fasta1.endswith(".gz")
        )
        d2, _ = scc.load_fasta(
            os.path.join(fasta_path, fasta2), gzipped=fasta2.endswith(".gz")
        )
        assert scc.compare(d, d2) == code


class TestDigestPinning:
    @pytest.mark.parametrize(["fasta_name", "expected_digest"], EXPECTED_DIGESTS)
    def test_fasta_digest_value(self, fasta_name, expected_digest, fasta_path):
        scc = SeqColClient({})
        f = os.path.join(fasta_path, fasta_name)
        d, _ = scc.load_fasta(f, gzipped=fasta_name.endswith(".gz"))
        assert d == expected_digest

    def test_trunc512_digest(self):
        assert (
            trunc512_digest("test")
            == "ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f"
        )
