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

def blub(env, registry, **kw):
    SCons.Script.AddOption('--3rdparty', dest='3rdparty', action='store', default='site_scons/3rdParty', help='Specify the 3rdparty directory')
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
    
    try:
        SConsider.registerCallback('PackagesCollected', blub)
        

                     
        
#        SCons.Script.AddOption('--package', dest='package', action='store', default='', help='Specify the destination directory')
    except optparse.OptionConflictError:
#        raise PackageToolException("Only one Package-Tool instance allowed")
        pass
    
#    destination = SCons.Script.GetOption('package')
#    if destination:
#        if not os.path.isdir(destination):
#            SCons.Script.Main.OptionsParser.error("given package destination path doesn't exist")
#        else:
#            SConsider.registerCallback("PreBuild", addPackageTarget, env=env, destdir=SCons.Script.Dir(destination))

def exists(env):
    return 1
