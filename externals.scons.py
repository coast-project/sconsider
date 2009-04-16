# -*- python -*-
import os, platform
Import('baseEnv')
import pdb

####################################################################
# Basic data structure to represent the external libraries we need #
####################################################################
externalLibraries = {

    'loki'     : {'version' : '0.1.6',
                  'includes' : ['loki/TypeTraits.h'],
                  'libraries' : {'lokiLibs'  : []},
                  'include-path' : os.path.join('$COAST_ROOT', '3rdparty/loki/include')
                  #'cppdefines' : ['someflag=somevalue']
                  },

    'boost'     : {'version' : '1.34.1',
                  'includes' : ['boost/bind.hpp'],
                  'libraries' : {'boostLibs'  : []},
                  'include-path' : os.path.join('$COAST_ROOT', '3rdparty/boost')
                  #'cppdefines' : ['someflag=$VERSION']
                  }
}

##############################################################
# Override above default values for platform specific values #
##############################################################
if baseEnv['PLATFORM'] == "win32":
    pass

if baseEnv['PLATFORM'] == 'sunos':
    pass

if baseEnv['PLATFORM'] == 'darwin':
    pass

############################################################################
# Set the correct compiler version, name, and library version in the paths #
############################################################################
if baseEnv['PLATFORM'] == "win32":
    pass # compiler = 'vc'+''.join(baseEnv['MSVS']['VERSION'].split('.')[0:2])
else:
    pass # compiler = 'gcc'+''.join(baseEnv['CXXVERSION'].split('.')[0:2])
for lib in externalLibraries.keys():
    for path in ['include-path', 'lib-path', 'bin-path']:
        if path in externalLibraries[lib]:
          try:
            externalLibraries[lib][path] = externalLibraries[lib][path].replace('$COMPILER', compiler)
            externalLibraries[lib][path] = externalLibraries[lib][path].replace('$VERSION', externalLibraries[lib]['version'])
            externalLibraries[lib][path] = externalLibraries[lib][path].replace('$NAME', lib)
          except:
            pass

############################################
# Add options to override paths if desired #
############################################
for lib in externalLibraries.keys():
    AddOption('--with-' + lib, dest=lib, nargs=1, type='string', action='store', metavar='DIR', help='location of ' + lib + ' ' + externalLibraries[lib]['version'] + ' headers/libraries')
    if 'include-path' in externalLibraries[lib]:
        AddOption('--with-' + lib + '-includes', dest=lib + '-includes', nargs=1, type='string', action='store', metavar='DIR', help='location of ' + lib + ' ' + externalLibraries[lib]['version'] + ' headers')
    if 'lib-path' in externalLibraries[lib]:
        AddOption('--with-' + lib + '-libraries', dest=lib + '-libraries', nargs=1, type='string', action='store', metavar='DIR', help='location of ' + lib + ' ' + externalLibraries[lib]['version'] + ' libraries')
    if 'bin-path' in externalLibraries[lib]:
        AddOption('--with-' + lib + '-binaries', dest=lib + '-binaries', nargs=1, type='string', action='store', metavar='DIR', help='location of ' + lib + ' ' + externalLibraries[lib]['version'] + ' binaries')

##########################
# Check Override Options #
##########################
for lib in externalLibraries.keys():
    if baseEnv.GetOption(lib):
        if 'include-path' in externalLibraries[lib]:
            externalLibraries[lib]['include-path'] = os.path.join(baseEnv.GetOption(lib), 'include')
        if 'lib-path' in externalLibraries[lib]:
            externalLibraries[lib]['lib-path'] = os.path.join(baseEnv.GetOption(lib), 'lib')
        if 'bin-path' in externalLibraries[lib]:
            externalLibraries[lib]['bin-path'] = os.path.join(baseEnv.GetOption(lib), 'bin')
    else:
        if 'include-path' in externalLibraries[lib]:
            if baseEnv.GetOption(lib + '-includes'):
                externalLibraries[lib]['include-path'] = baseEnv.GetOption(lib + '-includes')
        if 'lib-path' in externalLibraries[lib]:
            if baseEnv.GetOption(lib + '-libraries'):
                externalLibraries[lib]['lib-path'] = baseEnv.GetOption(lib + '-libraries')
        if 'bin-path'  in externalLibraries[lib]:
            if baseEnv.GetOption(lib + '-binaries'):
                externalLibraries[lib]['bin-path'] = baseEnv.GetOption(lib + '-binaries')

#################################################################
# Register all external libraries to be used in wrapper scripts #
#################################################################
for lib in externalLibraries.keys():
    if 'ld-path' in externalLibraries[lib] and 'version' in externalLibraries[lib]:
        if 'lib-path' in externalLibraries[lib]:
            externalLibraries[lib]['ld-path'] = externalLibraries[lib]['ld-path'].replace('$LIB-PATH', externalLibraries[lib]['lib-path'])
        if 'bin-path' in externalLibraries[lib]:
            externalLibraries[lib]['ld-path'] = externalLibraries[lib]['ld-path'].replace('$BIN-PATH', externalLibraries[lib]['bin-path'])
        baseEnv.AppendUnique(WRAPPERLIBS=[externalLibraries[lib]['ld-path']])
#baseEnv['ROOTSYS'] = os.path.normpath(os.path.join(externalLibraries['ROOT']['include-path'], '..'))

########################################
# Set up COAST-ROOT if it was specified #
########################################
if baseEnv.GetOption('COAST-ROOT'):
    for lib in externalLibraries.keys():
        for path in ['include-path', 'lib-path', 'bin-path']:
            if path in externalLibraries[lib]:
                externalLibraries[lib][path] = externalLibraries[lib][path].replace('$COAST_ROOT', Dir(baseEnv.GetOption('COAST-ROOT')).abspath)

######################################
# Add paths to the compile/link line #
######################################
for lib in externalLibraries.keys():
    if 'include-path' in externalLibraries[lib] and externalLibraries[lib]['include-path'].find('$') == - 1:
        baseEnv.AppendUnique(CPPPATH=[externalLibraries[lib]['include-path']])
    if 'lib-path' in externalLibraries[lib] and externalLibraries[lib]['lib-path'].find('$') == - 1:
        baseEnv.AppendUnique(LIBPATH=[externalLibraries[lib]['lib-path']])
    if 'bin-path' in externalLibraries[lib] and externalLibraries[lib]['bin-path'].find('$') == - 1:
        baseEnv.AppendUnique(PATH=[externalLibraries[lib]['bin-path']])

###########################################################
# Register various compile options for external libraries #
###########################################################
for lib in externalLibraries.keys():
    if 'libraries' in externalLibraries[lib]:
        for libGroup in externalLibraries[lib]['libraries'].keys():
            baseEnv[libGroup] = externalLibraries[lib]['libraries'][libGroup]
    if 'cppdefines' in externalLibraries[lib]:
        for define in externalLibraries[lib]['cppdefines']:
            if baseEnv.GetOption('COAST-ROOT'):
                define = define.replace('$COAST_ROOT', baseEnv.GetOption('COAST-ROOT'))
            define = define.replace('$VERSION', externalLibraries[lib]['version']).replace('$NAME', lib)
            baseEnv.AppendUnique(CPPDEFINES=[define])

###########################################################
# Check to make sure external libraries and headers exist #
###########################################################
if not baseEnv.GetOption('help') and not baseEnv.GetOption('clean'):
    env = baseEnv.Clone()
    conf = env.Configure()
    for lib in externalLibraries.keys():
        if 'includes' in externalLibraries[lib] and 'include-path' in externalLibraries[lib]:
            for include in externalLibraries[lib]['includes']:
                if not conf.CheckCXXHeader(include):
                    print 'Unable to find a header file for ' + lib + '. See config.log for more details.'
                    Exit(1)
        if 'libraries' in externalLibraries[lib] and 'lib-path' in externalLibraries[lib]:
            for libGroup in externalLibraries[lib]['libraries'].keys():
                for library in externalLibraries[lib]['libraries'][libGroup][:: - 1]:
                    if not conf.CheckLib(library, language='C++'):
                        print 'Unable to find a library for ' + lib + '. See config.log for more details.'
                        Exit(1)
    conf.Finish()
