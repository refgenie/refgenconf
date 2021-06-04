# refgenie looper plugin

import logging
import re

from ubiquerg import parse_registry_path as prp
from attmap import AttMap
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

    :param dict namespaces: variable namespaces dict
    :return dict: sample namespace dict
    """
    if (
        "var_templates" in namespaces["pipeline"]
        and "refgenie_config" in namespaces["pipeline"]["var_templates"]
    ):
        rgc_path = namespaces["pipeline"]["var_templates"]["refgenie_config"]
        rgc = refgenconf.RefGenConf(rgc_path)

        # Populate a dict with paths for the given sample's genome
        # paths_dict = {}
        # for a in rgc.list_assets_by_genome(g):
        #     paths_dict[a] = rgc.seek(g, a, "default")

        paths_dict = rgc.list_seek_keys_values(genomes=namespaces["sample"]["genome"])

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
