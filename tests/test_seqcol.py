import pytest
from refgenconf.seqcol import *

DEMO_FILES = ["demo.fa.gz", "demo2.fa", "demo3.fa", "demo4.fa", "demo5.fa.gz"]

CMP_SETUP = [((CONTENT_ALL_A_IN_B + CONTENT_ALL_B_IN_A + LENGTHS_ALL_A_IN_B + LENGTHS_ALL_B_IN_A + NAMES_ALL_A_IN_B + NAMES_ALL_B_IN_A + TOPO_ALL_B_IN_A + TOPO_ALL_A_IN_B + CONTENT_A_ORDER + CONTENT_B_ORDER), DEMO_FILES[1], DEMO_FILES[1]),
             ((CONTENT_ALL_A_IN_B + LENGTHS_ALL_A_IN_B + NAMES_ALL_A_IN_B + TOPO_ALL_A_IN_B + TOPO_ALL_B_IN_A + CONTENT_A_ORDER + CONTENT_B_ORDER), DEMO_FILES[0], DEMO_FILES[1]),
             ((LENGTHS_ALL_A_IN_B + LENGTHS_ALL_B_IN_A + TOPO_ALL_A_IN_B + TOPO_ALL_B_IN_A), DEMO_FILES[2], DEMO_FILES[4])]


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
        res = scc.load_fasta(f)
        assert len(res) == 2  # returns digest and list of AnnotatedSequencesList


class TestSCCRetrieval:
    @pytest.mark.parametrize("fasta_name", DEMO_FILES)
    def test_retrieval_works(self, fasta_name, fasta_path):
        scc = SeqColClient({})
        f = os.path.join(fasta_path, fasta_name)
        print("Fasta file to be loaded: {}".format(f))
        d, asds = scc.load_fasta(f)
        # convert integers in the dicts to strings
        lst = [{k: str(v) if isinstance(v, int) else v for k, v in asd.items()} for asd in asds]
        assert scc.retrieve(d) == lst


class TestSCCCompare:
    @pytest.mark.parametrize(["code", "fasta1", "fasta2"], CMP_SETUP)
    def test_fasta_compare(self, code, fasta1, fasta2, fasta_path):
        scc = SeqColClient({})
        d, _ = scc.load_fasta(os.path.join(fasta_path, fasta1))
        d2, _ = scc.load_fasta(os.path.join(fasta_path, fasta2))
        assert scc.compare(d, d2) == code
