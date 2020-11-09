"""SConsider.site_tools.SubstInFileBuilder.

Builder used to search/replace content in Files using regular expression
syntax
"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2010, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import re
from SCons.Action import Action
from SCons.Builder import Builder
from SCons.Script import Depends


def substInFile(target, source, searchre, subfn):
    with open(source, 'rU') as f:
        contents = f.read()

    contents = searchre.sub(subfn, contents)

    with open(target, 'wt') as f:
        f.write(contents)


def getLogMessage(target, source, env):
    items = [
        'Substituting vars from {source} to {target}'.format(source=str(s), target=str(t))
        for (t, s) in zip(target, source)
    ]
    return '\n'.join(items)


def getKeysFromFile(source, searchre):
    with open(source, 'rU') as f:
        content = f.read()
    return getKeysFromString(content, searchre)


def getKeysFromString(content, searchre):
    keys = []
    for match in searchre.finditer(content):
        key = match.group(1)
        if key != '':
            keys.append(key)
    return keys


def getData(keys, env):
    subst_dict = env.get('SUBST_DICT', env)

    data = {}
    for key in keys:
        if key in subst_dict:
            value = subst_dict[key]
            if callable(value):
                data[key] = env.subst(value(env=env))
            else:
                data[key] = env.subst(value)
    return data


def substituted_filename_emitter(target, source, env):
    from SCons.Node import FS, Python
    newTarget = []
    for (t, s) in zip(target, source):
        if isinstance(t, FS.Dir):
            newTarget.append(t.File(s.name))
        else:
            newTarget.append(t)
        keys = getKeysFromFile(str(s), getSearchRE(env))
        data = getData(keys, env)
        Depends(t, Python.Value(data))
        env.AlwaysBuild(newTarget)

    return (newTarget, source)


def getMarker(env):
    return env.get("SUBST_MARKER", "##")


def getSearchRE(env, marker=None):
    if not marker:
        marker = getMarker(env)
    return re.compile(env.get("SUBST_PATTERN", marker + '(.*?)' + marker))


def getSubFn(env, default):
    subfn = default
    if "SUBST_FN" in env and callable(env["SUBST_FN"]):
        subfn = env["SUBST_FN"]
    return subfn


def substInFiles(target, source, env):
    marker = getMarker(env)
    searchre = getSearchRE(env, marker)

    def subFnDefault(match, data):
        key = match.group(1)
        if key == '':
            return marker
        if key not in data:
            return match.group(0)
        return str(data[key])

    subfn = getSubFn(env, subFnDefault)

    keys = set()
    for s in source:
        keys.update(getKeysFromFile(str(s), searchre))
    data = getData(keys, env)

    for (t, s) in zip(target, source):
        substInFile(str(t), str(s), searchre, lambda match: subfn(match, data))


def generate(env):
    from SCons.Tool import install
    substInFileAction = Action(substInFiles, getLogMessage)
    substInFileBuilder = Builder(
        action=substInFileAction,
        emitter=[substituted_filename_emitter, install.add_targets_to_INSTALLED_FILES])
    env.Append(BUILDERS={'SubstInFileBuilder': substInFileBuilder})


def exists(env):
    return True
