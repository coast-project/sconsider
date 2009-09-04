import os, pdb
import SCons
from SCons.Script import AddOption, Dir, GetOption, Flatten
import setupBuildTools

added = None

def generate( env, **kw ):
    global added
    if not added:
        added = 1
        AddOption( '--enable-Trace', dest = 'Trace', action = 'store_true', help = 'Compile enabling trace support, (StartTrace, Trace,...), see Dbg.h for details' )
        import socket
        envconfigdir_default = socket.gethostname()
        AddOption( '--env-cfg', dest = 'envconfigdir', action = 'store', nargs = 1, type = 'string', default = envconfigdir_default, help = 'Define directory name to use for location dependent files, default [' + envconfigdir_default + ']. When a config file gets copied and a corresponding file exists below this directory, it will get used instead of the original one. This allows to define configuration settings appropriate for the current environment.' )

    # the following flag is used within coast only to detect the mode of compilation
    setupBuildTools.registerCallback( 'OPTIMIZE_OPTIONS', lambda env: env.AppendUnique( CPPDEFINES = ['WD_OPT'] ) )

    if GetOption( 'Trace' ):
        setupBuildTools.registerCallback( 'VARIANT_SUFFIX', lambda env: env.AppendUnique( VARIANT_SUFFIX = ['_trace'] ) )
        env.AppendUnique( CPPDEFINES = ['COAST_TRACE'] )

    env['__envconfigdir__'] = Dir( GetOption( 'envconfigdir' ) )
    print "environment specific directory:",env['__envconfigdir__'].abspath

def exists( env ):
    return true
