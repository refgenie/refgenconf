import os
import mock
from refgenconf import RefGenConf

__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"


def get_flag_pth(rgc):
    return os.path.join(os.path.dirname(rgc.file_path), "plugin.flag")


def set_flag(rgc):
    """
    Creates a flag file next to the genome configuration file.

    Useful for plugin system testing if one does not want to rely
    on printed messages to check plugin effect

    :param refgenconf.RefGenConf rgc: object to create the flag for
    """
    pth = get_flag_pth(rgc)
    if not os.path.exists(pth):
        write_flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        fd = os.open(pth, write_flags)
        os.close(fd)
        assert os.path.exists(pth)
        print("Created flag file: {}".format(pth))
    else:
        raise FileExistsError("Flag file already exists: {}".format(pth))


PLUGINS_DICT = {
    "pre_list": {"my_func": set_flag},
    "pre_pull": {},
    "pre_tag": {},
    "pre_update": {},
    "post_tag": {},
    "post_list": {},
    "post_pull": {},
    "post_update": {},
}


class TestPlugins:
    def test_prelist_plugins_called(self, cfg_file):
        with mock.patch(
            "refgenconf.refgenconf.RefGenConf.plugins", new_callable=mock.PropertyMock
        ) as mock_plugins:
            mock_plugins.return_value = PLUGINS_DICT
            rgc = RefGenConf(cfg_file, writable=False)
            rgc.list()
            assert get_flag_pth(rgc)
        os.remove(get_flag_pth(rgc))
        assert not os.path.exists(get_flag_pth(rgc))

    def test_plugin_entrypoints_scanning(self, ro_rgc):
        """
        Plugins property dynamically scans defined entrypoints in the packages
        in current Python environment. Properly defined ones are included in
        the plugins property return value
        """
        assert any([len(fun) > 0 for plugin, fun in ro_rgc.plugins.items()])
