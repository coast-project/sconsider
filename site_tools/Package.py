import re, os, optparse, functools

def makePackage(registry, buildTargets, env, destination, **kw):
    import SCons.Script
    isInBuilddir = functools.partial(hasPathPart, pathpart=env['BUILDDIR'])
    notInBuilddir = lambda target: not isInBuilddir(target)
    notCopiedInclude = lambda target: not target.path.startswith(env['INCDIR'])
    for tn in buildTargets:
        if isSConsiderTarget(registry, tn):
            print "==="
            tdeps = getTargetDependencies(env.Alias(tn)[0], [isDerivedDependency, notInBuilddir, notCopiedInclude])
            copyPackage(tn, tdeps, env, destination)
            print "==="
    
    SCons.Script.BUILD_TARGETS.append("makepackage")

def copyPackage(name, deps, env, destination):
    import SCons.Script
    if os.path.isdir(destination):
        destdir = SCons.Script.Dir(destination)
        for target in deps:
            print target.path
            target = env.Install(determineDirInPackage(name, env, destdir, target), target)
            env.Alias("makepackage", target)

def isSConsiderTarget(registry, ftn):
    import SConsider
    if registry.hasPackage(str(ftn)):
        return True
    pkg, tn = SConsider.splitTargetname(str(ftn))
    if registry.hasPackageTarget(pkg, tn):
        return True
    return False
            
def determineDirInPackage(name, env, destdir, target):
    import SomeUtils, pdb
    copydir = destdir.Dir(name)
    replist = [('^tests'+os.sep+'.*?'+os.sep, ''),
               ('^apps'+os.sep+'.*?'+os.sep, '')] 
    path = SomeUtils.multiple_replace(replist, target.get_dir().path)
    return copydir.Dir(path)
    
class PackageToolException(Exception):
    pass
    
def generate(env):
    import SCons.Script, SConsider
    try:
        SCons.Script.AddOption('--packagedestination', dest='packagedestination', action='store', default=False, help='Specify the destination directory')
    except optparse.OptionConflictError:
        raise PackageToolException("Only one Package-Tool instance allowed")
    
    destination = SCons.Script.GetOption('packagedestination')
    if destination:
        SConsider.registerCallback("PreBuild", makePackage, env=env, destination=destination)

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
        deps.add(target)
    
    for t in target.sources + target.depends + target.prerequisites:
        deps.update(getTargetDependencies(t, customfilters))
    
    return deps
