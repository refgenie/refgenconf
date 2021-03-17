# refgenie looper plugin

import logging
import refgenconf
import re

from ubiquerg import parse_registry_path as prp

_LOGGER = logging.getLogger(__name__)


def looper_refgenie_plugin(namespaces):
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
    rgc_path = namespaces["pipeline"]["var_templates"]["refgenie_config"]
    rgc = refgenconf.RefGenConf(rgc_path)
    return populate_refgenie_refs(rgc, namespaces)


# Example code:
# import refgenconf as RGC
# rgc = RGC.RefGenConf("/home/nsheff/Dropbox/env/refgenie_config/zither.yaml")
# rgc.seek("hg19", "fasta")
# demo = {"genome": 'refgenie://hg19/fasta',
#         "other_attr": "something",
#         "bt2": 'refgenie://t7/bowtie2_index'}
# nested_demo = {"top_level_attr": "refgenie://t7/fasta",
#                 "other_top_attr": "don't do anything to this",
#                 "nested_dict": demo }
# populate_refgenie_refs(rgc, demo)
# populate_refgenie_refs(rgc, nested_demo)


def populate_refgenie_refs(rgc, glob):
    """
    Populates refgenie references from refgenie://genome/asset:tag registry paths

    :param RefGenConf rgc: A RefGenConf object to use to populate the paths
    :param (dict | str) glob: String which may contain refgenie registry paths as
        values; or a dict, for which values may contain refgenie registry
        paths. Dict include nested dicts.
    :return dict: modified input dict with refgenie paths populated
    """
    p = re.compile("refgenie://([A-Za-z0-9_/\.]+)?")

    if isinstance(glob, str):
        m = p.match(glob)
        it = re.finditer(p, glob)
        for m in it:
            reg_path = m.group()
            # print(m)
            # print(reg_path)
            rgpkg = prp(reg_path)
            if not rgpkg:
                _LOGGER.info(
                    "Can't convert non-conforming refgenie registry path: {}".format(
                        reg_path
                    )
                )
                return glob
            rgpath = rgc.seek(
                rgpkg["namespace"], rgpkg["item"], rgpkg["tag"], rgpkg["subitem"]
            )
            glob = re.sub(reg_path, rgpath, glob)
        return glob
    elif isinstance(glob, dict):
        for k, v in glob.items():
            # print(k, v)
            if k.startswith("_"):
                continue
            if k.startswith("sources"):
                continue  # derived attribute sources
            glob[k] = populate_refgenie_refs(rgc, v)
            # if k == "project": continue
        return glob
    else:
        _LOGGER.error("Refgenie can only populate str or dict objects.")
        return glob
