""" Tests for ReferenceGenomeConfiguration.get_asset """

import os
import pytest
from refgenconf import *
from refgenconf.const import CFG_ASSETS_KEY
from tests.conftest import bind_to_assets, get_conf_genomes, \
    lift_into_path_pair, CONF_DATA, \
    HG38_DATA, MM10_DATA, MITO_DATA
from veracitools import ExpectContext

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


@pytest.fixture
def temp_asset_spec(tmpdir):
    """ Provide test case with a temp asset path. """
    fn = "semaphore.txt"
    fp = tmpdir.join(fn).strpath
    assert not os.path.exists(fp)
    return fp


@pytest.mark.parametrize(
    "gname", ["not-a-genome", "this_should_fail", "YoUrCrazeeOrganism"])
@pytest.mark.parametrize("aname", [
    "kallisto", "hisat2", "tss_annotation", "gtf", "bowtie2", "blacklist",
    "bowtie", "star"])
def test_get_asset_missing_genome(rgc, gname, aname):
    """ Request for asset on a missing genome raises appropriate error. """
    assert gname not in rgc
    with pytest.raises(MissingGenomeError):
        _get_asset(rgc, gname, aname)


@pytest.mark.parametrize("gname", get_conf_genomes())
@pytest.mark.parametrize("aname", ["not-an-asset", "asset_fails"])
def test_get_asset_missing_asset(rgc, gname, aname):
    """ Request for unknown asset raises appropriate error. """
    assert gname in rgc.genomes
    with pytest.raises(MissingAssetError):
        _get_asset(rgc, gname, aname)


@pytest.mark.parametrize(
    ["gname", "aname", "exp"],
    [(g, k, v) for g, data in
     [("hg38", HG38_DATA), ("mm10", MM10_DATA), ("rCRSd", MITO_DATA)]
     for k, v in data])
def test_get_asset_accuracy(rgc, gname, aname, exp):
    """ Asset request for particular genome is accurate. """
    assert exp == _get_asset(rgc, gname, aname)


@pytest.mark.parametrize("check_exist", [lambda: True, lambda _1, _2: True])
@pytest.mark.parametrize(
    ["gname", "aname"], [(g, a) for g, data in CONF_DATA for a in data])
def test_check_exist_param_type(rgc, check_exist, gname, aname):
    """ The asset existence check must be a one-arg function. """
    with pytest.raises(TypeError):
        rgc.get_asset(gname, aname, check_exist=check_exist)


@pytest.mark.parametrize(
    ["strict", "ctxmgr", "error"],
    [(False, pytest.warns, RuntimeWarning), (True, pytest.raises, IOError)])
def test_existence_check_strictness(rgc, temp_asset_spec, strict, ctxmgr, error):
    """ Asset existence check behavior responds to strictness parameter. """
    gname, aname = "tmpgen", "testasset"
    rgc.genomes[gname] = bind_to_assets({aname: lift_into_path_pair(temp_asset_spec)})
    def fetch():
        return _get_asset(rgc, gname, aname, strict_exists=strict)
    with ctxmgr(error):
        fetch()
    with open(temp_asset_spec, 'w'):
        pass
    try:
        fetch()
    except Exception as e:
        pytest.fail(str(e))


@pytest.mark.parametrize(
    ["check_exist", "get_exp_from_path"],
    [(os.path.isfile, lambda p: p), (os.path.isdir, lambda _: IOError)])
def test_existence_check_function(
        rgc, check_exist, get_exp_from_path, temp_asset_spec):
    """ Asset existence check behavior responds to existence checker. """
    gname, aname = "tmpgen", "testasset"
    rgc.genomes[gname] = bind_to_assets({aname: lift_into_path_pair(temp_asset_spec)})
    with open(temp_asset_spec, 'w'):
        pass
    with ExpectContext(get_exp_from_path(temp_asset_spec), _get_asset) as ctx:
        ctx(rgc, gname, aname, check_exist=check_exist, strict_exists=True)


@pytest.mark.parametrize(["extension", "exp_in_msg"], [
    (".tar", True), (".tar.gz", True), (".untar", False)])
@pytest.mark.parametrize(["strict", "ctx", "err", "get_msg"], [
    (False, pytest.warns, RuntimeWarning, lambda r: str(r[0])),
    (True, pytest.raises, IOError, lambda r: str(r.value))])
def test_tar_check(rgc, temp_asset_spec, extension, strict, ctx, err, get_msg,
                   exp_in_msg):
    """ Asset fetch checks for TAR variant of true asset path value. """
    gname, aname = "tmpgen", "testasset"
    rgc.genomes[gname] = bind_to_assets({aname: lift_into_path_pair(temp_asset_spec)})
    tarpath = temp_asset_spec + extension
    with open(tarpath, 'w'):
        pass
    with ctx(err) as rec:
        _get_asset(rgc, gname, aname, strict_exists=strict)
    assert (tarpath in get_msg(rec)) is exp_in_msg


@pytest.mark.parametrize("strict_exists", [None, False, True])
def test_asset_already_exists(tmpdir, strict_exists):
    """ Asset path is joined to genome folder and returned if it exists. """
    genome = "mm10"
    a_key = "chrom_sizes"
    a_path = "Mus_musculus.contig_lengths"
    cfgdat = {
        CFG_FOLDER_KEY: tmpdir.strpath,
        CFG_SERVER_KEY: DEFAULT_SERVER,
        CFG_GENOMES_KEY: {genome: bind_to_assets({a_key: {CFG_ASSET_PATH_KEY: a_path}})}}
    rgc = RefGenConf(cfgdat)
    assert a_path == rgc[CFG_GENOMES_KEY][genome][CFG_ASSETS_KEY][a_key][CFG_ASSET_PATH_KEY]
    assert not os.path.exists(a_path)
    def folder():
        return rgc[CFG_FOLDER_KEY]
    assert tmpdir.strpath == folder()
    fullpath = os.path.join(folder(), genome, a_path)
    if not os.path.exists(os.path.dirname(fullpath)):
        os.makedirs(os.path.dirname(fullpath))
    print("Writing: {}".format(fullpath))
    with open(fullpath, 'w'):
        assert os.path.isfile(fullpath)
    assert fullpath == rgc.get_asset(genome, a_key, strict_exists=strict_exists)


def _get_asset(rgc, g, a, **kwargs):
    """
    Call the asset fetch function.

    :param refgenconf.RefGenConf rgc: configuration instance
    :param str g: genome name
    :param str a: asset name
    """
    kwds = {"strict_exists": None}
    kwds.update(kwargs)
    return rgc.get_asset(g, a, **kwds)
