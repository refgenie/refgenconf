class TestAliasTable:
    def test_alias_table_dimensions(self, my_rgc):
        assert len(my_rgc.genomes_list()) == my_rgc.genome_aliases_table.row_count
        assert len(my_rgc.genome_aliases_table.columns) == 2


class TestAssetTable:
    def test_asset_table_dimensions(self, my_rgc):
        assert my_rgc.genome_aliases_table.row_count == len(
            my_rgc.list_assets_by_genome()
        )
