""" Tests for RefGenConf.initialize_config_file """

import os
import shutil
import tempfile

import pytest

from refgenconf import RefGenConf


class TestInitialize:
    def test_init_exists(self):
        rgc = RefGenConf()
        tf = tempfile.NamedTemporaryFile(prefix="/tmp/", suffix=".yaml")
        with pytest.raises(OSError, match="file exists"):
            rgc.initialize_config_file(filepath=tf.name)

    def test_init_nonwritable(self):
        rgc = RefGenConf()
        with pytest.raises(OSError, match="insufficient permissions"):
            rgc.initialize_config_file(filepath="/test.yaml")

    def test_init_success(self):
        rgc = RefGenConf()
        dirpath = tempfile.mkdtemp(prefix="/tmp/")
        cfg_file_path = os.path.join(dirpath, "test.yaml")
        rgc.initialize_config_file(filepath=cfg_file_path)
        assert os.path.exists(cfg_file_path)
        shutil.rmtree(dirpath)

    @pytest.mark.parametrize("pth", [None, 1, {"a": "b"}])
    def test_invalid_path(self, pth):
        rgc = RefGenConf()
        with pytest.raises(TypeError):
            rgc.initialize_config_file(filepath=pth)
