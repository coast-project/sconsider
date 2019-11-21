"""SConsider.SomeUtils.

Collection of helper functions
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

import os
import re
from logging import getLogger
from SConsider.PopenHelper import ProcessRunner, CalledProcessError, TimeoutExpired
logger = getLogger(__name__)


def FileNodeComparer(left, right):
    """Default implementation for sorting File nodes according to their
    lexicographical order."""
    return cmp(left.srcnode().get_abspath(), right.srcnode().get_abspath())


def listFiles(files, **kw):
    import SCons

    allFiles = []
    for file_pattern in files:
        globFiles = SCons.Script.Glob(file_pattern)
        for globFile in globFiles:
            if kw.get('recursive', False) and isinstance(globFile, SCons.Node.FS.Dir):
                allFiles += listFiles(
                    [str(SCons.Script.Dir('.').srcnode().rel_path(globFile.srcnode())) + "/*"],
                    recursive=True)
            else:
                allFiles.append(globFile)
    allFiles.sort(cmp=FileNodeComparer)
    return allFiles


def removeFiles(files, **kw):
    import SCons
    if not isinstance(files, list):
        files = [files]
    for fname in files:
        try:
            os.unlink(SCons.Script.File(fname).get_abspath())
        except:
            pass


def findFiles(directories, extensions=None, matchfiles=None, direxcludes=None):
    import SCons
    files = []
    if direxcludes is None:
        direxcludes = []
    baseDir = SCons.Script.Dir('.').srcnode()
    basepathabs = baseDir.get_abspath()
    for directory in directories:
        directory = baseDir.Dir(directory).get_abspath()
        for dirpath, dirnames, filenames in os.walk(directory):
            try:
                # the following call fails if the relative directory evaluates
                # to a target...
                curDir = baseDir.Dir(os.path.relpath(dirpath, basepathabs))
                dirnames[:] = [d for d in dirnames if d not in direxcludes]
                addfiles = []
                if extensions:
                    efiles = [curDir.File(f) for f in filenames if os.path.splitext(f)[1] in extensions]
                    addfiles.extend(efiles)
                if matchfiles:
                    mfiles = [curDir.File(f) for f in filenames if os.path.split(f)[1] in matchfiles]
                    addfiles.extend(mfiles)
                if addfiles:
                    files.extend(addfiles)
            except:
                pass
    files.sort(cmp=FileNodeComparer)
    return files


def copyFileNodes(env, nodetuples, destDir, stripRelDirs=None, mode=None, replaceDict=None):
    import SCons
    if stripRelDirs is None:
        stripRelDirs = []
    if not SCons.Util.is_List(stripRelDirs):
        stripRelDirs = [stripRelDirs]

    instTargs = []
    for filename, baseDir in nodetuples:
        if isinstance(filename, str):
            filename = SCons.Script.File(filename)
        installRelPath = baseDir.rel_path(filename.get_dir())

        if stripRelDirs and baseDir.get_abspath() != filename.get_dir().get_abspath():
            relPathParts = installRelPath.split(os.sep)
            delprefix = []
            for stripRelDir in stripRelDirs:
                delprefix = os.path.commonprefix([stripRelDir.split(os.sep), relPathParts])
            installRelPath = os.sep.join(relPathParts[len(delprefix):])

        if replaceDict:
            instTarg = env.SubstInFileBuilder(destDir.Dir(installRelPath), filename, SUBST_DICT=replaceDict)
        else:
            install_path = env.makeInstallablePathFromDir(destDir.Dir(installRelPath))
            instTarg = env.Install(dir=install_path, source=filename)

        if mode:
            env.AddPostAction(instTarg, SCons.Defaults.Chmod(str(instTarg[0]), mode))
        instTargs.extend(instTarg)

    return instTargs


def getPyFilename(filename):
    if filename.endswith(".pyc") or filename.endswith(".pyo"):
        filename = filename[:-1]
    return filename


def multiple_replace(replist, text):
    """Using a list of tuples (pattern, replacement) replace all occurrences of
    pattern (supports regex) with replacement.

    Returns the new string.
    """
    if replist is None:
        replist = []
    for pattern, replacement in replist:
        if not pattern or not text:
            continue
        text = re.sub(pattern, replacement, text)
    return text


def replaceRegexInFile(fname, searchReplace, multiReplFunc=multiple_replace, replacedCallback=None):
    try:
        fo = open(fname)
        if fo:
            fstr = fo.read()
            fo.close()
            if fstr:
                strout = multiReplFunc(searchReplace, fstr)
                if fstr != strout:
                    try:
                        of = open(fname, 'w+')
                        of.write(strout)
                        of.close()
                        if callable(replacedCallback):
                            replacedCallback(fname=fname, text=strout)
                        return strout
                    except:
                        pass
    except IOError:
        pass
    return None


def RegexReplace(filematch, baseDir='.', searchReplace=None, excludelist=None, replacedCallback=None):
    if excludelist is None:
        excludelist = []
    for dirpath, dirnames, filenames in os.walk(baseDir):
        dirnames[:] = [d for d in dirnames if d not in excludelist]
        for name in filenames:
            if filematch(dirpath, name):
                fname = os.path.join(dirpath, name)
                try:
                    replaceRegexInFile(fname, searchReplace, replacedCallback)
                except IOError:
                    pass


# monkey patch os.path to include relpath if python version is < 2.6
if not hasattr(os.path, "relpath"):

    def relpath_posix(path, start):
        """Return a relative version of a path."""

        if not path:
            raise ValueError('no path specified')

        if path == start:
            return '.'

        start_list = (os.path.abspath(start)).split(os.sep)
        path_list = (os.path.abspath(path)).split(os.sep)

        # Work out how much of the filepath is shared by start and path.
        i = len(os.path.commonprefix([start_list, path_list]))

        rel_list = [os.pardir] * (len(start_list) - i) + path_list[i:]
        return os.path.join(*rel_list)

    def relpath_nt(path, start):
        """Return a relative version of a path."""

        if not path:
            raise ValueError("no path specified")

        if path == start:
            return '.'

        start_list = os.path.abspath(start).split(os.sep)
        path_list = os.path.abspath(path).split(os.sep)
        if start_list[0].lower() != path_list[0].lower():
            unc_path, _ = os.path.splitunc(path)
            unc_start, _ = os.path.splitunc(start)
            if bool(unc_path) ^ bool(unc_start):
                raise ValueError("Cannot mix UNC and non-UNC paths (%s and %s)" % (path, start))
            else:
                raise ValueError("path is on drive %s, start on drive %s" % (path_list[0], start_list[0]))

        # Work out how much of the filepath is shared by start and path.
        for i in range(min(len(start_list), len(path_list))):
            if start_list[i].lower() != path_list[i].lower():
                break
            else:
                i += 1

        rel_list = [os.pardir] * (len(start_list) - i) + path_list[i:]
        if not rel_list:
            return os.path.curdir
        return os.path.join(*rel_list)

    if os.name == 'posix':
        os.path.relpath = relpath_posix
    elif os.name == 'nt':
        os.path.relpath = relpath_nt


def allFuncs(funcs, *args):
    """Returns True if all functions in 'funcs' return True."""
    for f in funcs:
        if callable(f) and not f(*args):
            return False
    return True


def getFlatENV(env):
    import SCons

    if 'ENV' not in env:
        env = SCons.Environment(ENV=env)

    # Ensure that the ENV values are all strings:
    newENV = {}
    for key, value in env['ENV'].items():
        if SCons.Util.is_List(value):
            # If the value is a list, then we assume it is a path list,
            # because that's a pretty common list-like value to stick
            # in an environment variable:
            value = SCons.Util.flatten_sequence(value)
            newENV[key] = os.path.join(*[str(j) for j in value])
        else:
            # It's either a string or something else.  If it's a string,
            # we still want to call str() because it might be a *Unicode*
            # string, which makes subprocess.Popen() gag.  If it isn't a
            # string or a list, then we just coerce it to a string, which
            # is the proper way to handle Dir and File instances and will
            # produce something reasonable for just about everything else:
            newENV[key] = str(value)

        newENV[key] = env.subst(newENV[key])

    return newENV


def isFileNode(node):
    """No path means it is not a file."""
    return hasattr(node, 'path')


def isDerivedNode(node):
    """Returns True if this node is built."""
    return node.is_derived()


def hasPathPart(node, pathpart):
    """Checks if node's path has a given part."""
    regex = '(^' + re.escape(pathpart + os.sep) + ')'
    regex += '|(.*' + re.escape(os.sep + pathpart + os.sep) + ')'
    regex += '|(.*' + re.escape(os.sep + pathpart) + '$)'
    match = re.match(regex, node.path)
    return match is not None


def getNodeDependencies(target, filters=None):
    """Determines the recursive dependencies of a node.

    Specify node filters using 'filters'.
    """
    if filters is None:
        filters = []
    if not isinstance(filters, list):
        filters = [filters]

    deps = set()
    prerequisites = target.prerequisites
    if prerequisites is None:
        prerequisites = []
    sources = target.sources
    if sources is None:
        sources = []
    depends = target.depends
    if depends is None:
        depends = []
    for t in sources + depends + prerequisites:
        if allFuncs(filters, t):
            executor = t.get_executor()
            if executor is not None:
                deps.update(executor.get_all_targets())
        deps.update(getNodeDependencies(t, filters))

    return deps


def getfqdn():
    import socket
    hostname = socket.gethostname().lower()
    fqdn = socket.getfqdn().lower()
    domain = '.'.join(fqdn.split('.')[1:])
    return (hostname, domain, fqdn)


def runCommand(args, logpath='', filename=None, stdincontent=None, timeout=120.0, **kw):
    if filename:
        with open(filename) as f:
            stdincontent = f.read()

    filter_func = None
    for k in ['filter_func', 'filter']:
        try:
            filter_func = kw.pop(k)
            break
        except KeyError:
            pass
    if callable(filter_func):
        stdincontent = filter_func(stdincontent)

    if not os.path.isdir(logpath):
        os.makedirs(logpath)
    logfilebasename = ''
    if kw.get('shell', False):
        logfilebasename = 'shell.'
    if isinstance(args, str):
        # split args as it might contain newlines if it is a shell command
        logfilebasename += os.path.basename(args.split()[0])
    else:
        logfilebasename += os.path.basename(args[0])
    if filename:
        logfilebasename = logfilebasename + '.' + os.path.basename(filename)
    errfilename = os.path.join(logpath, logfilebasename + '.stderr')
    outfilename = os.path.join(logpath, logfilebasename + '.stdout')

    executor = None
    try:
        errfile = open(errfilename, 'w')
        outfile = open(outfilename, 'w')
        kw.setdefault('seconds_to_wait', 0.1)
        with ProcessRunner(args, timeout=timeout, stdin_handle=stdincontent, **kw) as executor:
            for out, err in executor:
                outfile.write(out)
                errfile.write(err)
    except CalledProcessError as e:
        logger.debug("non-zero exitcode: %s", e)
    except TimeoutExpired as e:
        logger.debug(e)
    except OSError as e:
        logger.debug("executable error: %s", e)
        # follow shell exit code
        exitcode = 127
    except Exception as e:
        logger.debug("process creation failure: %s", e)
        print >> errfile, e
    finally:
        if executor:
            exitcode = executor.returncode
        errfile.close()
        outfile.close()
    return exitcode


def getLibCVersion(bits='32'):
    import platform
    libcnames = []
    for directory in ['/lib' + bits, '/lib', '/lib32', '/lib64']:
        for dirpath, _, filenames in os.walk(directory):
            filenames[:] = [f for f in filenames if f == 'libc.so.6']
            for f in filenames:
                libcnames.append(os.path.join(dirpath, f))
    libcver = ('dummy', '0.0')
    for libcn in libcnames:
        try:
            libcver = platform.libc_ver(executable=libcn)
            break
        except:
            continue
    return libcver
