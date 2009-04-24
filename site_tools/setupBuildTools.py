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
        bitchoices=["32", "64"]
        bitdefault='32'
        AddOption('--archbits', dest='archbits', action='store', nargs=1, type='choice', choices=bitchoices, default=bitdefault, metavar='OPTIONS', help='Select target bit width (if compiler supports it), '+str(bitchoices)+', default='+bitdefault)
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
    compver = ''
    if env.has_key('CXXVERSION'):
        compver = '(' + env['CXXVERSION'] + ')'
    print 'using CXX compiler and version:', env['CXX'], compver

    # select target architecture bits
    bitwidth=GetOption('archbits')
    bitwoption='-m'
    if str(platf) == 'sunos' and not whichgcc:
        # sun-CC compiler is to use
        bitwoption='-xtarget=native'
        if bitwidth == '32':
            # when compiling 32bit, -xtarget=native is all we need, otherwise native64 must be specified
            bitwidth=''
    env.AppendUnique(CCFLAGS=bitwoption+bitwidth)
    env.AppendUnique(SHCCFLAGS=bitwoption+bitwidth)
    env.AppendUnique(LINKFLAGS=bitwoption+bitwidth)

def exists(env):
    return 1
