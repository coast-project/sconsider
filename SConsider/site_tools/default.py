"""SConsider.site_tools.default.

SConsider-specific default initialization tool - postpones
SCons.Tool.default loading  -> see setupBuildTools for details

-> see setupBuildTools for details
"""

# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------


def generate(env):
    """Postpone adding default tools, see setupBuildTools for
    implementation."""
    pass


def exists(env):
    return True
