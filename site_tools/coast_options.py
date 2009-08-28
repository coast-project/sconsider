import os, platform, pdb, traceback
import SCons
from SCons.Script import AddOption, Dir, GetOption, Flatten
import setupBuildTools

added = None

def generate(env, **kw):
    global added
    if not added:
        added = 1
        AddOption('--enable-Trace', dest='Trace', action='store_true', help='Compile enabling trace support, (StartTrace, Trace,...), see Dbg.h for details')

    # the following flag should only be set when not compiling in debug mode
    setupBuildTools.registerCallback('OPTIMIZE_OPTIONS', lambda env: env.AppendUnique(CPPDEFINES=['WD_OPT']) )

    if GetOption('Trace'):
        setupBuildTools.registerCallback('VARIANT_SUFFIX', lambda env: env.AppendUnique(VARIANT_SUFFIX=['_trace']) )
        env.AppendUnique(CPPDEFINES=['COAST_TRACE'])

def exists(env):
    return true
