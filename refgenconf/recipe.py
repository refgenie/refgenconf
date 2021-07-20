import logging
import os
from functools import cached_property
from json import dump
from subprocess import check_output
from typing import Dict, List

import jinja2
from attmap.attmap import AttMap
from jsonschema.validators import validate
from rich.console import Console
from rich.table import Table
from yacman.yacman import load_yaml

from .asset import AssetClass, asset_class_factory, make_asset_class_path
from .const import DEFAULT_RECIPE_SCHEMA

_LOGGER = logging.getLogger(__name__)


class Recipe:
    def __init__(
        self,
        name: str,
        output_asset_class: AssetClass,
        command_template_list: List[str],
        inputs: Dict[Dict[Dict[str, str], str], str],
        description: str = None,
        container: str = None,
        custom_properties: Dict[str, str] = None,
        default_tag: str = None,
    ):
        self.name = name
        self.output_class = output_asset_class
        self.command_template_list = command_template_list
        self.inputs = inputs
        self.description = description or self.name
        self.container = container
        self.custom_properties = custom_properties or {}
        self.default_tag = default_tag

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
            "output_class": self.output_class.name,
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
            dump(self.to_dict(), f, indent=4)

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
                key: check_output(commands, shell=True)
                for key, commands in self.custom_properties.items()
            }
            if self.custom_properties
            else {}
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
                    input_data.get("description", ""),
                    str(input_data.get("default", "")),
                    f"--{input_type} {input_name}={input_data.get('default', 'value')}",
                )
        # comment out below
        c = Console()
        c.print(table)
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
    recipe_definition_file: str,
    recipe_schema_file: str = DEFAULT_RECIPE_SCHEMA,
    asset_class_definition_file_dir: str = None,
) -> Recipe:
    # read recipe definition file
    recipe_data = load_yaml(recipe_definition_file)
    # read recipe schema
    recipe_schema = load_yaml(recipe_schema_file)
    # validate recipe definition file
    validate(recipe_data, recipe_schema)
    # remove output_class from recipe data
    asset_class_name = recipe_data.pop("output_asset_class", None)
    asset_class = asset_class_factory(
        asset_class_definition_file=make_asset_class_path(
            asset_class_name, asset_class_definition_file_dir
        )
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
        variable_start_string="{",
        variable_end_string="}",
    )
    templ_obj = env.from_string(template)
    try:
        rendered = templ_obj.render(**namespaces)
    except jinja2.exceptions.UndefinedError as e:
        _LOGGER.error("Error populating command template: " + str(e))
        _LOGGER.debug(f"({', '.join(list(namespaces.keys()))}) missing for ")
        _LOGGER.debug(f"Template: '{template}'")
        raise e
    _LOGGER.debug("rendered command: {}".format(rendered))
    return rendered
