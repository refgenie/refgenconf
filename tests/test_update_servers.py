""" Tests for updating a configuration object's genome_servers section """

import pytest
from refgenconf.const import *


class TestUpdateServers:
    @pytest.mark.parametrize("urls", ["www.new_url.com"])
    def test_add_basic(self, my_rgc, urls):
        my_rgc.subscribe(urls=urls)
        assert urls in my_rgc[CFG_SERVERS_KEY]

    @pytest.mark.parametrize("urls", [1, ["a", 1]])
    def test_faulty_url(self, my_rgc, urls):
        with pytest.raises(TypeError):
            my_rgc.subscribe(urls=urls)

    @pytest.mark.parametrize("urls", [["www.new_url.com", "www.url.pl"]])
    def test_multiple_urls(self, my_rgc, urls):
        my_rgc.subscribe(urls=urls)
        assert urls[0] in my_rgc[CFG_SERVERS_KEY] and \
               urls[1] in my_rgc[CFG_SERVERS_KEY]

    @pytest.mark.parametrize("urls", [["www.new_url.com", "www.new_url.com"]])
    def test_reset(self, my_rgc, urls):
        my_rgc.subscribe(urls=urls, reset=True)
        assert len(my_rgc[CFG_SERVERS_KEY]) == 1

    @pytest.mark.parametrize("urls", [["http://refgenomes.databio.org"]])
    def test_reset(self, my_rgc, urls):
        my_rgc.subscribe(urls=urls, reset=True)
        assert len(my_rgc[CFG_SERVERS_KEY]) == 1

    @pytest.mark.parametrize("urls", [["http://refgenomes.databio.org"]])
    def test_unsubscribe(self, my_rgc, urls):
        my_rgc.subscribe(urls=urls)
        my_rgc.unsubscribe(urls=urls)
        assert len(my_rgc[CFG_SERVERS_KEY]) == 0

    @pytest.mark.parametrize("urls", [["http://refge"], ["what"]])
    def test_unsubscribe_invalid(self, my_rgc, urls):
        my_rgc.subscribe(urls=["http://refgenomes.databio.org"])
        servers = my_rgc[CFG_SERVERS_KEY]
        my_rgc.unsubscribe(urls=urls)
        assert my_rgc[CFG_SERVERS_KEY] == servers
