# -*- python -*-
"""
The eol_scons package for EOL extensions to standard SCons.

This package extends SCons in three ways.  First of all, it overrides or
adds methods for the SCons Environment class.  See the _ExtendEnvironment()
function to see the full list.

Second, this package adds a set of EOL tools to the SCons tool path.  Most
of the tools for configuring and building against third-party software
packages.

Lastly, this module itself provides an interface of a few functions, for
configuring and controlling the eol_scons framework outside of the
Environment methods.  These are the public functions:

GlobalOptions(): for accessing the global list of eol_options maintained by this
package.

GlobalTools(): for accessing the global tools list.  Each tool in the
global tools list is applied to every Environment created.  Typically, the
SConstruct file appends a global tool function and other tools to this
list.  This is the hook by which the SConsctruct file can provide the basic
configuration for an entire source tree.

  import eol_scons
  eol_scons.GlobalTools().extend([Aeros, "doxygen"])

The list of global tools can also be extended by passing the list in the
GLOBAL_TOOLS construction variable when creating an Environment.

  env = Environment(tools = ['default'],
                    GLOBAL_TOOLS = ['svninfo', 'qtdir', 'doxygen', Aeros])

Debug(msg): print a debug message if the global debugging flag is true.

SetDebug(enable): set the global debugging flag to 'enable'.

Nothing else in this module should be called from outside the package.  In
particular, all the symbols starting with an underscore are meant to be
private.
"""

import os
import sys
import re
import glob
import fnmatch,pdb
from fnmatch import fnmatch

import SCons
import SCons.Tool

from SCons.Script import Variables
from SCons.Script import Environment
from SCons.Script import DefaultEnvironment
from SCons.Script import Options
from SCons.Script import PackageOption
from SCons.Script import EnumVariable
from SCons.Script import BoolVariable
from SCons.Script import PathVariable

from SCons.Util import NodeList
from SCons.Script.SConscript import global_exports
from SCons.Builder import _null

import string
#import eol_scons.chdir

# ================================================================
# The public interface for the eol_scons package.
# ================================================================

eol_options = None

# We have to use a 'hardcoded' path to the config file rather than using
# the DefaultEnvironment() to create a path.  Otherwise creating the
# DefaultEnvironment causes this module to be called again setting up all
# kinds of weird and hard-to-diagnose behaviors.

cfile = os.path.abspath(os.path.join(__path__[0],"../../config.py"))

def GlobalOptions(fname = cfile):
    """Return the eol_scons global eol_options."""
    global eol_options
    if not eol_options:
        eol_options = Variables (fname)
        eol_options.Add(
            BoolVariable('eolsconsdebug',
                       'Enable debug messages from eol_scons.',
                       debug))
        print "Config file: %s" % fname
    return eol_options

debug = False

def SetDebug(enable):
    """Set the flag to enable or disable printing of debug messages."""
    global debug
    debug = enable

def Debug(msg):
    """Print a debug message if the global debugging flag is true."""
    global debug
    if debug:
        print msg

_global_tools = [ 'prefixoptions' ]
#_global_tools = [ 'prefixoptions', 'buildmode' ]

def GlobalTools():
    """Return the global tools list."""
    global _global_tools
    return _global_tools

# ================================================================
# End of public interface
# ================================================================

_global_targets = {}

def _generate (env):
    """Generate the basic eol_scons customizations for the given
    environment, especially applying the scons built-in default tool
    and the eol_scons global tools."""
    GlobalOptions().Update(env)
    global debug
    if env.has_key('eolsconsdebug') and env['eolsconsdebug']:
        debug = True
    name = env.Dir('.').get_path(env.Dir('#'))
    Debug("Generating eol defaults for Environment(%s)" % name)

    # Apply the built-in default tool before applying the eol_scons
    # customizations and tools.
    import SCons.Tool.default
    SCons.Tool.default.generate(env)

    # Internal includes need to be setup *before* OptPrefixSetup or any
    # other includes, so that scons will scan for headers locally first.
    # Otherwise it looks in the opt prefix include first, and it notices
    # that the logx headers get installed there (even though not by
    # default).  This creates a dependency on the headers in that location,
    # which causes them to be installed even when the target is not
    # specifically 'install'.  The include arguments *are* (or used to be
    # and may someday again) re-ordered later on the command-line, putting
    # local includes first, but apparently that is not soon enough to
    # affect the scons scan.
    env.PrependUnique (CPPPATH=['.',])
    env.PrependUnique (CPPPATH=['#',])

    # Builder wrappers
#    Pkg_Program(env)
#    Pkg_Library(env)

    # Pass on certain environment variables, especially those needed
    # for automatic checkouts.
    env.PassEnv(r'CVS.*|SSH_.*')

    if env.has_key('GLOBAL_TOOLS'):
        _global_tools.extend(env['GLOBAL_TOOLS'])
    Debug("Applying global tools: %s" % \
          ",".join([str(x) for x in _global_tools]))
    env.Require(_global_tools)
    return env


# ================================================================
# Custom methods for the SCons Environment class.
#
# These are eol_scons internal functions which should only be called as
# methods through an Environment instance.  The methods are added to the
# built-in Environment class directly, so they are available to all
# environment instances once the eol_scons package has been imported.
# Other methods are added to an environment instance only when a particular
# tool has been applied; see prefixoptions.py for an example using
# InstallLibrary() and related methods.
# ================================================================

def _PassEnv(env, regexp):
    """Pass system environment variables matching regexp to the scons
    execution environment."""
    for ek in os.environ.keys():
        if re.match(regexp, ek):
            env['ENV'][ek] = os.environ[ek]


def _Require(env, tools):
    applied = []
    if not isinstance(tools,type([])):
        tools = [ tools ]
    for t in tools:
        try:
            tool = env.Tool(t)
            if tool:
                applied.append( tool )
        except:
            print("failed adding tool %s") % t
    return applied


#class Pkg_Program:
#
#    def __init__(self, env):
#        self.programBuilder = env.get_builder('Program')
#        env['BUILDERS']['Program'] = self
#        if not env.has_key('EXTRA_SOURCES'):
#            env['EXTRA_SOURCES'] = []
#
#    def __call__(self, env, target = None, source = _null, **overrides):
#        es = env['EXTRA_SOURCES']
#        if source == _null and len(es) == 0:
#            return self.programBuilder(env, target, source, **overrides)
#        else:
#            if type(source) != type([]):
#                source = [source]
#            return self.programBuilder(env, target, source + es, **overrides)


#class Pkg_Library:
#
#    def __init__(self, env):
#        self.libraryBuilder = env['BUILDERS']['Library']
#        env['BUILDERS']['Library'] = self
#
#    def __call__(self, env, target = None, source = _null, **overrides):
#        "Add the library to the list of global targets."
#        ret = self.libraryBuilder(env, target, source, **overrides)
#        if target:
#            env.AddLibraryTarget(target, ret)
#        return ret


#def _Test (self, sources, actions):
#    """Create a test target and aliases for the given actions with
#    sources as its dependencies.
#
#    Tests within a particular directory can be run using the xtest name, as
#    in 'scons datastore/tests/xtest', or 'scons -u xtest' to run the tests
#    for the current directory.  Tests created with this method will also be
#    added to the global 'test' alias."""
#    xtest = self.Command("xtest", sources, actions)
#    self.Precious(xtest)
#    self.AlwaysBuild(xtest)
#    DefaultEnvironment().Alias('test', xtest)
#    return xtest


#def _ChdirActions (self, actions, dir = None):
#    return chdir.ChdirActions(self, actions, dir)

#def _Install (self, dir, source):
#    """Call the standard Install() method and also add the target to the
#    global 'install' alias."""
#    t = SCons.Environment.Base.Install (self, dir, source)
#    DefaultEnvironment().Alias('install', t)
#    return t

#def _ExtraSources(env, source):
#    """Add the given list of sources to the list of extra sources.
#
#    If a member of the source list is a string, then it will be resolved
#    to a target from the list of global targets.  Otherwise the members
#    must be a SCons target node.
#    """
#    if type(source) != type([]):
#        source = [source]
#    targets=[]
#    for s in source:
#        try:
#            if type(s) == str:
#                targets.append (_global_targets[s])
#            else:
#                targets.append (s)
#        except KeyError:
#            print "Unknown global target '%s'." % (s)
#    env['EXTRA_SOURCES'].extend (targets)
#    return targets

#def _AddLibraryTarget(env, base, target):
#    "Register this library target using a prefix reserved for libraries."
#    while type(base) == type(NodeList) or type(base) == type([]):
#        base = base[0]
#    name = "lib"+str(base)
#    env.AddGlobalTarget(name, target)
#    return target

#def _AddGlobalTarget(env, name, target):
#    "Register this target under the given name."
#    # Make sure we register a node and not a list, just because that has
#    # been the convention, started before scons changed all targets to
#    # lists.
#    try:
#        node = target[0]
#    except (TypeError, AttributeError):
#        node = target
#    Debug(["AddGlobalTarget:"] + [name] + [node])
#    _global_targets[name] = node
#    return node

#def _GetGlobalTarget(env, name):
#    "Look up a global target node by this name and return it."
#    try:
#        target = _global_targets[name]
#        return target
#    except KeyError:
#        return None

#def _AppendLibrary (env, name, path = None):
#    "Add this library either as a local target or a link option."
#    env.Append(DEPLOY_SHARED_LIBS=name)
#    target = env.GetGlobalTarget("lib"+name)
#    if target:
#        Debug("appending library node: %s" % str(target))
#        env.Append(LIBS=[target])
#    else:
#        env.Append(LIBS=[name])
#        if path:
#            env.Append(LIBPATH=[path])

#def _AppendSharedLibrary (env, name, path=None):
#    "Add this shared library either as a local target or a link option."
#    env.Append(DEPLOY_SHARED_LIBS=name)
#    target = env.GetGlobalTarget("lib"+name)
#    Debug("appending shared library node: %s" % str(target))
#    if target and not path:
#        path = target.dir.get_abspath()
#    env.Append(LIBS=[name])
#    if not path:
#        return
#    env.AppendUnique(LIBPATH=[path])
#    env.AppendUnique(RPATH=[path])

#def _FindPackagePath(env, optvar, globspec, defaultpath = None):
#    """Check for a package installation path matching globspec."""
#    eol_options = GlobalOptions()
#    dir=defaultpath
#    try:
#        dir=os.environ[optvar]
#    except KeyError:
#        if not env:
#            env = DefaultEnvironment()
#        eol_options.Update(env)
#        dirs = glob.glob(env.subst(globspec))
#        dirs.sort()
#        dirs.reverse()
#        for d in dirs:
#            if os.path.isdir(d):
#                dir=d
#                break
#    return dir


## This is for backwards compatibility only to help with transition.
## Someday it will be removed.
#def _Create (env,
#            package,
#            platform=None,
#            tools=None,
#            toolpath=None,
#            eol_options=None,
#            **kw):
#    return Environment (platform, tools, toolpath, eol_options, **kw)


#def _CheckMissingHeaders(env, doxfiles, ignores):
#
#    found = []
#    for root, dirs, files in os.walk(env.Dir('.').get_path()):
#        # root = root.lstrip('./')
#        files = filter(lambda f: not fnmatch(f, "moc_*") and
#                       not fnmatch(f, "*.ui*") and not fnmatch(f, "uic_*") and
#                       fnmatch(f, "*.h"), files)
#        found += [os.path.normpath(os.path.join(root, f)) for f in files]
#
#    known = [ os.path.normpath(p) for p in doxfiles+ignores ]
#    missing = [ f for f in found if f not in known ]
#    missing.sort()
#    if len(missing) > 0:
#        print "Header files missing in ", env.Dir('.').get_abspath(), ":"
#        print "\n".join(missing)

def _LogDebug(env, msg):
    Debug(msg)

def _GlobalOptions(env):
    return GlobalOptions()

def _GlobalTools(env):
    return GlobalTools()

tool_dict = {}

def _Tool(env, tool, toolpath=None, **kw):
    name = str(tool)
    if SCons.Util.is_String(tool):
        name = env.subst(tool)
        tool = None

        if tool_dict.has_key(name):
            Debug("Found tool already loaded: %s" % name)
            tool = tool_dict[name]

        # Check if this tool is actually an exported tool function,
        # in which case convert to the function.  Otherwise leave it as
        # a string and let scons look it up.
        if not tool:
            if global_exports.has_key(name):
                tool = global_exports[name]
            if tool:
                Debug("Found tool in global exports: %s" % name)

        if not tool:
            if toolpath is None:
                toolpath = env.get('toolpath', [])
            toolpath = map(env._find_toolpath_dir, toolpath)
            tool = apply(SCons.Tool.Tool, (name, toolpath), kw)
            Debug("Loading tool: %s" % tool)

    try:
        tool(env)
    except:
        print "Failed loading tool",name,sys.exc_value
        tool = None
        pass
    else:
        tool_dict[name] = tool
    return tool


def _ExtendEnvironment(envclass):

    envclass.Require = _Require
#    envclass.ExtraSources = _ExtraSources
#    envclass.AddLibraryTarget = _AddLibraryTarget
#    envclass.AddGlobalTarget = _AddGlobalTarget
#    envclass.GetGlobalTarget = _GetGlobalTarget
#    envclass.AppendLibrary = _AppendLibrary
#    envclass.AppendSharedLibrary = _AppendSharedLibrary
    envclass.PassEnv = _PassEnv
#    envclass.Install = _Install
#    envclass.ChdirActions = _ChdirActions
#    envclass.Test = _Test
#    envclass.CheckMissingHeaders = _CheckMissingHeaders
    envclass.LogDebug = _LogDebug
#    envclass.FindPackagePath = _FindPackagePath
    envclass.GlobalOptions = _GlobalOptions
    envclass.GlobalTools = _GlobalTools
    envclass.Tool = _Tool

#    # For backwards compatibility:
#    envclass.Create = _Create

_ExtendEnvironment(SCons.Environment.Environment)

# ================================================================
# End of Environment customization.
# ================================================================

Debug("eol_scons.__init__ loaded.")
