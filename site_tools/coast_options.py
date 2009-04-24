import os, platform, pdb, traceback
import SCons
from SCons.Script import AddOption, Dir, GetOption, Flatten

added = None

def generate(env, **kw):
    global added
    if not added:
        added = 1
        AddOption('--with-COAST-ROOT', dest='COAST-ROOT', action='store', nargs=1, type='string', default='#', metavar='DIR', help='location of COAST_ROOT directory, default is [' + Dir('#').abspath + ']')
        AddOption('--no-stdiostream', dest='no-stdiostream', action='store_true', help='Disable use of std libraries iostream headers')
    if not GetOption('no-stdiostream'):
        env.AppendUnique(CPPDEFINES=['ONLY_STD_IOSTREAM'])
    env.AppendUnique(CPPDEFINES=['_LARGEFILE64_SOURCE'])
    #FIXME: how shall we handle debug/opt-wddbg/opt compilations?
    env.AppendUnique(CPPDEFINES=['WD_OPT'])

def exists(env):
    return true
