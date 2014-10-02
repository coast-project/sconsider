import DoxygenBuilder


def test_AliasesList():
    assert r'FIXME=\xrefitem FIXME "Fixme" "Locations to fix when possible" ' == DoxygenBuilder.parseDoxyfileContent(
        r'ALIASES = "FIXME=\xrefitem FIXME \"Fixme\" \"Locations to fix when possible\" "',
        {},
        None)['ALIASES']
    assert r'\xrefitem FIXME "Fixme" "Locations to fix when possible" ' == DoxygenBuilder.parseDoxyfileContent(
        r'ALIASES = FIXME="\xrefitem FIXME \"Fixme\" \"Locations to fix when possible\" "',
        {},
        None)['ALIASES']

if __name__ == "__main__":
    test_AliasesList()
