# -------------------------------------------------------------------------
# Copyright (c) 2014, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import DoxygenBuilder


def test__AliasesList():
    assert r'FIXME=\xrefitem FIXME "Fixme" "Locations to fix when possible" ' == DoxygenBuilder.parseDoxyfileContent(
        r'ALIASES = "FIXME=\xrefitem FIXME \"Fixme\" \"Locations to fix when possible\" "',
        {}, None)['ALIASES']
    assert r'\xrefitem FIXME "Fixme" "Locations to fix when possible" ' == DoxygenBuilder.parseDoxyfileContent(
        r'ALIASES = FIXME="\xrefitem FIXME \"Fixme\" \"Locations to fix when possible\" "',
        {}, None)['ALIASES']


if __name__ == "__main__":
    test_AliasesList()
