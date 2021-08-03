import os
from json import dump as jdump
from typing import Any, Dict, List

from jsonschema import validate
from ubiquerg import is_url
from yacman import load_yaml
from yaml import dump as ydump

from .const import DEFAULT_ASSET_CLASS_SCHEMA, TEMPLATE_ASSET_CLASS_YAML


class AssetClass:
    pass


class AssetClass:
    def __init__(
        self,
        name: str,
        version: str,
        seek_keys: Dict[str, str],
        description: str = None,
        parents: List[AssetClass] = None,
    ):
        self.name = name
        self.version = version
        self.parents = parents or []
        self.seek_keys = {}
        if self.parents:
            for parent in self.parents:
                self.seek_keys.update(parent.seek_keys)
        self.seek_keys.update(seek_keys)
        self.seek_keys.update({"dir": "."})
        self.description = description or self.name

    def __str__(self) -> str:
        from textwrap import indent

        repr = f"{self.__class__.__name__}: {self.name}"
        repr += f"\nDescription: {self.description}"
        repr += f"\nSeek keys:"
        for key, value in self.seek_keys.items():
            repr += indent(f"\n{key}: {value}", "  ")
        if self.parents:
            repr += f"\nParents: {', '.join([parent.name for parent in self.parents])}"
        return repr

    def to_dict(self) -> Dict[str, Any]:
        # don't include the automatic dir seek key
        temp_seek_keys = self.seek_keys.copy()
        temp_seek_keys.pop("dir", None)
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "seek_keys": temp_seek_keys,
            "parents": [parent.name for parent in self.parents],
        }

    def to_json(self, filepath) -> None:
        """
        Save the asset class to a JSON file

        :param str filepath: The filepath to save the asset class to
        """
        with open(filepath, "w") as f:
            jdump(self.to_dict(), f, indent=4)

    def to_yaml(self, filepath) -> None:
        """
        Save the asset class to a YAML file

        :param str filepath: The filepath to save the asset class to
        """
        with open(filepath, "w") as f:
            ydump(self.to_dict(), f, default_flow_style=False)


def asset_class_factory(
    asset_class_definition_file: str = None,
    asset_class_schema_file: str = DEFAULT_ASSET_CLASS_SCHEMA,
    asset_class_definition_dict: Dict[str, Any] = None,
    asset_class_definition_file_dir: str = None,
) -> AssetClass:
    """
    Read yaml file and return a AssetClass object

    :param str asset_class_definition_file: path/URL to yaml file that defines the asset class
    :param str asset_class_schema_file: path/URL to schema file to validate against (optional)
    :return AssetClass: AssetClass object
    :raises FileNotFoundError: if asset_class_definition_file does not exist
    """
    # check asset class definition if file exists
    if (
        asset_class_definition_file is not None
        and not os.path.isfile(asset_class_definition_file)
        and not is_url(asset_class_definition_file)
    ):
        raise FileNotFoundError(
            f"Asset class definition file not found: {asset_class_definition_file}"
        )

    if not os.path.isfile(asset_class_schema_file) and not is_url(
        asset_class_schema_file
    ):
        raise FileNotFoundError(
            f"Asset class schema file not found: {asset_class_schema_file}"
        )
    # read asset class defintion file or use provided dict
    asset_class_data = asset_class_definition_dict or load_yaml(
        asset_class_definition_file
    )
    # read schema file
    asset_class_schema = load_yaml(asset_class_schema_file)
    # validate asset class definition
    validate(schema=asset_class_schema, instance=asset_class_data)
    # remove parents from asset class definition
    asset_class_parents = asset_class_data.pop("parents", None)
    # recursively create asset class parent objects
    parent_objects = []
    if asset_class_parents:
        # get file directory to look for parent asset classes in
        if (
            asset_class_definition_file_dir is None
            and asset_class_definition_file is None
        ):
            raise ValueError(
                f"Must provide asset class definition file or file directory since "
                f"{asset_class_data['name']} asset class has parents"
            )

        file_dir = asset_class_definition_file_dir or (
            os.path.dirname(asset_class_definition_file)
            if not is_url(asset_class_definition_file)
            else None
        )
        parent_objects = [
            asset_class_factory(
                asset_class_definition_file=make_asset_class_path(
                    class_src=asset_class_parent, dir=file_dir
                ),
                asset_class_schema_file=asset_class_schema_file,
            )
            for asset_class_parent in asset_class_parents
        ]
    # create top asset class object
    return AssetClass(parents=parent_objects, **asset_class_data)


def make_asset_class_path(class_src: str, dir: str = None) -> str:
    """
    Return and absolute path/URL of an asset class definition file

    :param str path: path/URL to the asset class definition file
    :return str: absolute path/URL to the asset class definition file
    """
    if is_url(class_src):
        return class_src
    class_file_name = (
        class_src
        if class_src.endswith(TEMPLATE_ASSET_CLASS_YAML.replace("{}", ""))
        else TEMPLATE_ASSET_CLASS_YAML.format(class_src)
    )
    if os.path.isabs(class_file_name):
        return class_file_name
    return (
        os.path.join(dir, os.path.basename(class_file_name))
        if dir
        else os.path.abspath(class_file_name)
    )
