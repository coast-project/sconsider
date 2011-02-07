import re, os, optparse, functools, fnmatch, pdb
import SomeUtils, SCons

thirdDartyPackages = {}

def hasSourceDist(packagename):
    return thirdDartyPackages.get(packagename, {}).has_key('src')

def getSourceDistDir(packagename):
    return thirdDartyPackages.get(packagename, {}).get('src', '')

def hasBinaryDist(packagename):
    return thirdDartyPackages.get(packagename, {}).has_key('bin')

def getBinaryDistDir(packagename):
    return thirdDartyPackages.get(packagename, {}).get('bin', '')

def collectPackages(startdir, exceptions=[]):
    package_re = re.compile('^(?P<packagename>.*)\.(?P<type>sys|src|bin)\.sconsider$')
    packages = {}
    for root, dirnames, filenames in os.walk(startdir):
        dirnames[:] = [dir for dir in dirnames if dir not in exceptions]
        for filename in fnmatch.filter(filenames, '*.sconsider'):
            match = package_re.match(filename)
            if match:
                packages.setdefault(match.group('packagename'), {})[match.group('type')] = SCons.Script.Dir(root).File(filename)
    return packages


def registerDist(registry, packagename, package, distType, distDir, duplicate):
    registry.setPackage(packagename, package[distType], package[distType].get_dir(), duplicate)
    package[distType].get_dir().addRepository(distDir)
    thirdDartyPackages.setdefault(packagename, {})[distType] = distDir

def prepareLibraries(env, registry, **kw):
    thirdPartyPath = SCons.Script.GetOption('3rdparty')
    packages = collectPackages(thirdPartyPath, [env.get('BUILDDIR', '')])
    
    for packagename, package in packages.iteritems(): 
        SCons.Script.AddOption('--with-src-'+packagename, dest='with-src-'+packagename, action='store', default='', metavar=packagename+'_SOURCEDIR', help='Specify the '+packagename+' source directory')
        SCons.Script.AddOption('--with-'+packagename, dest='with-'+packagename, action='store', default='', metavar=packagename+'_DIR', help='Specify the '+packagename+' binary directory')
                          
        libpath = SCons.Script.GetOption('with-src-'+packagename)
        if libpath:
            if not package.has_key('src'):
                print 'Third party source distribution definition for {0} not found, aborting!'.format(packagename)
                SCons.Script.Exit(1)
            registerDist(registry, packagename, package, 'src', env.Dir(libpath), True)
        else:
            distpath = SCons.Script.GetOption('with-'+packagename)
            if distpath:
                if not package.has_key('bin'):
                    print 'Third party binary distribution definition for {0} not found, aborting!'.format(packagename)
                    SCons.Script.Exit(1)
                registerDist(registry, packagename, package, 'bin', env.Dir(distpath), False)
            else:
                if not package.has_key('sys'):
                    print 'Third party system definition for {0} not found, aborting!'.format(packagename)
                    SCons.Script.Exit(1)
                registry.setPackage(packagename, package['sys'], package['sys'].get_dir(), False)

def generate(env):
    import SCons.Script, SConsider
    SCons.Script.AddOption('--3rdparty', dest='3rdparty', action='store', default='site_scons/3rdparty', help='Specify the 3rdparty directory')    
    SConsider.registerCallback('PostPackageCollection', prepareLibraries)

def exists(env):
    return 1
