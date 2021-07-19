import os
from typing import Dict
from jsonschema import validate
from yacman import load_yaml
from ubiquerg import is_url

from typing import List, Dict

from .const import DEFAULT_ASSET_CLASS_SCHEMA


class AssetClass:
    pass


class AssetClass:
    def __init__(
        self,
        class_name: str,
        seek_keys: Dict[str, str],
        description: str = None,
        parents: List[AssetClass] = None,
    ):
        self.class_name = class_name
        self.parents = parents or []
        self.seek_keys = {}
        if self.parents:
            for parent in self.parents:
                self.seek_keys.update(parent.seek_keys)
        self.seek_keys.update(seek_keys)
        self.description = description or self.class_name

    def __str__(self) -> str:
        from textwrap import indent

        repr = f"{self.__class__.__name__}: {self.class_name}"
        repr += f"\nDescription: {self.description}"
        repr += f"\nSeek keys:"
        for key, value in self.seek_keys.items():
            repr += indent(f"\n{key}: {value}", "  ")
        if self.parents:
            repr += f"\nParents: {', '.join([parent.class_name for parent in self.parents])}"
        return repr


def asset_class_factory(
    asset_class_definition_file: str,
    asset_class_schema_file: str = DEFAULT_ASSET_CLASS_SCHEMA,
) -> AssetClass:
    """
    Read yaml file and return a AssetClass object

    :param str asset_class_definition_file: path/URL to yaml file that defines the asset class
    :param str asset_class_schema_file: path/URL to schema file to validate against (optional)
    :return AssetClass: AssetClass object
    """
    # read asset class defintion
    print(f"Reading asset class definition: {asset_class_definition_file}")
    asset_class_data = load_yaml(asset_class_definition_file)
    # check if file exists
    if not os.path.isfile(asset_class_definition_file):
        raise FileNotFoundError(
            f"Asset class definition file not found: {asset_class_definition_file}"
        )
    # read schema file
    asset_class_schema = load_yaml(asset_class_schema_file)
    # validate asset class definition
    validate(schema=asset_class_schema, instance=asset_class_data)
    # remove parents from asset class definition
    asset_class_parents = asset_class_data.pop("parents", None)
    # get file directory to look for parent asset classes in
    file_dir = (
        os.path.dirname(asset_class_definition_file)
        if not is_url(asset_class_definition_file)
        else None
    )
    # recursively create asset class parent objects
    parent_objects = []
    if asset_class_parents:
        parent_objects = [
            asset_class_factory(
                asset_class_definition_file=make_class_path(
                    class_src=asset_class_parent, dir=file_dir
                ),
                asset_class_schema_file=asset_class_schema_file,
            )
            for asset_class_parent in asset_class_parents
        ]
    # create top asset class object
    return AssetClass(parents=parent_objects, **asset_class_data)


def make_class_path(class_src: str, dir: str = None) -> str:
    """
    Return and absolute path/URL of an asset class definition file

    :param str path: path/URL to the asset class definition file
    :return str: absolute path/URL to the asset class definition file
    """
    if is_url(class_src):
        return class_src
    class_file_name = (
        class_src
        if class_src.endswith("_asset_class.yaml")
        else f"{class_src}_asset_class.yaml"
    )
    if os.path.isabs(class_file_name):
        return class_file_name
    return (
        os.path.join(dir, os.path.basename(class_file_name))
        if dir
        else os.path.abspath(class_file_name)
    )
