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

def populate_refgenie_refs(rgc, vardict):
    """
    Populates refgenie references from refgenie://genome/asset:tag registry paths

    :param RefGenConf rgc: A RefGenConf object to use to populate the paths
    :param dict vardict: dict which may contain refgenie registry paths as
    :values. Dict include nested dicts.
    :return dict: modified input dict with refgenie paths populated
    """
    p = re.compile('refgenie://(.*)')

    vardict
    for k,v in vardict.items():
        # print(k, v)
        if k.startswith("_"): continue
        # if k == "project": continue
        if isinstance(v, dict):
            vardict[k] = populate_refgenie_refs(rgc, v)
        elif isinstance(v, str):
            m = p.match(v)
            if m:
                reg_path = m.group()
                # print(reg_path)
                rgpkg = prp(reg_path)
                if not rgpkg:
                    print("Can't convert non-conforming refgenie registry path: {}".format(reg_path))
                    continue
                rgpath = rgc.seek(rgpkg["namespace"], rgpkg["item"], rgpkg["tag"], rgpkg["subitem"])
                vardict[k] = rgpath

    return vardict
