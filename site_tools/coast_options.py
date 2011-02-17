import os, pdb
import SCons
from SCons.Script import AddOption, Dir, GetOption, Flatten

added = None

def generate( env, **kw ):
    global added
    if not added:
        added = 1
        AddOption( '--enable-Trace', dest = 'Trace', action = 'store_true', help = 'Compile enabling trace support, (StartTrace, Trace,...), see Dbg.h for details' )
        import socket
        envconfigdir_default = socket.gethostname()
        AddOption( '--env-cfg', dest = 'envconfigdir', action = 'store', nargs = 1, type = 'string', default = envconfigdir_default, help = 'Define directory name to use for location dependent files, default [' + envconfigdir_default + ']. When a config file gets copied and a corresponding file exists below this directory, it will get used instead of the original one. This allows to define configuration settings appropriate for the current environment.' )

    buildflags = []
    buildmode = GetOption( 'buildcfg' )
    if buildmode == 'optimized':
        buildflags.append('OPT')
    elif buildmode == 'debug':
        buildflags.append('DBG')
    else:
        buildflags.append('PROFILE')

    if GetOption( 'Trace' ):
        env.AppendUnique( VARIANT_SUFFIX = ['_trace'] )
        env.AppendUnique( CPPDEFINES = ['COAST_TRACE'] )
        buildflags.append('TRACE')

    env.AppendUnique( CPPDEFINES = ['COAST_BUILDFLAGS' + '="\\"' + '_'.join(buildflags) + '\\""' ] )
    compilerstring = [ env.get('CXX', 'unknown')]
    if env.get('CXXVERSION', ''):
        compilerstring.append(env.get( 'CXXVERSION', 'unknown' ))
    if env.get('CXXFLAVOUR', ''):
        compilerstring.append(env.get( 'CXXFLAVOUR', 'unknown' ))
    env.AppendUnique( CPPDEFINES = ['COAST_COMPILER' + '="\\"' + '_'.join(compilerstring) + '\\""'] )

    env['__envconfigdir__'] = Dir( GetOption( 'envconfigdir' ) )
    print "environment specific directory:",env['__envconfigdir__'].abspath

def exists( env ):
    return true
