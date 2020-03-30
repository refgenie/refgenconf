""" Plugin functions """

import pkg_resources

__all__ = ["plugins"]

# HOOKS is a list of all available plugin entry points
HOOKS = ["post_update", "pre_pull", "pre_tag", "pre_list"]

plugins = {}
for hook in HOOKS:
    plugins[hook] = { entry_point.name: entry_point.load() for entry_point 
        in pkg_resources.iter_entry_points('refgenie.hooks.' + hook) }
