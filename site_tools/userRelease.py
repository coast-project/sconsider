import os,platform,pdb,traceback
import SCons
from SCons.Script import AddOption

added = None

def generate(env, **kw):
    global added
    if not added:
        added = 1
        AddOption('--user-release', dest='userRelease', nargs=1, type='string', action='store', metavar='FILE', help='Creates a compressed user release and stores it in FILE')
    ##################
    # Create release #
    ##################
    if env.GetOption('userRelease'):
        if env['PLATFORM'] != 'win32':
            env['TARFLAGS']+=' -z'
            env.Default(env.Tar(env.GetOption('userRelease'), env['LIBDIR']))
            env.Tar(env.GetOption('userRelease'), env['BINDIR'])
            env.Tar(env.GetOption('userRelease'), env['SCRIPTDIR'])
            env.Tar(env.GetOption('userRelease'), env['INCDIR'])
            env.Tar(env.GetOption('userRelease'), env['DATADIR'])
            env.Tar(env.GetOption('userRelease'), env['XMLDIR'])
            env.Tar(env.GetOption('userRelease'), env['TESTDIR'])
#            env.Tar(env.GetOption('userRelease'), env['TESTSCRIPTDIR'])
            env.Tar(env.GetOption('userRelease'), env['PYTHONDIR'])
        else:
            env.Default(env.Zip(env.GetOption('userRelease'), env['LIBDIR']))
            env.Zip(env.GetOption('userRelease'), env['BINDIR'])
            env.Zip(env.GetOption('userRelease'), env['SCRIPTDIR'])
            env.Zip(env.GetOption('userRelease'), env['INCDIR'])
            env.Zip(env.GetOption('userRelease'), env['DATADIR'])
            env.Zip(env.GetOption('userRelease'), env['XMLDIR'])
            env.Zip(env.GetOption('userRelease'), env['TESTDIR'])
#            env.Zip(env.GetOption('userRelease'), env['TESTSCRIPTDIR'])
            env.Zip(env.GetOption('userRelease'), env['PYTHONDIR'])
        Return()

def exists(env):
    return true
