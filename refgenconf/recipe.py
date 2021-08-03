import logging
from functools import cached_property
from json import dump as jdump
from subprocess import check_output
from typing import Any, Dict, List

import jinja2
from attmap.attmap import AttMap
from jsonschema.validators import validate
from rich.table import Table
from yacman.yacman import load_yaml
from yaml import dump as ydump

from .asset import AssetClass, asset_class_factory, make_asset_class_path
from .const import DEFAULT_RECIPE_SCHEMA
from .exceptions import MissingAssetClassError

_LOGGER = logging.getLogger(__name__)


class Recipe:
    def __init__(
        self,
        name: str,
        version: str,
        output_asset_class: AssetClass,
        command_template_list: List[str],
        inputs: Dict[Dict[Dict[str, str], str], str],
        description: str = None,
        container: str = None,
        custom_properties: Dict[str, str] = None,
        default_tag: str = None,
        checksum_exclude_list: List[str] = None,
    ):
        self.name = name
        self.version = version
        self.output_class = output_asset_class
        self.command_template_list = command_template_list
        # set up inputs dict, which accounts for missing keys in the recipe
        self.inputs = {
            "files": inputs.get("files"),
            "params": inputs.get("params"),
            "assets": inputs.get("assets"),
        }
        self.description = description or self.name
        self.container = container
        self.custom_properties = custom_properties or {}
        self.default_tag = default_tag
        self.checksum_exclude_list = checksum_exclude_list or []

    def __str__(self) -> str:
        repr = f"{self.__class__.__name__}: {self.name} -> {self.output_class.name}"
        repr += f"\nDescription: {self.description}"
        return repr

    def to_dict(self) -> Dict[str, str]:
        """
        Convert the recipe to a dictionary

        :return Dict[str, str]: A dictionary representation of the recipe
        """
        # TODO: should we include the seek_keys as it was before? They are a part of asset class now.
        return {
            "name": self.name,
            "version": self.version,
            "output_asset_class": self.output_class.name,
            "description": self.description,
            "inputs": self.inputs,
            "container": self.container,
            "command_template_list": self.command_template_list,
            "custom_properties": self.custom_properties,
            "default_tag": self.default_tag,
        }

    def to_json(self, filepath) -> None:
        """
        Save the recipe to a JSON file

        :param str filepath: The filepath to save the recipe to
        """
        with open(filepath, "w") as f:
            jdump(self.to_dict(), f, indent=4)

    def to_yaml(self, filepath) -> None:
        """
        Save the recipe to a YAML file

        :param str filepath: The filepath to save the recipe to
        """
        with open(filepath, "w") as f:
            ydump(self.to_dict(), f, default_flow_style=False)

    @cached_property
    def required_assets(self) -> Dict[str, Dict[str, str]]:
        """
        Return a collection of required assets for this recipe.

        :return Dict[str, Dict[str, str]]: required assets
        """
        return self.inputs["assets"] or {}

    @cached_property
    def required_files(self) -> Dict[str, Dict[str, str]]:
        """
        Return a collection of required files for this recipe.

        :return Dict[str, Dict[str, str]]: required files
        """
        return self.inputs["files"] or {}

    @cached_property
    def required_params(self) -> Dict[str, Dict[str, str]]:
        """
        Return a collection of required params for this recipe.

        :return Dict[str, Dict[str, str]]: required params
        """
        return self.inputs["params"] or {}

    @cached_property
    def resolved_custom_properties(self):
        """
        Resolve custom properties

        :return Dict[str, str]: A dictionary of custom properties
        """
        return (
            {
                key: check_output(commands, shell=True).decode("utf-8").strip()
                for key, commands in self.custom_properties.items()
            }
            if self.custom_properties
            else {}
        )

    def resolve_default_tag(self, namespaces: AttMap) -> str:
        """
        Resolve the default tag

        :param attmap.Attmap namespaces: A mapping of template values organized in namespaces
        :return str: The default tag
        """
        return (
            jinja_render_template_strictly(self.default_tag, namespaces)
            if self.default_tag
            else None
        )

    @cached_property
    def requirements(self):
        msg = f"{self.name} recipe requirements:\n"
        for input_type, input_id in self.inputs.items():
            if input_id is None:
                continue
            msg += f"\n{input_type}:"
            for input_name, input_data in input_id.items():
                msg += f"\n  - {input_name}"
                if "description" in input_data:
                    msg += f" ({input_data['description']})"
                if "default" in input_data:
                    msg += f"; default: {input_data['default']}"
        return msg

    @cached_property
    def requirements_table(self):
        table = Table(title=f"{self.name} recipe requirements")
        table.add_column("Type")
        table.add_column("ID")
        table.add_column("Description", style="italic")
        table.add_column("Default value")
        table.add_column("Argument pattern")
        for input_type, input_element in self.inputs.items():
            if input_element is None:
                continue

            for input_name, input_data in input_element.items():
                table.add_row(
                    input_type,
                    input_name,
                    input_data.get("description", "[dim]None[/dim]"),
                    str(input_data.get("default", "[dim]None[/dim]")),
                    f"--{input_type} {input_name}={input_data.get('default', '[dim]<value>[/dim]')}",
                )
        return table

    def populate_command_templates(self, namespaces: AttMap) -> List[str]:
        """
        Populate the command templates

        :param attmap.Attmap namespaces: A mapping of template values organized in namespaces
        :return List[str]: A list of populated command templates
        """
        return [
            jinja_render_template_strictly(cmd, namespaces)
            for cmd in self.command_template_list
        ]


def recipe_factory(
    recipe_definition_file: str = None,
    recipe_schema_file: str = DEFAULT_RECIPE_SCHEMA,
    asset_class_definition_file_dir: str = None,
    recipe_definition_dict: Dict[str, Any] = None,
) -> Recipe:
    """
    Factory method to create a recipe from a definition file

    :param str recipe_definition_file: The recipe definition file
    :param str recipe_schema_file: The recipe schema file
    :param str asset_class_definition_file_dir: The directory containing the asset class definition files
    :param Dict[str, Dict[str, Any]] recipe_definition_dict: A dictionary of recipe definition
    :return refgenconf.recipe.Recipe: A recipe
    :raises MissingAssetClassError: If the asset class definition file is missing
    """
    # read recipe definition file or use a provided dictionary
    recipe_data = recipe_definition_dict or load_yaml(recipe_definition_file)
    # read recipe schema
    recipe_schema = load_yaml(recipe_schema_file)
    # validate recipe definition file
    validate(recipe_data, recipe_schema)
    # remove output_class from recipe data
    asset_class_name = recipe_data.pop("output_asset_class", None)
    try:
        asset_class = asset_class_factory(
            asset_class_definition_file=make_asset_class_path(
                asset_class_name, asset_class_definition_file_dir
            )
        )
    except FileNotFoundError:
        raise MissingAssetClassError(
            f"Asset class '{asset_class_name}' not found. You need to add/pull the asset class first."
        )
    return Recipe(output_asset_class=asset_class, **recipe_data)


def jinja_render_template_strictly(template, namespaces):
    """
    Render a command string in the provided namespaces context.

    Strictly, which means that all the requested attributes must be
    available in the namespaces

    :param str template: command template do be filled in with the
        variables in the provided namespaces. For example:
        "prog.py --name {params.name} --len {inputs.len}"
    :param Mapping[Mapping[str] namespaces: context for command rendering.
        Example namespaces are: inputs, params
    :return str: rendered command
    """
    env = jinja2.Environment(
        undefined=jinja2.StrictUndefined,
        # variable_start_string="{",
        # variable_end_string="}",
    )
    templ_obj = env.from_string(template)
    try:
        rendered = templ_obj.render(**namespaces)
    except jinja2.exceptions.UndefinedError as e:
        _LOGGER.error(f"Error populating command template: {str(e)}")
        _LOGGER.info(f"Template: '{template}'")
        raise e
    _LOGGER.debug(f"Rendered template: {rendered}")
    return rendered
