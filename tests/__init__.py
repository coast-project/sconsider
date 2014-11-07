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
maindir = os.path.realpath(
    os.path.join(
        os.path.dirname(__file__),
        '../SConsider'))
sys.path += [maindir, os.path.join(maindir, 'site_tools')]
