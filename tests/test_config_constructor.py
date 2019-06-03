""" Tests for basic functionality of the RefGenConf constructor """

import pytest
from refgenconf import RefGenConf, MissingConfigDataError
from refgenconf.const import CFG_FOLDER_KEY, CFG_SERVER_KEY


@pytest.mark.parametrize("missing", [
    [CFG_FOLDER_KEY], [CFG_SERVER_KEY], [CFG_FOLDER_KEY, CFG_SERVER_KEY]])
def test_missing_config(tmpdir, missing):
    """ Omission of required config items causes expected exception """
    base_data = [(CFG_SERVER_KEY, "http://localhost"),
                 (CFG_FOLDER_KEY, tmpdir.strpath)]
    data = {k: v for k, v in base_data if k not in missing}
    with pytest.raises(MissingConfigDataError) as err_ctx:
        RefGenConf(data)
    err_msg = str(err_ctx.value)
    missing_from_msg = [v for v in missing if v not in err_msg]
    assert [] == missing_from_msg
