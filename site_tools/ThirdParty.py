import re, os, optparse, functools, fnmatch, pdb
import SomeUtils, SCons

thirdDartyPackages = {}

def hasSourceDist(packagename):
    return thirdDartyPackages.get(packagename, {}).has_key('sourcedistdir')

def getSourceDistDir(packagename):
    return thirdDartyPackages.get(packagename, {}).get('sourcedistdir', '')

def hasBinaryDist(packagename):
    return thirdDartyPackages.get(packagename, {}).has_key('binarydistdir')

def getBinaryDistDir(packagename):
    return thirdDartyPackages.get(packagename, {}).get('binarydistdir', '')

def addScanDir(env, directories):
    thirdPartyPath = SCons.Script.GetOption('3rdparty')
    directories.insert(0, thirdPartyPath)

def prepareLibraries(env, registry, **kw):
    thirdPartyPath = SCons.Script.GetOption('3rdparty')
    for root, dirnames, filenames in os.walk(thirdPartyPath):
        dirnames[:] = [dir for dir in dirnames if dir != env.get('BUILDDIR', '')]
        for filename in fnmatch.filter(filenames, '*.sconsider'):
            packagename, _ = os.path.splitext(filename)
            SCons.Script.AddOption('--with-src-'+packagename, dest='with-src-'+packagename, action='store', default='', metavar=packagename+'_SOURCEDIR', help='Specify the '+packagename+' source directory')               
            libpath = SCons.Script.GetOption('with-src-'+packagename)
            if libpath:
                libDir = env.Dir(libpath)
                env.Dir(thirdPartyPath).Dir(packagename).addRepository(libDir)
                registry.setPackageDuplicate(packagename, True)
                thirdDartyPackages.setdefault(packagename, {})['sourcedistdir'] = libDir
            
            SCons.Script.AddOption('--with-'+packagename, dest='with-'+packagename, action='store', default='', metavar=packagename+'_DIR', help='Specify the '+packagename+' binary directory')
            distpath = SCons.Script.GetOption('with-'+packagename)
            if distpath:
                distDir = env.Dir(distpath)
                env.Dir(thirdPartyPath).Dir(packagename).addRepository(distDir)
                thirdDartyPackages.setdefault(packagename, {})['binarydistdir'] = distDir

def generate(env):
    import SCons.Script, SConsider
    SCons.Script.AddOption('--3rdparty', dest='3rdparty', action='store', default='site_scons/3rdparty', help='Specify the 3rdparty directory')    
    SConsider.registerCallback('PrePackageCollection', addScanDir)
    SConsider.registerCallback('PostPackageCollection', prepareLibraries)

def exists(env):
    return 1
