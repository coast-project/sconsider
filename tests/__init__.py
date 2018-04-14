# -------------------------------------------------------------------------
# Copyright (c) 2014, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import sys
import os
import pkg_resources


def path_to_pkg(pkg_name, path_fallback=None):
    try:
        distro = pkg_resources.get_distribution(pkg_name)
        for i in [distro.key, distro.project_name]:
            for j in ['-' + distro.version, '']:
                path_to_module = os.path.join(distro.location, i + j)
                if os.path.isdir(path_to_module):
                    return path_to_module
    except pkg_resources.DistributionNotFound:
        pass
    return path_fallback if path_fallback is not None and os.path.isdir(path_fallback) else None


local_sconsider_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '../SConsider'))

effective_sconsider_path = path_to_pkg('sconsider', local_sconsider_path)
sys.path += [
    j for j in
    [effective_sconsider_path,
     os.path.join(effective_sconsider_path, 'site_tools'),
     path_to_pkg('scons')] if j
]
