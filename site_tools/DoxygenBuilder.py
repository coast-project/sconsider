from __future__ import with_statement
import os, pdb, subprocess, optparse
import SCons.Action, SCons.Builder
from SCons.Script import AddOption, GetOption
import StanfordUtils, SomeUtils

# monkey patch os.path to include relpath if python version is < 2.6
if not hasattr(os.path, "relpath"):
    def relpath(path, start):
        """Return a relative version of a path"""

        if not path:
            raise ValueError, 'no path specified'

        if path == start:
            return '.'

        start_list = (os.path.abspath(start)).split(os.sep)
        path_list = (os.path.abspath(path)).split(os.sep)

        # Work out how much of the filepath is shared by start and path.
        i = len(os.path.commonprefix([start_list, path_list]))

        rel_list = [os.pardir] * (len(start_list)-i) + path_list[i:]
        return os.path.join(*rel_list)
    os.path.relpath = relpath

def __getDependencies(registry, packagename, fnobj, recursive=False):
    depPackages = {}
    
    buildSettings = registry.getBuildSettings(packagename)
    for targetname, settings in buildSettings.items():
        deps = settings.get('requires', []) + settings.get('linkDependencies', [])
        usedTarget = settings.get('usedTarget', '')
        if usedTarget:
            deps.append(usedTarget)
        
        for ftn in deps:
            depPkgname, depTname = StanfordUtils.splitTargetname(ftn)
            if not depPkgname == packagename:
                if recursive:
                    depPackages.update(__getDependencies(registry, depPkgname, fnobj, recursive))
                file = fnobj(depPkgname)
                if file:
                    depPackages[depPkgname] = file
    
    return depPackages

doxyfiles = {}
def registerPackageDoxyfile(packagename, doxyfile):
    doxyfiles[packagename] = doxyfile
    
def getPackageDoxyfile(packagename):
    return doxyfiles.get(packagename, '')

def getDoxyfileDependencies(registry, packagename, recursive=False):
    return __getDependencies(registry, packagename, getPackageDoxyfile, recursive).values()

tagfiles = {}
def registerPackageTagfile(packagename, tagfile):
    tagfiles[packagename] = tagfile
    
def getPackageTagfile(packagename):
    return tagfiles.get(packagename, '')

def getTagfileDependencies(registry, packagename, recursive=False):
    return __getDependencies(registry, packagename, getPackageTagfile, recursive).values()

doxyfiledata = {}
def getDoxyfileData(doxyfile, env):
    """
    Caches parsed Doxyfile content.
    """
    doxyfilepath = doxyfile.get_abspath()
    if not os.path.isfile(doxyfilepath):
        return {}
    if not doxyfiledata.get(doxyfilepath, {}):
        doxyfiledata[doxyfilepath] = parseDoxyfile(doxyfile, env)
    return doxyfiledata[doxyfilepath]

def parseDoxyfile(file_node, env):
   """
   Parse a Doxygen source file and return a dictionary of all the values.
   Values will be strings and lists of strings.
   """
   if not os.path.isfile(file_node.get_abspath()):
       return {}
   
   with open(file_node.get_abspath()) as file:
       file_contents = file.read()
       
   file_dir = file_node.get_dir().get_abspath()
   
   data = {}

   import shlex

   lex = shlex.shlex(instream=file_contents, posix=True)
   lex.wordchars += "*+./-:@$()"
   lex.whitespace = lex.whitespace.replace("\n", "")
   lex.escape = ""

   lineno = lex.lineno
   token = lex.get_token()
   key = token   # the first token should be a key
   last_token = ""
   key_token = True
   new_data = True
   
   def append_data(data, key, new_data, token):
      if token[:2] == "$(":
         try:
            token = env[token[2:token.find(")")]]
         except KeyError:
            print "ERROR: Variable %s used in Doxygen file is not in environment!" % token
            token = ""
         # Convert space-separated list to actual list
         token = token.split()
         if len(token):
            append_data(data, key, new_data, token[0])
            for i in token[1:]:
               append_data(data, key, True, i)
         return

      if new_data or len(data[key]) == 0:
         data[key].append(token)
      else:
         data[key][-1] += token

   while token:
      if token in ['\n']:
         if last_token not in ['\\']:
            key_token = True
      elif token in ['\\']:
         pass
      elif key_token:
         key = token
         key_token = False
      else:
         if token == "+=":
            if not data.has_key(key):
               data[key] = list()
         elif token == "=":
            if key == "TAGFILES" and data.has_key(key):
               append_data(data, key, False, "=")
               new_data = False
            else:
               data[key] = list()
         elif key == "@INCLUDE":

            filename = token
            if not os.path.isabs(filename):
               filename = os.path.join(file_dir, filename)

            lex.push_source(open(filename), filename)
         else:
            append_data(data, key, new_data, token)
            new_data = True

      last_token = token
      token = lex.get_token()

      if last_token == '\\' and token != '\n':
         new_data = False
         append_data(data, key, new_data, '\\')

   # compress lists of len 1 into single strings
   for (k, v) in data.items():
      if len(v) == 0:
         data.pop(k)

      # items in the following list will be kept as lists and not converted to strings
      if k in ["INPUT", "FILE_PATTERNS", "EXCLUDE_PATTERNS", "TAGFILES"]:
         continue

      if len(v) == 1:
         data[k] = v[0]

   return data

def getInputDirs(registry, packagename):
    """
    Gets the input directories using this package's build settings.
    """
    doxyfilepath = registry.getPackageDir(packagename).get_abspath()
    
    buildSettings = registry.getBuildSettings(packagename)
    sourceDirs = set()
    includeBasedir = registry.getPackageDir(packagename)
    for targetname, settings in buildSettings.items():
        # directories of own cpp files
        for sourcefile in settings.get("sourceFiles", []):
            if isinstance(sourcefile, SCons.Node.FS.File):
                sourceDirs.add(os.path.relpath(sourcefile.srcnode().dir.abspath, doxyfilepath))

        # include directory of own private headers
        includeSubdirPrivate = settings.get("includeSubdir", '')
        sourceDirs.add(os.path.relpath(includeBasedir.Dir(includeSubdirPrivate).abspath, doxyfilepath))
                    
        # include directory of own public headers
        includeSubdirPublic = settings.get("public", {}).get("includeSubdir", '')
        sourceDirs.add(os.path.relpath(includeBasedir.Dir(includeSubdirPublic).abspath, doxyfilepath))

        # directories of own public headers which are going to be copied
        for sourcefile in settings.get("public", {}).get("includes", []):
            if isinstance(sourcefile, SCons.Node.FS.File):
                sourceDirs.add(os.path.relpath(sourcefile.srcnode().dir.abspath, doxyfilepath))
    
    return sourceDirs

def getSourceFiles(registry, packagename):
    """
    Gets the source files using this package's build settings.
    """
    sources = []
    buildSettings = registry.getBuildSettings(packagename)
    for targetname, settings in buildSettings.items():
        for sourcefile in settings.get("sourceFiles", []):
            if isinstance(sourcefile, SCons.Node.FS.File):
                sources.append(sourcefile)
    # headers are appended through CPPScanner
    return sources

def getTagfileDependencyLines(target, ownData, dependencies, env):
    """
    Returns the tagfile lines in Doxyfile format.
    target is the current Doxyfile.
    ownData is the parsed content of the current Doxyfile.
    dependencies are the Doxyfiles on which the current Doxyfile depends.
    env is the current Environment.
    Parses the dependencies, gets their tagfile and determines the path relative to the current Doxyfile.
    """
    deps = []
    
    ownPath = ownData.get("HTML_OUTPUT", 'html')
    if not os.path.isabs(ownPath):
        ownPath = os.path.join(ownData.get("OUTPUT_DIRECTORY", ''), ownPath)
        if not os.path.isabs(ownPath):
            ownPath = os.path.realpath(os.path.join(target.dir.get_abspath(), ownPath))
    
    for doxyfile in dependencies:
        if doxyfile:
            data = getDoxyfileData(doxyfile, env)
            tagfile = data.get('GENERATE_TAGFILE', '')
            if tagfile:
                tagfilePath = os.path.realpath(os.path.join(doxyfile.dir.get_abspath(), tagfile))
                tagfileRelPath = os.path.relpath(tagfilePath, target.dir.get_abspath())
                
                linkPath = data.get("HTML_OUTPUT", 'html')
                if not os.path.isabs(linkPath):
                    linkPath = os.path.join(data.get("OUTPUT_DIRECTORY", ''), linkPath)
                    if not os.path.isabs(linkPath):
                        linkPath = os.path.realpath(os.path.join(doxyfile.dir.get_abspath(), linkPath))

                linkRelPath = os.path.relpath(linkPath, ownPath)
                
                deps.append("%s=%s" % (tagfileRelPath, linkRelPath))
    
    return deps

def buildDoxyfile(target, source, env):    
    """
    Creates the Doxyfile.
    The first (and only) target should be the Doxyfile.
    Sourcefiles are used for dependency tracking only.
    """
    if not os.path.isfile(target[0].get_abspath()):
        proc = subprocess.Popen(["doxygen", "-s", "-g", target[0].get_abspath()], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res = proc.wait()
        
        data = env.get('doxyDefaults', {})
        if data:
            with open(target[0].get_abspath(), 'a') as doxyfile:
                for k, v in data.items():
                    doxyfile.write("%s = %s\n" % (k, v))
    
    data = parseDoxyfile(target[0], env) # needs to be uncached
    
    with open(str(target[0]), 'a') as doxyfile:    
        inputDirs = env.get('inputDirs', [])
        if inputDirs:
            doxyfile.write("INPUT = \\\n")
            for s in inputDirs:
                doxyfile.write("%s \\\n" % s)
            doxyfile.write("\n")

        dependencies = env.get('dependencies', [])
        if dependencies:
            doxyfile.write("TAGFILES = \\\n")
            for tagfileline in getTagfileDependencyLines(target[0], data, dependencies, env):
                doxyfile.write("%s \\\n" % tagfileline)
            doxyfile.write("\n")
    
    proc = subprocess.Popen(["doxygen", "-s", "-u", target[0].get_abspath()], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = proc.wait()
                
# don't need this for now... hopefully works with tag files
#        target = registry.getPackageTarget(packagename, targetname)["plaintarget"]
#        if target and target.has_builder():
#            for cpppath in target.env["CPPPATH"]:
#                print cpppath.srcnode().abspath
#                includeDirs.add(cpppath.srcnode().abspath)

def callDoxygen(target, source, env):   
    """
    Creates the output directory (doxygen can't do that recursively) and calls doxygen.
    The first source must be the Doxyfile, the other sources are used for dependency tracking only.
    """
    data = getDoxyfileData(source[0], env)
    doxyfilepath = source[0].get_dir().get_abspath()
    outputpath = data.get("OUTPUT_DIRECTORY", '')
    if not os.path.isabs(outputpath):
        outputpath = os.path.realpath(os.path.join(doxyfilepath, outputpath))
    if not os.path.isdir(outputpath):
        os.makedirs(outputpath)
    
    cmd = "cd %s && %s %s" % (source[0].get_dir().get_abspath(), "doxygen", os.path.basename(str(source[0])))
    
    log_out = None
    log_err = None
    
    logfilebasename = env.get('logname', '')
    if logfilebasename:
        logpath = env['BASEOUTDIR'].Dir(os.path.join(env['LOGDIR'])).get_abspath()
        if not os.path.isdir(logpath):
            os.makedirs(logpath)
        log_out = open(os.path.join(logpath, logfilebasename + '.stdout'), 'w')
        log_err = open(os.path.join(logpath, logfilebasename + '.stderr'), 'w')
        
    proc = subprocess.Popen(cmd, shell=True, stdout=log_out, stderr=log_err)
    res = proc.wait()
    
    if log_out:
        log_out.close()
    if log_err:
        log_err.close()

def emitDoxygen(target, source, env):
    """
    Adds the tagfile and the output directories as the doxygen targets.
    The first source must be the Doxyfile, the other sources are used for dependency tracking only.
    The target array will be overwritten.
    """
    data = env.get("doxyDefaults", {})
    if os.path.isfile(source[0].get_abspath()):
        data = parseDoxyfile(source[0], env) # needs to be uncached
    
    doxyfilepath = source[0].get_dir().get_abspath()
    
    target = []
    tagfile = data.get("GENERATE_TAGFILE", '')
    if tagfile:
        path = tagfile
        if not os.path.isabs(tagfile):
            path = os.path.realpath(os.path.join(doxyfilepath, path))
        target.append(env.File(path))

    outputpath = data.get("OUTPUT_DIRECTORY", '')
    if not os.path.isabs(outputpath):
        outputpath = os.path.realpath(os.path.join(doxyfilepath, outputpath))

    for format in ["HTML", "LATEX", "RTF", "MAN", "XML"]:
        generate = data.get("GENERATE_" + format, "NO").upper()
        destination = data.get(format + "_OUTPUT", format.lower())
        
        if generate == "YES" and destination:
            path = destination
            if not os.path.isabs(path):
                path = os.path.realpath(os.path.join(outputpath, path))
            target.append(env.Dir(path))
    
    env.Clean(target, outputpath)
    for t in target:
        env.Clean(target, t)
    
    return target, source

def getDoxyDefaults(env, registry, packagename):
    """
    Determines the default Doxyfile settings for a package.
    Used if the Doxyfile is not yet existing.
    """
    outputpath = os.path.relpath(env['BASEOUTDIR'].Dir(env['DOCDIR']).Dir(packagename).get_abspath(),
                                                registry.getPackageDir(packagename).get_abspath())
    return {
            'OUTPUT_DIRECTORY': outputpath,
            'PROJECT_NAME': packagename,
            'GENERATE_HTML': 'YES',
            'HTML_OUTPUT': 'html',
            'GENERATE_LATEX': 'NO',
            'GENERATE_TAGFILE': os.path.join(outputpath, packagename+'.tag'),
            }

def createDoxygenTarget(env, registry, packagename):
    """
    Wrapper for creating a doxygen target for a package.
    """
    if not GetOption('doxygen'):
        return None
    
    defaults = getDoxyDefaults(env, registry, packagename)
    doxyfileTarget = env.DoxyfileBuilder(target=registry.getPackageDir(packagename).File('Doxyfile'),
                                         source=registry.getPackageFile(packagename),
                                         inputDirs=getInputDirs(registry, packagename),
                                         dependencies=getDoxyfileDependencies(registry, packagename, recursive=True),
                                         doxyDefaults=defaults)
    env.Precious(doxyfileTarget)
    env.NoClean(doxyfileTarget)
    registerPackageDoxyfile(packagename, doxyfileTarget[0])
    env.Depends(doxyfileTarget[0], getDoxyfileDependencies(registry, packagename))
    
    doxySources = doxyfileTarget[:]
    doxySources.extend(getSourceFiles(registry, packagename))
    doxyTarget = env.DoxygenBuilder(source=doxySources,
                                    doxyDefaults=defaults,
                                    logname='doxygen_' + packagename)
    if doxyTarget and isinstance(doxyTarget[0], SCons.Node.FS.File):
        registerPackageTagfile(packagename, doxyTarget[0])
        env.Depends(doxyTarget[0], getTagfileDependencies(registry, packagename))

    env.Depends(doxyfileTarget, SomeUtils.getPyFilename(__file__))
    env.Depends(doxyTarget, SomeUtils.getPyFilename(__file__))
    return doxyTarget

class DoxygenToolException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def generate(env):
    """
    Add the options, builders and wrappers to the current Environment.
    """
    try:
        AddOption('--doxygen', dest='doxygen', action='store_true', default=False, help='Create documentation')
    except optparse.OptionConflictError:
        raise DoxygenToolException("Only one Doxygen-Tool instance allowed")

    doxyfileAction = SCons.Action.Action(buildDoxyfile, "Creating Doxygen config file '$TARGET'")
    doxyfileBuilder = SCons.Builder.Builder(action=doxyfileAction,
                                            source_scanner=SCons.Scanner.C.CScanner()) # adds headers as dependencies

    doxygenAction = SCons.Action.Action(callDoxygen, "Creating documentation using '$SOURCE'")
    doxygenBuilder = SCons.Builder.Builder(action=doxygenAction,
                                           emitter=emitDoxygen,
                                           source_scanner=SCons.Scanner.C.CScanner()) # adds headers as dependencies)

    env.Append(BUILDERS={ 'DoxygenBuilder' : doxygenBuilder })
    env.Append(BUILDERS={ 'DoxyfileBuilder' : doxyfileBuilder })
    env.AddMethod(createDoxygenTarget, "PackageDoxygen")

def exists(env):
   """
   Make sure doxygen exists.
   """
   return env.Detect("doxygen")
