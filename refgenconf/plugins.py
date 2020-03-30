""" Plugin functions """

import pkg_resources
from .const import HOOKS

__all__ = ["plugins"]

plugins = {}
for hook in HOOKS:
    plugins[hook] = \
        {entry_point.name: entry_point.load() for entry_point in
         pkg_resources.iter_entry_points('refgenie.hooks.' + hook)}
