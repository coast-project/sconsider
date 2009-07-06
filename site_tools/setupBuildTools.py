import pdb, os
import SCons.Tool
import SCons.Script
from SCons.Script import AddOption, Dir, GetOption

added = None

def generate(env, **kw):
    """Add build tools."""
    global added
    if not added:
        added = 1
        AddOption('--with-g++', dest='whichgcc', action='store', nargs=1, type='string', default=None, metavar='PATH', help='fully qualified path and name to gnu c++ compiler')
        bitchoices = ["32", "64"]
        bitdefault = '32'
        AddOption('--archbits', dest='archbits', action='store', nargs=1, type='choice', choices=bitchoices, default=bitdefault, metavar='OPTIONS', help='Select target bit width (if compiler supports it), ' + str(bitchoices) + ', default=' + bitdefault)
        AddOption('--no-stdiostream', dest='no-stdiostream', action='store_true', help='Disable use of std libraries iostream headers')
    platf = env['PLATFORM']
    whichgcc = GetOption('whichgcc')
    if whichgcc:
        dirname = os.path.dirname(whichgcc)
        env.PrependENVPath('PATH', dirname)
        # this section is needed to select gnu toolchain on sun systems, default is sunCC
        # -> see SCons.Tool.__init__.py tool_list method for explanation
        if str(platf) == 'sunos':
            platf = None
    for t in SCons.Tool.tool_list(platf, env):
        SCons.Tool.Tool(t)(env)
    platf = env['PLATFORM']
    compver = ''
    if env.has_key('CXXVERSION'):
        compver = '(' + env['CXXVERSION'] + ')'
    print 'using CXX compiler and version:', env['CXX'], compver

    # common flags which influence compilation
    env.AppendUnique(CPPDEFINES=['_POSIX_PTHREAD_SEMANTICS'])

    # tell linker to only succeed when all external references can be resolved
    ##FIXME: attention the following is a workaround
    ##  because LINKFLAGS='-z defs' would lead to a string'ified "-z defs" in the linker command line
    env.Append(LINKFLAGS=['$_NONLAZYLINKFLAGS'])
    env['_NONLAZYLINKFLAGS'] = '-z defs -z now '

    if str(platf) == 'sunos' and not whichgcc:
        env.AppendUnique(CCFLAGS='-mt')
        env.AppendUnique(LINKFLAGS='-mt')
        # do not use rpath
        env.AppendUnique(LINKFLAGS='-norunpath')
    elif str(platf) == "cygwin":
        env.AppendUnique(CPPDEFINES=['_REENTRANT'])
        env['_NONLAZYLINKFLAGS'] = ''
        env.AppendUnique(CPPDEFINES=['WIN32', '_WIN32_WINNT=0x400'])
#        env.AppendUnique(CPPDEFINES=['_MSC_VER=$MSVC_VER'])
    else:
        env.AppendUnique(CPPDEFINES=['_REENTRANT'])
        env['_NONLAZYLINKFLAGS'] += '--no-undefined '

    env.AppendUnique(LIBS=['m', 'dl', 'c'])
    if not str(platf) == "cygwin":
        env.AppendUnique(LIBS=['nsl'])

    # this lib is needed when using sun-CC or gcc on sunos systems
    if str(platf) == "sunos":
        env.AppendUnique(LIBS=['socket', 'resolv', 'aio', 'posix4'])

    # select target architecture bits
    bitwidth = GetOption('archbits')
    env['ARCHBITS'] = bitwidth
    bitwoption = '-m'
    if str(platf) == 'sunos' and not whichgcc:
        # sun-CC compiler is to use
        bitwoption = '-xtarget=native'
        if bitwidth == '32':
            # when compiling 32bit, -xtarget=native is all we need, otherwise native64 must be specified
            bitwidth = ''

    env.AppendUnique(CCFLAGS=bitwoption + bitwidth)
    env.AppendUnique(LINKFLAGS=bitwoption + bitwidth)

    if not GetOption('no-stdiostream'):
        env.AppendUnique(CPPDEFINES=['ONLY_STD_IOSTREAM'])
    # if we use sun-CC, we need to specify some stl compliancy options...
    # important switch to enable up to date c++ features, especially template specific things
    ##--- c++ specific flags, templates, iostream, etc
    if str(platf) == 'sunos' and not whichgcc:
        env.AppendUnique(CCFLAGS='-library=stlport4')
        env.AppendUnique(LINKFLAGS='-library=stlport4')
        if not GetOption('no-stdiostream'):
            ## iostream library means "classic", but we want to use the std
            env.AppendUnique(CCFLAGS='-library=no%iostream')
            env.AppendUnique(LINKFLAGS='-library=no%iostream')

def exists(env):
    return 1
