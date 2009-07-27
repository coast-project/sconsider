from __future__ import with_statement
import os, pdb, subprocess, optparse
from SCons.Script import AddOption, GetOption
import SCons.Action
import SCons.Builder

def parseDoxyfile(file_node, env):
   """
   Parse a Doxygen source file and return a dictionary of all the values.
   Values will be strings and lists of strings.
   """
   file_dir = file_node.get_dir().get_abspath()
   file_contents = file_node.get_contents()
   
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
         data[key][ - 1] += token

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

def buildDoxyfile(target, source, env):
    if not env["registry"] or not env["packagename"]:
        return False
    
    for t in target:
        registry = env["registry"]
        packagename = env["packagename"]  
        if not os.path.isfile(t.get_abspath()):
            proc = subprocess.Popen(["doxygen", "-s", "-g", str(t)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res = proc.wait()
            
            data = env["doxyDefaults"]
            with open(str(t), 'a') as doxyfile:
                for k, v in data.items():
                    doxyfile.write("%s = %s\n" % (k, v))
        
        doxyfilepath = t.get_dir().get_abspath()
                
        buildSettings = registry.getBuildSettings(packagename)
        sourceDirs = set()
        includeBasedir = registry.getPackageDir(packagename)
        for targetname, settings in buildSettings.items():
            # directories of own cpp files
            for sourcefile in settings.get("sourceFiles", []):
                sourceDirs.add(os.path.relpath(sourcefile.srcnode().dir.abspath, doxyfilepath))
    
            # include directory of own private headers
            includeSubdirPrivate = settings.get("includeSubdir", '')
            sourceDirs.add(os.path.relpath(includeBasedir.Dir(includeSubdirPrivate).abspath, doxyfilepath))
                        
            # include directory of own public headers
            includeSubdirPublic = settings.get("public", {}).get("includeSubdir", '')
            sourceDirs.add(os.path.relpath(includeBasedir.Dir(includeSubdirPublic).abspath, doxyfilepath))
    
            # directories of own public headers which are going to be copied
            for sourcefile in settings.get("public", {}).get("includes", []):
                sourceDirs.add(os.path.relpath(sourcefile.srcnode().dir.abspath, doxyfilepath))
        
        with open(str(t), 'a') as doxyfile:
            doxyfile.write("INPUT = \\\n")
            for s in sourceDirs:
                doxyfile.write("%s \\\n" % s)
        
        proc = subprocess.Popen(["doxygen", "-s", "-u", str(t)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res = proc.wait()
                
# don't need this for now... hopefully works with tag files
#        target = registry.getPackageTarget(packagename, targetname)["plaintarget"]
#        if target and target.has_builder():
#            for cpppath in target.env["CPPPATH"]:
#                print cpppath.srcnode().abspath
#                includeDirs.add(cpppath.srcnode().abspath)

def emitDoxyfile(target, source, env):
    if not env["registry"] or not env["packagename"]:
        return target, source
    
    registry = env["registry"]
    packagename = env["packagename"]

    buildSettings = registry.getBuildSettings(packagename)
    for targetname, settings in buildSettings.items():
        for sourcefile in settings.get("sourceFiles", []):
            source.append(sourcefile)
            # headers are appended through CPPScanner
    
    if not target:
        doxyfile = registry.getPackageDir(packagename).File('Doxyfile')
        target.append(doxyfile)
        env.Precious(doxyfile)
        env.NoClean(doxyfile)

    return target, source

def callDoxygen(target, source, env):
    """
    Creates the output directory (doxygen can't do that recursively) and calls doxygen.
    The first (and only) source should be the Doxyfile.
    """
    data = parseDoxyfile(source[0], env)
    doxyfilepath = source[0].get_dir().get_abspath()
    outputpath = os.path.realpath(os.path.join(doxyfilepath, data.get("OUTPUT_DIRECTORY", '')))
    if not os.path.isdir(outputpath):
        os.makedirs(outputpath)
    
    cmd = "cd %s && %s %s" % (source[0].get_dir().get_abspath(), "doxygen", os.path.basename(str(source[0])))
    
    logpath = env['BASEOUTDIR'].Dir(os.path.join(env['LOGDIR'])).get_abspath()
    logfilebasename = 'doxygen_' + env["packagename"]
    
    if not os.path.isdir(logpath):
        os.makedirs(logpath)
    
    with open(os.path.join(logpath, logfilebasename + '.stdout'), 'w') as outfile:
        with open(os.path.join(logpath, logfilebasename + '.stderr'), 'w') as errfile:
            proc = subprocess.Popen(cmd, shell=True, stdout=outfile, stderr=errfile)
            res = proc.wait()

def callDoxygenMessage(target, source, env):
    return "Creating documentation for '%s'" % env["packagename"]

def emitDoxygen(target, source, env):
    """
    Adds the output directories as the doxygen targets, representative of
    all of the files which will be generated by doxygen. The first (and
    only) source should be the Doxyfile.
    """
    
    data = env["doxyDefaults"]
    doxyfilepath = source[0].get_dir().get_abspath()
    if os.path.isfile(source[0].get_abspath()):
        data = parseDoxyfile(source[0], env)
    
    if not target:
        for format in ["HTML", "LATEX", "RTF", "MAN", "XML"]:
            generate = data.get("GENERATE_"+format, "NO").upper()
            destination = data.get(format+"_OUTPUT", format.lower())
            
            if generate == "YES" and destination:
                if os.path.isabs(destination):
                    path = destination
                else: 
                    path = os.path.join(data.get("OUTPUT_DIRECTORY", ''), destination)
                    if not os.path.isabs(path):
                        path = os.path.realpath(os.path.join(doxyfilepath, path))

                target.append(env.Dir(path))

    return target, source

def getDoxyDefaults(env, registry, packagename):
    return {
            'OUTPUT_DIRECTORY': os.path.relpath(env['BASEOUTDIR'].Dir(env['DOCDIR']).Dir(packagename).get_abspath(),
                                                registry.getPackageDir(packagename).get_abspath()),
            'PROJECT_NAME': packagename,
            'GENERATE_HTML': 'YES',
            'HTML_OUTPUT': 'html',
            'GENERATE_LATEX': 'NO',
            }

def createDoxygenTarget(env, registry, packagename):
    if not GetOption('doxygen'):
        return None
    
    defaults = getDoxyDefaults(env, registry, packagename)
    doxyfileTarget = env.DoxyFileBuilder(registry=registry, packagename=packagename, doxyDefaults=defaults)
    doxyTarget = env.DoxygenBuilder([], doxyfileTarget, packagename=packagename, doxyDefaults=defaults)

    return doxyTarget
    
def generate(env):
    try:
        AddOption('--doxygen', dest='doxygen', action='store_true', default=False, help='Create documentation')
    except optparse.OptionConflictError:
        pass

    doxyfileAction = SCons.Action.Action(buildDoxyfile, "Creating Doxygen config file '$TARGET'")
    doxyfileBuilder = SCons.Builder.Builder(action=doxyfileAction,
                                            emitter=emitDoxyfile,
                                            source_scanner=SCons.Scanner.C.CScanner()) # adds headers as dependencies

    doxygenAction = SCons.Action.Action(callDoxygen, callDoxygenMessage)
    doxygenBuilder = SCons.Builder.Builder(action=doxygenAction,
                                           emitter=emitDoxygen,
                                           single_source=True)

    env.Append(BUILDERS={ 'DoxygenBuilder' : doxygenBuilder })
    env.Append(BUILDERS={ 'DoxyFileBuilder' : doxyfileBuilder })
    env.AddMethod(createDoxygenTarget, "Doxygen")

def exists(env):
   """
   Make sure doxygen exists.
   """
   return env.Detect("doxygen")
