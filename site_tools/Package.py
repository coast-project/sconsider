import re, os, optparse, functools, pdb
import SomeUtils

def makePackage(registry, buildTargets, env, destdir, **kw):
    isInBuilddir = functools.partial(hasPathPart, pathpart=env['BUILDDIR'])
    notInBuilddir = lambda target: not isInBuilddir(target)
    notCopiedInclude = lambda target: not target.path.startswith(env['INCDIR'])
    copyfilters = [filterTestsAppsPath, filterVariantPath]
    for tn in buildTargets:
        if isSConsiderTarget(registry, tn):
            tdeps = getTargetDependencies(env.Alias(tn)[0], [isDerivedDependency, notInBuilddir, notCopiedInclude])
            copyPackage(tn, tdeps, env, destdir, copyfilters)
    
    buildTargets.append("makepackage")

def copyPackage(name, deps, env, destdir, filters=[]):
    for target in deps:
        copyTarget(env, determineDirInPackage(name, env, destdir, target, filters), target)

def copyTarget(env, destdir, node):
    old = env.Alias(destdir.File(node.name))
    if len(old) and len(old[0].sources):
        if isInstalledDependency(node, old[0].sources[0]) or isInstalledDependency(old[0].sources[0], node):
            return None
        else:
            print "Ambiguous target [%s] copied from [%s] and [%s]." % (old[0].path, node.path, old[0].sources[0].path)
            print "Can't create package! See errors below..."
    target = env.Install(destdir, node)
    env.Alias("makepackage", target)
    return target

def isInstalledDependency(testnode, node):
    if testnode.path == node.path:
        return True
    if not hasattr(node, 'builder') or not hasattr(node.builder, 'name') or node.builder.name != 'InstallBuilder':
        return False
    if len(node.sources) < 1:
        return False
    return isInstalledDependency(testnode, node.sources[0])

def isSConsiderTarget(registry, ftn):
    import SConsider
    if registry.hasPackage(str(ftn)):
        return True
    pkg, tn = SConsider.splitTargetname(str(ftn))
    if registry.hasPackageTarget(pkg, tn):
        return True
    return False

def filterTestsAppsPath(path, **kw):
    replist = [('^tests'+os.sep+'[^'+os.sep+']*'+os.sep+'?', ''),
               ('^apps'+os.sep+'[^'+os.sep+']*'+os.sep+'?', '')]
    return SomeUtils.multiple_replace(replist, path)

def filterVariantPath(path, **kw):
    variant = kw.get('env', {}).get('VARIANTDIR', False)
    if not variant:
        return path

    return re.sub(re.escape(variant)+os.sep+'?', '', path)

def determineDirInPackage(name, env, destdir, target, filters=[]):
    path = target.get_dir().path

    if not isinstance(filters, list):
        filters = [filters]
    for filter in filters:
        if callable(filter):
            path = filter(path, env=env)

    copydir = destdir.Dir(name)
    return copydir.Dir(path)
    
class PackageToolException(Exception):
    pass
    
def generate(env):
    import SCons.Script, SCons.Script.Main, SConsider
    try:
        SCons.Script.AddOption('--packagedestination', dest='packagedestination', action='store', default=False, help='Specify the destination directory')
    except optparse.OptionConflictError:
        raise PackageToolException("Only one Package-Tool instance allowed")
    
    destination = SCons.Script.GetOption('packagedestination')
    if not os.path.isdir(destination):
        SCons.Script.Main.OptionsParser.error("given package destination path doesn't exist")
    else:
        SConsider.registerCallback("PreBuild", makePackage, env=env, destdir=SCons.Script.Dir(destination))

def exists(env):
    return 1

def isFileDependency(target):
    """No path means it is not a file."""
    return hasattr(target, 'path')

def isDerivedDependency(target):
    """Returns True if this node is built"""
    return target.is_derived()

def hasPathPart(target, pathpart):
    """Checks if target's path has a given part"""
    regex = '(^'+re.escape(pathpart+os.sep)+')'
    regex += '|(.*'+re.escape(os.sep+pathpart+os.sep)+')'
    regex += '|(.*'+re.escape(os.sep+pathpart)+'$)'
    match = re.match(regex, target.path)
    return match is not None

def allFuncs(funcs, *args):
    """Returns True if all functions in 'funcs' return True"""
    for f in funcs:
        if not f(*args):
            return False
    return True
        
def getTargetDependencies(target, customfilters=[]):
    """Determines the recursive dependencies of a target (including itself).
    
    Specify additional target filters using 'customfilters'.
    """
    if not isinstance(customfilters, list):
        customfilters = [customfilters]
    filters = [isFileDependency] + customfilters
    
    deps = set()
    if allFuncs(filters, target):
        deps.update( target.get_executor().get_all_targets() )

    for t in target.sources + target.depends + target.prerequisites:
        deps.update(getTargetDependencies(t, customfilters))

    return deps
