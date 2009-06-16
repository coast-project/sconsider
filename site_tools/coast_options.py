import os, platform, pdb, traceback
import SCons
from SCons.Script import AddOption, Dir, GetOption, Flatten

added = None

def generate(env, **kw):
    global added
    if not added:
        added = 1
        AddOption('--enable-Trace', dest='Trace', action='store_true', help='enable webdisplay tracing (StartTrace, Trace,...), see Dbg.h for details')
    env.AppendUnique(CPPDEFINES=['_LARGEFILE64_SOURCE'])
    #FIXME: how shall we handle debug/opt-wddbg/opt compilations?
    env.AppendUnique(CPPDEFINES=['WD_OPT'])
    if GetOption('Trace'):
        env.AppendUnique(CPPDEFINES=['DEBUG'])

def exists(env):
    return true
