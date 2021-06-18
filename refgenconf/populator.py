# refgenie looper plugin

import logging
import re
from collections.abc import Mapping

from attmap import AttMap
from ubiquerg import parse_registry_path as prp

import refgenconf

_LOGGER = logging.getLogger(__name__)


def looper_refgenie_populate(namespaces):
    """
    A looper plugin that populates refgenie references in a PEP from
    refgenie://genome/asset:tag registry paths. This can be used to convert
    all refgenie references into their local paths at the looper stage, so the
    final paths are passed to the workflow. This way the workflow does not
    need to depend on refgenie to resolve the paths.
    This is useful for example for CWL pipelines, which are built to have
    paths resolved outside the workflow.

    The namespaces structure required to run the plugin is:
    `namespaces["pipeline"]["var_templates"]["refgenie_config"]`

    :param Mapping namespaces: a nested variable namespaces dict
    :return dict: sample namespace dict
    :raises TypeError: if the input namespaces is not a mapping
    :raises KeyError: if the namespaces mapping does not include 'pipeline'
    :raises NotImplementedError: if 'var_templates' key is missing in the 'pipeline' namespace or
        'refgenie_config' is missing in 'var_templates' section.
    """
    if not isinstance(namespaces, Mapping):
        raise TypeError("Namespaces must be a Mapping")
    if "pipeline" not in namespaces:
        raise KeyError(
            "Namespaces do not include 'pipeline'. The job is misconfigured."
        )
    if (
        "var_templates" in namespaces["pipeline"]
        and "refgenie_config" in namespaces["pipeline"]["var_templates"]
    ):
        rgc_path = namespaces["pipeline"]["var_templates"]["refgenie_config"]
        rgc = refgenconf.RefGenConf(rgc_path)

        if not "genome" in namespaces["sample"]:
            _LOGGER.error(
                "Refgenie plugin requires samples to have a 'genome' attribute."
            )
            raise KeyError

        complete_seek_key_dict = rgc.list_seek_keys_values(
            genomes=namespaces["sample"]["genome"]
        )

        genome_seek_key_dict = complete_seek_key_dict[namespaces["sample"]["genome"]]
        paths_dict = {}

        # This function allows you to specify tags for specific assets to use
        # in the project config like:
        # refgenie_asset_tags:
        #   asset_name: tag_name
        def get_asset_tag(asset):
            try:
                return namespaces["project"]["refgenie_asset_tags"][asset]
            except:
                return "default"

        # Restructure the seek key paths to make them accessible with
        # {refgenie.asset_name.seek_key} in command templates
        for k, v in genome_seek_key_dict.items():
            tag = get_asset_tag(k)
            # print(k,v)
            try:
                paths_dict[k] = v[tag]
            except KeyError:
                _LOGGER.warn(f"Can't find tag '{tag}' for asset '{k}'. Using default")
                paths_dict[k] = v["default"]

        # print(paths_dict)
        # Provide these values under the 'refgenie' namespace
        namespaces["refgenie"] = AttMap(paths_dict)

        return rgc.populate(namespaces)
    else:
        msg = """
        var_templates:
          refgenie_config: "$REFGENIE"
        """
        _LOGGER.error(
            f"refgenie_config not specified in pipeline interface. Do like so: {msg}"
        )
        raise NotImplementedError
