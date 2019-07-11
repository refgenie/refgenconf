# """ Tests regarding unboudn environment variables in a genome config file. """
#
# import os
# import pytest
# from refgenconf import CFG_FOLDER_KEY, UnboundEnvironmentVariablesError as UEVErr
# from tests.conftest import get_get_url, REQUESTS
#
# __author__ = "Vince Reuter"
# __email__ = "vreuter@virginia.edu"
#
#
# @pytest.mark.parametrize(["genome", "asset"], REQUESTS)
# @pytest.mark.parametrize("evs", [["NOT_A_VAR"], ["NOT_A_VAR", "RANDNAME"]])
# def test_missing_env_vars_in_genome_config_path_raises_exception(
#         rgc, tmpdir, evs, genome, asset, gencfg, remove_genome_folder):
#     """ Unbound env var(s) in genome folder path cause error. """
#     assert all(_is_unbound(v) for v in evs)
#     path_parts = ["$" + v for v in [tmpdir.strpath] + evs]
#     path = os.path.join(*path_parts)
#     print("Genome folder path: {}".format(path))
#     rgc[CFG_FOLDER_KEY] = path
#     assert path == rgc[CFG_FOLDER_KEY]
#     assert not os.path.exists(path)
#     with pytest.raises(UEVErr) as err_ctx:
#         rgc.pull_asset(genome, asset, gencfg,
#                        get_main_url=get_get_url(genome, asset))
#     err_msg = str(err_ctx.value)
#     print("Observed error message: {}".format(err_msg))
#     missing = [v for v in evs if v not in err_msg]
#     assert [] == missing
#
#
# def _is_unbound(ev):
#     return os.getenv(ev) is None and ev not in os.environ
