"""SConsider.site_tools.DoxygenBuilder.

Builder to generate doxygen API documentation. It automatically adds a
doxygen target for every target specified.
"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

from __future__ import with_statement
import os
import re
from logging import getLogger
from SConsider.PopenHelper import ProcessRunner
logger = getLogger(__name__)


def __get_buildsettings(registry, packagename):
    if hasattr(registry, 'getBuildSettings'):
        buildSettings = registry.getBuildSettings(packagename)
    else:
        buildSettings = {}
    return buildSettings


def __get_dependencies(registry, packagename, fnobj, recursive=False):
    dependencies = set()

    buildSettings = __get_buildsettings(registry, packagename)
    for _, settings in buildSettings.items():
        deps = settings.get('requires', []) + settings.get('linkDependencies', [])
        usedTarget = settings.get('usedTarget', '')
        if usedTarget:
            deps.append(usedTarget)

        for ftn in deps:
            from SConsider.PackageRegistry import PackageRegistry
            depPkgname, _ = PackageRegistry.splitFulltargetname(ftn)
            if not depPkgname == packagename:
                value = fnobj(depPkgname)
                if value:
                    if hasattr(value, '__iter__'):
                        dependencies.update(value)
                    else:
                        dependencies.add(value)
                if recursive:
                    dependencies.update(__get_dependencies(registry, depPkgname, fnobj, recursive))

    return list(dependencies)


def getPackageDependencies(registry, packagename, recursive=False):
    return __get_dependencies(registry, packagename, lambda pkg: pkg, recursive)


doxyfiles = {}


def registerPackageDoxyfile(packagename, doxyfile):
    doxyfiles[packagename] = doxyfile


def getPackageDoxyfile(packagename):
    return doxyfiles[packagename]


def getPackageInputDirs(registry, packagename, relativeTo=None):
    """Gets the input directories using this package's build settings."""
    if not relativeTo:
        relativeTo = registry.getPackageDir(packagename).get_abspath()

    sourceDirs = set()
    includeBasedir = registry.getPackageDir(packagename)

    def resolvePath(abspath, relativeTo=None):
        if relativeTo:
            return os.path.relpath(abspath, relativeTo)
        else:
            return abspath

    buildSettings = __get_buildsettings(registry, packagename)
    from SCons.Node import FS
    for _, settings in buildSettings.items():
        # directories of own cpp files
        for sourcefile in settings.get('sourceFiles', []):
            if not isinstance(sourcefile, FS.File):
                sourcefile = includeBasedir.File(sourcefile)
            sourceDirs.add(resolvePath(sourcefile.srcnode().dir.get_abspath(), relativeTo))

        # include directory of own private headers
        includeSubdirPrivate = settings.get('includeSubdir', '')
        sourceDirs.add(resolvePath(includeBasedir.Dir(includeSubdirPrivate).get_abspath(), relativeTo))

        # include directory of own public headers
        includeSubdirPublic = settings.get('public', {}).get('includeSubdir', '')
        sourceDirs.add(resolvePath(includeBasedir.Dir(includeSubdirPublic).get_abspath(), relativeTo))

        # directories of own public headers which are going to be copied
        for sourcefile in settings.get('public', {}).get('includes', []):
            if not isinstance(sourcefile, FS.File):
                sourcefile = includeBasedir.File(sourcefile)
            sourceDirs.add(resolvePath(sourcefile.srcnode().dir.get_abspath(), relativeTo))

    return sourceDirs


def getHeaderFiles(registry, packagename):
    """Gets the header files using this package's build settings."""
    headers = []
    buildSettings = __get_buildsettings(registry, packagename)
    for _, settings in buildSettings.items():
        for headerFile in settings.get("public", {}).get("includes", []):
            import SCons
            if isinstance(headerFile, SCons.Node.FS.File):
                headers.append(headerFile.srcnode().get_abspath())

    return headers


def getSourceFiles(registry, packagename):
    """Gets the source files using this package's build settings."""
    sources = []
    buildSettings = __get_buildsettings(registry, packagename)
    for _, settings in buildSettings.items():
        for sourcefile in settings.get('sourceFiles', []):
            import SCons
            if isinstance(sourcefile, SCons.Node.FS.File):
                sources.append(sourcefile.srcnode().get_abspath())
    # headers are appended through CPPScanner
    return sources


doxyfiledata = {}


def getDoxyfileData(doxyfile, env):
    """Caches parsed Doxyfile content."""
    if not doxyfiledata.get(doxyfile.get_abspath(), {}):
        doxyfiledata[doxyfile.get_abspath()] = parseDoxyfile(doxyfile, env)

    return doxyfiledata[doxyfile.get_abspath()]


def setDoxyfileData(doxyfile, doxyDict):
    doxyfiledata[doxyfile.get_abspath()] = doxyDict


def getDoxyfileTemplate():
    _cmd = ['doxygen', '-s', '-g', '-']
    _out = ''
    with ProcessRunner(_cmd, timeout=30) as executor:
        for out, _ in executor:
            _out += out
    return parseDoxyfileContent(_out, {})


def parseDoxyfile(file_node, env):
    if not os.path.isfile(file_node.get_abspath()):
        return {}

    with open(file_node.get_abspath()) as doxyfile:
        file_contents = doxyfile.read()

    include_basepath = file_node.get_dir().get_abspath()

    return parseDoxyfileContent(file_contents, env, include_basepath)


def parseDoxyfileContent(file_content, env, include_basepath=None):
    """Parse a Doxygen source string and return a dictionary of all the values.

    Values will be strings and lists of strings.
    """
    data = {}

    import shlex

    lex = shlex.shlex(instream=file_content, posix=True)
    lex.wordchars += '*+./-:@$()'
    lex.whitespace = lex.whitespace.replace('\n', '')

    token = lex.get_token()
    key = token  # the first token should be a key
    last_token = ''
    key_token = True
    new_data = True

    def append_data(data, key, new_data, token):
        if token[:2] == '$(':
            try:
                token = env[token[2:token.find(')')]]
            except KeyError:
                logger.warning("Variable %s used in Doxygen file is not in environment!", token)
                token = ''
            # Convert space-separated list to actual list
            token = token.split()
            if token:
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
            if token == '+=':
                if key not in data:
                    data[key] = list()
            elif token == '=':
                if key == 'TAGFILES' and key in data:
                    append_data(data, key, False, '=')
                    new_data = False
                else:
                    data[key] = list()
            elif key == '@INCLUDE':
                filename = token
                if os.path.isabs(filename) or include_basepath:
                    if not os.path.isabs(filename):
                        filename = os.path.join(include_basepath, filename)
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
        if not v:
            data.pop(k)

        # items in the following list will be kept as lists and not converted
        # to strings
        if k in [
                'INPUT',
                'FILE_PATTERNS',
                'EXCLUDE_PATTERNS',
                'TAGFILES',
                'INCLUDE_PATH',
                'INCLUDE_FILE_PATTERNS',
        ]:
            continue

        if len(v) == 1:
            data[k] = v[0]

    return data


def writeDoxyfile(doxyfilepath, data):
    with open(doxyfilepath, 'a') as doxyfile:
        for key, value in data.iteritems():
            if hasattr(value, '__iter__'):
                doxyfile.write('%s = \\\n' % key)
                for v in value:
                    doxyfile.write('%s \\\n' % v)
                doxyfile.write('\n')
            else:
                doxyfile.write('%s = %s\n' % (key, value))


def getTagfileDependencyLine(ownDoxyfile, ownData, otherDoxyfile, env):
    """Returns the tagfile lines in Doxyfile format.

    ownDoxyfile is the current Doxyfile. ownData is the parsed data of
    the current Doxyfile. doxyfiles are the Doxyfiles on which the
    current Doxyfile depends. env is the current Environment. Parses the
    doxyfiles, gets their tagfile and determines the path relative to
    the current Doxyfile.
    """
    ownPath = ownData.get('HTML_OUTPUT', 'html')
    if not os.path.isabs(ownPath):
        ownPath = os.path.join(ownData.get('OUTPUT_DIRECTORY', ''), ownPath)
        if not os.path.isabs(ownPath):
            ownPath = os.path.realpath(os.path.join(ownDoxyfile.dir.get_abspath(), ownPath))

    otherData = getDoxyfileData(otherDoxyfile, env)
    tagfile = otherData.get('GENERATE_TAGFILE', '')

    tagfilePath = os.path.realpath(os.path.join(otherDoxyfile.dir.get_abspath(), tagfile))
    tagfileRelPath = os.path.relpath(tagfilePath, ownDoxyfile.dir.get_abspath())

    linkPath = otherData.get('HTML_OUTPUT', 'html')
    if not os.path.isabs(linkPath):
        linkPath = os.path.join(otherData.get('OUTPUT_DIRECTORY', ''), linkPath)
        if not os.path.isabs(linkPath):
            linkPath = os.path.realpath(os.path.join(otherDoxyfile.dir.get_abspath(), linkPath))

    linkRelPath = os.path.relpath(linkPath, ownPath)
    return '%s=%s' % (tagfileRelPath, linkRelPath)


def buildDoxyfile(target, env, **kw):
    """Creates the Doxyfile.

    The first (and only) target should be the Doxyfile. Sourcefiles are
    used for dependency tracking only.
    """
    writeDoxyfile(str(target[0]), env.get('data', {}))

    with open(str(target[0]), 'a') as doxyfile:
        doxyfile.write('PREDEFINED = \\\n')
        defines = {}
        defines.update(compilerDefines)
        for define in env.get('CPPDEFINES', []):
            defines[define] = ''

        for define, value in defines.iteritems():
            if value:
                if value.find(' ') != -1:
                    doxyfile.write('"%s=%s" \\\n' % (define, value))
                else:
                    doxyfile.write('%s=%s \\\n' % (define, value))
            else:
                doxyfile.write('%s \\\n' % define)
        doxyfile.write('\n')

    try:
        log_out, log_err = openLogFiles(env)
        _cmd = ['doxygen', '-s', '-u', target[0].get_abspath()]
        with ProcessRunner(_cmd, timeout=60) as executor:
            for out, err in executor:
                log_out.write(out)
                log_err.write(err)
    finally:
        closeLogFiles(log_out, log_err)


def openLogFiles(env):
    log_out = None
    log_err = None

    logfilebasename = env.get('logname', '')
    if logfilebasename:
        logpath = env.getLogInstallDir().get_abspath()
        if not os.path.isdir(logpath):
            os.makedirs(logpath)
        log_out = open(os.path.join(logpath, logfilebasename + '.stdout'), 'w')
        log_err = open(os.path.join(logpath, logfilebasename + '.stderr'), 'w')

    return (log_out, log_err)


def closeLogFiles(log_out, log_err):
    if log_out:
        log_out.close()
    if log_err:
        log_err.close()


def callDoxygen(source, env, **kw):
    """Creates the output directory (doxygen can't do that recursively) and
    calls doxygen.

    The first source must be the Doxyfile, the other sources are used
    for dependency tracking only.
    """
    data = env.get('data', {})
    outputpath = data.get('OUTPUT_DIRECTORY', '')
    if not os.path.isabs(outputpath):
        doxyfilepath = source[0].get_dir().get_abspath()
        outputpath = os.path.realpath(os.path.join(doxyfilepath, outputpath))
    if not os.path.isdir(outputpath):
        os.makedirs(outputpath)

    cmd = 'cd %s && %s %s' % (source[0].get_dir().get_abspath(), 'doxygen', os.path.basename(str(source[0])))

    try:
        log_out, log_err = openLogFiles(env)
        with ProcessRunner(cmd, timeout=300, shell=True) as executor:
            for out, err in executor:
                log_out.write(out)
                log_err.write(err)
    finally:
        closeLogFiles(log_out, log_err)


def emitDoxygen(target, source, env):
    """Adds the tagfile and the output directories as the doxygen targets.

    The first source must be the Doxyfile, the other sources are used
    for dependency tracking only. The target array will be overwritten.
    """
    data = env.get('data', {})
    doxyfilepath = source[0].get_dir().get_abspath()

    target = []
    tagfile = data.get('GENERATE_TAGFILE', '')
    if tagfile:
        path = tagfile
        if not os.path.isabs(tagfile):
            path = os.path.realpath(os.path.join(doxyfilepath, path))
        target.append(env.File(path))

    outputpath = data.get('OUTPUT_DIRECTORY', '')
    if not os.path.isabs(outputpath):
        outputpath = os.path.realpath(os.path.join(doxyfilepath, outputpath))

    for output_format in ['HTML', 'LATEX', 'RTF', 'MAN', 'XML']:
        generate_output = data.get('GENERATE_' + output_format, 'NO').upper()
        destination = data.get(output_format + '_OUTPUT', output_format.lower())

        if generate_output == 'YES' and destination:
            path = destination
            if not os.path.isabs(path):
                path = os.path.realpath(os.path.join(outputpath, path))
            target.append(env.Dir(path))

    env.Clean(target, outputpath)
    for j in target:
        env.Clean(target, j)

    return (target, source)


def getDoxyDefaults(env, registry, packagename=''):
    """Determines the default Doxyfile settings for a package or for the whole
    coast project.

    Used if the Doxyfile is not yet existing.
    """

    baseOutDir = env.getBaseOutDir()
    if not packagename:
        packagename = 'Coast'
        basepathrel = os.path.relpath(os.path.curdir, baseOutDir.get_abspath())
        outputpath = os.path.relpath(
            baseOutDir.Dir(env['DOCDIR']).Dir(packagename).get_abspath(), baseOutDir.get_abspath())
    else:
        basepathrel = os.path.relpath(baseOutDir.get_abspath(),
                                      registry.getPackageDir(packagename).get_abspath())
        outputpath = os.path.relpath(
            baseOutDir.Dir(env['DOCDIR']).Dir(packagename).get_abspath(),
            registry.getPackageDir(packagename).get_abspath())

    file_patterns = \
        '*.c *.cc *.cxx *.cpp *.c++ *.java *.ii *.ixx *.ipp *.i++ *.inl *.h '\
        '*.hh *.hxx *.hpp *.h++ *.idl *.odl *.cs *.php *.php3 *.inc *.m *.mm'\
        ' *.py *.f90'.split(' ') + ['*.sh', '*.any', '*.sconsider']
    include_file_patterns = '*.h *.hh *.hxx *.hpp *.h++'.split(' ')

    doxyDefaults = {
        'PROJECT_NAME': packagename,
        'OUTPUT_DIRECTORY': outputpath,
        'IMAGE_PATH': basepathrel,
        'INPUT_ENCODING': 'ISO-8859-1',
        'TAB_SIZE': '4',
        'BUILTIN_STL_SUPPORT': 'YES',
        'EXTRACT_ALL': 'YES',
        'EXTRACT_STATIC': 'YES',
        'EXTRACT_LOCAL_METHODS': 'YES',
        'SOURCE_BROWSER': 'YES',
        'REFERENCES_RELATION': 'YES',
        'ALPHABETICAL_INDEX': 'YES',
        'SEARCHENGINE': 'NO',
        'SEARCH_INCLUDES': 'YES',
        'HIDE_UNDOC_RELATIONS': 'NO',
        'HAVE_DOT': 'YES',
        'TEMPLATE_RELATIONS': 'YES',
        'DOT_TRANSPARENT': 'YES',
        'SORT_BY_SCOPE_NAME': 'YES',
        'SORT_MEMBERS_CTORS_1ST': 'YES',
        'SHOW_USED_FILES': 'NO',
        'LAYOUT_FILE': os.path.join(basepathrel, 'DoxygenLayout.xml'),
        'FILE_PATTERNS': ' '.join(file_patterns),
        'INCLUDE_FILE_PATTERNS': ' '.join(include_file_patterns),
        'GENERATE_ECLIPSEHELP': 'NO',
        'DOT_GRAPH_MAX_NODES': '80',
        'MAX_DOT_GRAPH_DEPTH': '7',
        'DOT_CLEANUP': 'NO',
        'FULL_PATH_NAMES': 'NO',
        'SORT_GROUP_NAMES': 'YES',
        'DOT_MULTI_TARGETS': 'YES',
        'DOT_NUM_THREADS': '2',
        'MULTILINE_CPP_IS_BRIEF': 'NO',
        'REPEAT_BRIEF': 'NO',
        'EXTENSION_MAPPING': ' '.join(['sh=Python', 'sconsider=Python', 'any=Python']),
        'GENERATE_HTML': 'YES',
        'HTML_OUTPUT': 'html',
        'GENERATE_LATEX': 'NO',
        'LATEX_HIDE_INDICES': 'YES',
        'ALIASES': '"FIXME=\\xrefitem FIXME \\"Fixme\\" \\"Locations to fix when possible\\" "',
    }
    return doxyDefaults


def createDoxygenTarget(env, registry, packagename):
    """Wrapper for creating a doxygen target for a package."""

    doxyfile = registry.getPackageDir(packagename).File('Doxyfile')

    doxyData = getDoxyfileData(doxyfile, env)
    if not doxyData:
        doxyData = getDoxyfileTemplate()
        doxyData.update(getDoxyDefaults(env, registry, packagename))

    doxyData['INPUT'] = set()
    doxyData['INCLUDE_PATH'] = set()
    doxyData['TAGFILES'] = []

    doxyData['INPUT'].update(getPackageInputDirs(registry, packagename))

    if '3rdparty' in doxyfile.get_dir().get_abspath():
        doxyData['GENERATE_TAGFILE'] = \
            os.path.join(doxyData.get('OUTPUT_DIRECTORY', ''),
                         packagename + '.tag')

    otherDoxyfileSources = []
    otherDoxygenSources = []
    packages = getPackageDependencies(registry, packagename, recursive=True)

    for otherPackage in packages:
        otherDoxyfile = getPackageDoxyfile(otherPackage)
        otherDoxyfileSources.append(otherDoxyfile)

        otherData = getDoxyfileData(otherDoxyfile, env)
        otherTagfile = otherData.get('GENERATE_TAGFILE', False)

        if otherTagfile:
            otherDoxygenSources.append(otherDoxyfile.get_dir().File(otherTagfile).get_abspath())

            doxyData['TAGFILES'].append(getTagfileDependencyLine(doxyfile, doxyData, otherDoxyfile, env))
        else:
            otherDoxyfileSources.append(registry.getPackageFile(otherPackage))
            otherDoxygenSources.extend(getSourceFiles(registry, otherPackage))
            otherDoxygenSources.extend(getHeaderFiles(registry, otherPackage))
            otherPackageDir = registry.getPackageDir(otherPackage)
            otherInputDirs = getPackageInputDirs(registry,
                                                 otherPackage,
                                                 relativeTo=doxyfile.get_dir().get_abspath())
            if '3rdparty' in otherPackageDir.get_abspath():
                doxyData['INCLUDE_PATH'].update(otherInputDirs)
                doxyData['SEARCH_INCLUDES'] = 'YES'
            else:
                doxyData['INPUT'].update(otherInputDirs)

    setDoxyfileData(doxyfile, doxyData)

    doxyfileSources = [registry.getPackageFile(packagename)]
    doxyfileSources.extend(otherDoxyfileSources)

    doxyfileTarget = env.DoxyfileBuilder(target=doxyfile,
                                         source=doxyfileSources,
                                         data=doxyData,
                                         logname='doxyfile_' + packagename)

    env.Precious(doxyfileTarget)
    env.NoClean(doxyfileTarget)

    registerPackageDoxyfile(packagename, doxyfileTarget[0])

    doxygenSources = doxyfileTarget[:]
    doxygenSources.extend(getSourceFiles(registry, packagename))
    doxygenSources.extend(getHeaderFiles(registry, packagename))
    doxygenSources.extend(otherDoxygenSources)

    doxygenTarget = env.DoxygenBuilder(source=doxygenSources, data=doxyData, logname='doxygen_' + packagename)

    from SConsider.SomeUtils import getPyFilename
    env.Depends(doxyfileTarget, getPyFilename(__file__))
    env.Depends(doxygenTarget, getPyFilename(__file__))
    env.Depends(doxygenTarget, doxyfileTarget)

    return doxygenTarget


def createDoxygenAllTarget(registry):
    """Wrapper for creating a doxygen target for coast."""

    from SConsider import cloneBaseEnv
    env = cloneBaseEnv()

    doxyfile = env.getBaseOutDir().File('Doxyfile')

    doxyData = getDoxyfileData(doxyfile, env)
    if not doxyData:
        doxyData = getDoxyfileTemplate()
        doxyData.update(getDoxyDefaults(env, registry))

    # FIXME temporary hack to get rid of doxygen problems with 3rdparty
    # packages

    thirdparty = [
        'openssl',
        'boost',
        'oracle',
        'mysql',
        'sybase',
        'zlib',
        'cute',
        'iplanetLDAP',
    ]

    def isExcludedPackage(packagename):
        if packagename in thirdparty:
            return True
        buildSettings = __get_buildsettings(registry, packagename)
        for _, settings in buildSettings.iteritems():
            if settings.get('runConfig', {}).get('type', '') == 'test':
                return True
        return False

    allPackageNames = [
        package_name for package_name in registry.getPackageNames() if not isExcludedPackage(package_name)
    ]
    allInputDirs = set()
    allPackageFiles = []

    for package_name in allPackageNames:
        allInputDirs.update(
            getPackageInputDirs(registry, package_name, relativeTo=env.getBaseOutDir().get_abspath()))
        allPackageFiles.append(registry.getPackageFile(package_name))

    doxyData['INPUT'] = []
    doxyData['INPUT'].extend(allInputDirs)

    # DoxyFileTarget: Dependent on all package sconsider files
    doxyfileTarget = env.DoxyfileBuilder(target=doxyfile,
                                         source=allPackageFiles,
                                         data=doxyData,
                                         logname='doxyfile_coast')

    env.Precious(doxyfileTarget)
    env.NoClean(doxyfileTarget)

    # DoxyTarget: Dependent on all header and source files of all packages
    doxySources = doxyfileTarget[:]

    for package_name in allPackageNames:
        doxySources.extend(getSourceFiles(registry, package_name))
        doxySources.extend(getHeaderFiles(registry, package_name))
    doxyTarget = env.DoxygenBuilder(source=doxySources, data=doxyData, logname='doxygen_coast')

    # DoxyFileTarget and DoxyTarget depend on this python file
    from SConsider.SomeUtils import getPyFilename
    env.Depends(doxyfileTarget, getPyFilename(__file__))
    env.Depends(doxyTarget, getPyFilename(__file__))
    env.Depends(doxyTarget, doxyfileTarget)

    return doxyTarget


class DoxygenToolException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def determineCompilerDefines(env):
    defines = {}
    ignores = [
        'cc',
        '__BASE_FILE__',
        '__DATE__',
        '__FILE__',
        '__LINE__',
        '__TIME__',
        '__TIMESTAMP__',
    ]
    pattern = re.compile(r'^([^\s]+)\s*=\s*(.*)\s*')

    cmd = 'PATH=' + env.get('ENV', []).get('PATH', '')
    cmd += ' ' + os.path.join(os.path.dirname(__file__), 'defines.sh')
    cmd += ' ' + env['CXX']

    with ProcessRunner(cmd, timeout=60, shell=True) as executor:
        for out, _ in executor:
            for line in out.splitlines():
                match = re.match(pattern, line)
                if match and match.group(1) not in ignores:
                    defines[match.group(1)] = match.group(2)

    return defines


compilerDefines = {}


def generate(env):
    """Add the options, builders and wrappers to the current Environment."""
    from SCons.Script import AddOption, GetOption, BUILD_TARGETS
    from SCons.Action import Action
    from SCons.Builder import Builder
    from SCons.Scanner.C import CScanner
    AddOption('--doxygen',
              dest='doxygen',
              action='store_true',
              default=False,
              help='Create module documentation')
    AddOption('--doxygen-only',
              dest='doxygen-only',
              action='store_true',
              default=False,
              help='Same as --doxygen but skips all targets except doxygen')

    doxyfileAction = Action(buildDoxyfile, "Creating Doxygen config file '$TARGET'")
    doxyfileBuilder = Builder(action=doxyfileAction,
                              source_scanner=CScanner())  # adds headers as dependencies

    doxygenAction = Action(callDoxygen, "Creating documentation using '$SOURCE'")
    # adds headers as dependencies
    doxygenBuilder = Builder(action=doxygenAction, emitter=emitDoxygen, source_scanner=CScanner())

    env.Append(BUILDERS={'DoxyfileBuilder': doxyfileBuilder})
    env.Append(BUILDERS={'DoxygenBuilder': doxygenBuilder})

    env.AddMethod(createDoxygenTarget, "PackageDoxygen")

    env.Append(DOCDIR='doc')

    def createTargetCallback(registry, packagename, **kw):
        from SConsider import cloneBaseEnv
        doxyEnv = cloneBaseEnv()
        doxyTarget = doxyEnv.PackageDoxygen(registry, packagename)
        doxyEnv.Alias("doxygen", doxyTarget)

    def addBuildTargetCallback(registry, buildTargets, **kw):
        if GetOption("doxygen-only"):
            buildTargets[:] = ["doxygen"]
        else:
            buildTargets.append("doxygen")

    def addBuildAllTargetCallback(registry, **kw):
        from SConsider import cloneBaseEnv
        doxyEnv = cloneBaseEnv()
        doxyTarget = createDoxygenAllTarget(registry)
        doxyEnv.Alias("doxygen", doxyTarget)
        addBuildTargetCallback(registry, **kw)

    if GetOption("doxygen") or GetOption("doxygen-only"):
        from SConsider.Callback import Callback
        compilerDefines.update(determineCompilerDefines(env))
        if not BUILD_TARGETS or 'all' in BUILD_TARGETS:
            Callback().register("PreBuild", addBuildAllTargetCallback)
        else:
            Callback().register("PostCreatePackageTargets", createTargetCallback)
            Callback().register("PreBuild", addBuildTargetCallback)


def exists(env):
    """Make sure doxygen exists."""
    return env.Detect('doxygen')
