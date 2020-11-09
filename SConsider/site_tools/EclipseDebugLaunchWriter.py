"""SConsider.site_tools.EclipseDebugLaunchWriter.

Eclipse-SConsider-specific tool to create an Eclipse debug launch
configuration file.  This can be used to start a target in debug mode
through Run->Debug Configurations...->targetname.
"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2011, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

from __future__ import with_statement
import os
from SCons.Action import Action
from SCons.Builder import Builder
from SCons.Script import AddOption, GetOption


def generateLaunchConfigFile(launchConfigFile, env, binpath):
    launchConfigXml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<launchConfiguration type="org.eclipse.cdt.launch.remoteApplicationLaunchType">
<stringAttribute key="org.eclipse.cdt.dsf.gdb.PORT" value="2345"/>
<stringAttribute key="org.eclipse.cdt.launch.PROGRAM_NAME" value="%(binpath)s"/>
</launchConfiguration>""" % locals()
    launchConfigFile.write(launchConfigXml)


def generateEclipseLaunchEmitter(target, source, env):
    workspacePath = os.path.abspath(GetOption("workspace"))
    debugLaunchesPath = os.path.join(workspacePath, '.metadata', '.plugins', 'org.eclipse.debug.core',
                                     '.launches')
    target = []
    for src in source:
        target.append(
            env.Dir(debugLaunchesPath).File(
                os.path.splitext(os.path.basename(src.get_abspath()))[0] + '.launch'))
    return (target, source)


def generateEclipseLaunchConfiguration(target, source, env):
    for t, s in zip(target, source):
        with open(str(t), 'w') as launchConfigFile:
            generateLaunchConfigFile(launchConfigFile, env, s.get_abspath())
    return 0


def generate(env):
    import optparse
    try:
        AddOption('--workspace',
                  dest='workspace',
                  action='store',
                  default='',
                  help='Select workspace directory')
    except optparse.OptionConflictError:
        pass

    GenerateEclipseDebugLaunchConfigAction = Action(generateEclipseLaunchConfiguration,
                                                    "Creating Eclipse debug launch config for '$TARGET'")
    GenerateEclipseDebugLaunchConfigBuilder = Builder(action=[GenerateEclipseDebugLaunchConfigAction],
                                                      emitter=[generateEclipseLaunchEmitter])
    env.Append(BUILDERS={'GenerateEclipseDebugLaunchConfigBuilder': GenerateEclipseDebugLaunchConfigBuilder})


def exists(env):
    return True
