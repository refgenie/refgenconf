import logging
import os
from functools import cached_property
from json import dump as jdump
from subprocess import check_output
from typing import Any, Dict, List

import jinja2
import requests
from attmap.attmap import AttMap
from jsonschema import ValidationError
from jsonschema.validators import validate
from rich.table import Table
from ubiquerg.web import is_url
from yacman.yacman import load_yaml
from yaml import dump as ydump

from .asset_class import AssetClass, asset_class_factory, make_asset_class_path
from .const import DEFAULT_RECIPE_SCHEMA
from .exceptions import MissingAssetClassError
from .helpers import validate_tag

_LOGGER = logging.getLogger(__name__)


class Recipe:
    """
    A representation of the recipe
    """

    def __init__(
        self,
        name: str,
        version: str,
        output_asset_class: AssetClass,
        command_template_list: List[str],
        inputs: Dict[Dict[Dict[str, str], str], str],
        test: Dict[Dict[Dict[str, str], str], str] = None,
        description: str = None,
        container: str = None,
        custom_properties: Dict[str, str] = None,
        default_tag: str = None,
        checksum_exclude_list: List[str] = None,
    ):
        """
        Initialize a recipe

        For convenience, use the `recipe_factory` function to create a recipes.

        :param str name: The name of the recipe
        :param str version: The version of the recipe
        :param AssetClass output_asset_class: The output asset class that the recipe will produce
        :param List[str] command_template_list: A list of command templates
        :param Dict[Dict[Dict[str, str], str], str] inputs: A dictionary of input values organized in namespaces
        :param str description: A description of the recipe
        :param str container: The container to use for running the recipe, e.g. 'databio/refgenie'
        :param Dict[str, str] custom_properties: A dictionary of custom properties to use/to resolve
        :param str default_tag: The default tag to use for the recipe/to resolve
        :param List[str] checksum_exclude_list: A list of filepaths to exclude from the checksum calculation
        """
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
        self.test = test
        self.description = description or self.name
        self.container = container
        self.custom_properties = custom_properties or {}
        self.default_tag = default_tag
        self.checksum_exclude_list = checksum_exclude_list or []

    def __str__(self) -> str:
        repr = f"{self.__class__.__name__}: {self.name} -> {self.output_class.name}"
        repr += f"\nDescription: {self.description}"
        return repr

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} '{self.name}'\n{self.to_dict()}"

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
            "test": self.test,
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

    def _run_cmd_in_container(self, cmd: str) -> str:
        """
        Run a command in the container

        :param str cmd: The command to run
        :return str: The output of the command
        """
        if self.container is None:
            raise ValueError("Container not set")

        get_id_cmd = f"docker run -itd --rm {self.container}"
        container_id = check_output(get_id_cmd, shell=True).decode("utf-8").strip()
        get_result_cmd = f"docker exec -it {container_id} {cmd}"
        return check_output(get_result_cmd, shell=True)

    def resolve_custom_properties(self, use_docker=False) -> Dict[str, Any]:
        """
        Resolve custom properties

        :param bool use_docker: If True, resolve custom properties in the container
        :return Dict[str, Any]: A dictionary of custom properties
        """
        return (
            {
                key: (
                    self._run_cmd_in_container(commands)
                    if use_docker
                    else check_output(commands, shell=True)
                )
                .decode("utf-8")
                .strip()
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
            validate_tag(jinja_render_template_strictly(self.default_tag, namespaces))
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

    def get_test_outputs(self) -> Dict[str, Dict[str, str]]:
        """
        Get all the outputs to test the recipe.

        :return Dict[str, Dict[str, str]]: A dictionary of test outputs
        """
        return self.test["outputs"] or {}

    def get_test_inputs(self, rgc=None) -> Dict[str, Dict[str, str]]:
        """
        Get all the inputs to test the recipe.

        This requires the inputs files to be specified as URLs.
        Asset and param type inputs cannot be overridden, the default values are used.

        :param RefGenConf rgc: A RefGenConf object to store the test data in.
            Conditionally required, if assets need to be pulled.
        :return Dict[str, Dict[str, str]]: A dictionary of test data
        """

        def download_file(url: str, filepath: str) -> None:
            """
            Download a file from a URL

            :param str url: The URL to download from
            :param str filepath: The filepath to save the file to
            :return str: The output filepath
            :raises ValueError: If the URL is not a valid URL
            """
            _LOGGER.info(f"Downloading recipe input {url} and saving to '{filepath}'")
            if url is None:
                raise ValueError(
                    f"No test URL provided for recipe input file: {file_id}"
                )
            if not is_url(url):
                raise ValueError(
                    f"'{url}' is not a valid URL. "
                    f"Use a remotely accessible file so that the recipe is portable."
                )
            if not os.path.exists(filepath):
                with open(filepath, "wb") as f:
                    f.write(requests.get(url).content)
            return filepath

        if self.test is None:
            raise ValueError(f"No tests specified for '{self.name}' recipe")

        resolved_inputs = {"files": {}, "assets": {}, "params": {}}

        if self.inputs["files"] is not None:
            if "files" not in self.test["inputs"]:
                raise ValueError(
                    "Test inputs must include a 'files' key for top-level recipes."
                )
            test_dir = os.path.join(rgc.data_dir, "_recipe_test", self.name)
            os.makedirs(test_dir, exist_ok=True)
            # download the required test files
            for file_id, url in self.test["inputs"]["files"].items():
                resolved_inputs["files"][file_id] = download_file(
                    url, os.path.join(test_dir, f"{file_id}_test_input")
                )

        if self.inputs["assets"] is not None:
            if rgc is None:
                raise ValueError(
                    "Test data cannot be pulled without a RefGenConf object."
                )
            if "genome" not in self.test:
                raise ValueError("Genome must be specified to test derived assets")
            for asset_id, asset_data in self.inputs["assets"].items():
                pth = rgc.seek(
                    genome_name=self.test["genome"],
                    asset_name=asset_data["default"],
                    tag_name=None,
                )
                _LOGGER.info(f"Using input asset: {pth}")
                resolved_inputs["assets"][asset_id] = pth

        if self.inputs["params"] is not None:
            for param_id, param_data in self.inputs["params"].items():
                resolved_inputs[param_id] = param_data["default"]

        return resolved_inputs


def recipe_factory(
    recipe_definition_file: str = None,
    recipe_schema_file: str = DEFAULT_RECIPE_SCHEMA,
    asset_class_definition_file_dir: str = None,
    recipe_definition_dict: Dict[str, Any] = None,
) -> Recipe:
    """
    Factory method to create a recipe from a definition file

    :param str recipe_definition_file: The recipe definition file. It can be a local file or a URL.
    :param Dict[str, Any] recipe_definition_dict: A dictionary of recipe definition data,
        overrides `recipe_definition_file` if specified.
    :param str recipe_schema_file: The recipe schema file. Default schema is used if not specified.
    :param str asset_class_definition_file_dir: The directory containing the asset class definition files
    :return refgenconf.recipe.Recipe: A recipe
    :raises MissingAssetClassError: If the asset class definition file is missing
    """
    # read recipe definition file or use a provided dictionary
    recipe_data = recipe_definition_dict or load_yaml(recipe_definition_file)
    # read recipe schema
    recipe_schema = load_yaml(recipe_schema_file)
    # validate recipe definition file
    try:
        validate(recipe_data, recipe_schema)
    except ValidationError as e:
        _LOGGER.error(f"Invalid {recipe_data.get('name', '')} recipe definition!")
        raise
    # remove output_class from recipe data
    asset_class_name = recipe_data.pop("output_asset_class", None)
    try:
        asset_class, _ = asset_class_factory(
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
