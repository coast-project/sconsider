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

def generate(env):
    import SCons.Script, SConsider
    
    try:
        SCons.Script.AddOption('--3rdparty', dest='3rdparty', action='store', default='site_scons/3rdParty', help='Specify the 3rdparty directory')
        thirdPartyPath = SCons.Script.GetOption('3rdparty')
        for root, dirnames, filenames in os.walk(thirdPartyPath):
            dirnames[:] = [dir for dir in dirnames if dir != '.build']
            for filename in fnmatch.filter(filenames, '*.sconsider'):
                library, _ = os.path.splitext(filename)
                SCons.Script.AddOption('--with-src-'+library, dest='with-src-'+library, action='store', default='', metavar=library+'_SOURCEDIR', help='Specify the '+library+' source directory')               
                libpath = SCons.Script.GetOption('with-src-'+library)
                if libpath:
                    libDir = env.Dir(libpath)
                    env.Dir(thirdPartyPath).Dir(library).addRepository(libDir)
                    
                    def createCallback(packagename):
                        return lambda registry: registry.setPackageDuplicate(packagename, True)                    
                    SConsider.registerCallback('PackagesCollected', createCallback(library))
                     
                    thirdDartyPackages.setdefault(library, {})['sourcedistdir'] = libDir
                
                SCons.Script.AddOption('--with-'+library, dest='with-'+library, action='store', default='', metavar=library+'_DIR', help='Specify the '+library+' binary directory')
                distpath = SCons.Script.GetOption('with-'+library)
                if distpath:
                    distDir = env.Dir(distpath)
                    env.Dir(thirdPartyPath).Dir(library).addRepository(distDir)

                    thirdDartyPackages.setdefault(library, {})['binarydistdir'] = distDir
                     
        
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
