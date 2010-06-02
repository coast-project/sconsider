import os, glob, string, re
import pdb

def FileNodeComparer( left, right ):
    """Default implementation for sorting File nodes according to their lexicographical order"""
    return cmp( left.srcnode().abspath, right.srcnode().abspath )

def listFiles( files, **kw ):
    import SCons, SConsider
    allFiles = []
    for file in files:
        globFiles = SCons.Script.Glob( file )
        newFiles = []
        for globFile in globFiles:
            if 'recursive' in kw and kw.get( 'recursive' ) and os.path.isdir( globFile.srcnode().abspath ) and os.path.basename( globFile.srcnode().abspath ) != 'CVS':
                allFiles += SConsider.listFiles( [str( SCons.Script.Dir( '.' ).srcnode().rel_path( globFile.srcnode() ) ) + "/*"], recursive = True )
            if os.path.isfile( globFile.srcnode().abspath ):
                allFiles.append( globFile )
    allFiles.sort( cmp = FileNodeComparer )
    return allFiles

def removeFiles( files, **kw ):
    import SCons
    if not isinstance( files, list ):
        files = [files]
    for fname in files:
        try:
            os.unlink( SCons.Script.File( fname ).abspath )
        except: pass

def findFiles( directories, extensions = [], matchfiles = [], direxcludes = [] ):
    import SCons
    files = []
    basepathabs=SCons.Script.Dir('.').srcnode().abspath
    for directory in directories:
        directory = SCons.Script.Dir( directory ).srcnode().abspath
        for dirpath, dirnames, filenames in os.walk( directory ):
            curDir = SCons.Script.Dir(os.path.relpath(dirpath,basepathabs))
            dirnames[:] = [d for d in dirnames if not d in direxcludes]
            addfiles = []
            if extensions:
                efiles = [curDir.File( f ) for f in filenames if os.path.splitext( f )[1] in extensions]
                addfiles.extend( efiles )
            if matchfiles:
                mfiles = [curDir.File( f ) for f in filenames if os.path.split( f )[1] in matchfiles]
                addfiles.extend( mfiles )
            if addfiles:
                files.extend( addfiles )
    files.sort( cmp = FileNodeComparer )
    return files

def copyFileNodes( env, nodetuples, destDir, stripRelDirs = [], mode = None ):
    import SCons
    if not SCons.Util.is_List( stripRelDirs ):
        stripRelDirs = [stripRelDirs]

    instTargs = []
    for file, baseDir in nodetuples:
        if isinstance( file, str ):
            file=SCons.Script.File(file)
        installRelPath = baseDir.rel_path( file.get_dir() )

        if stripRelDirs and baseDir.get_abspath() != file.get_dir().get_abspath():
            relPathParts = installRelPath.split( os.sep )
            delprefix = []
            for stripRelDir in stripRelDirs:
                delprefix = os.path.commonprefix( [stripRelDir.split( os.sep ), relPathParts] )
            installRelPath = os.sep.join( relPathParts[len( delprefix ):] )

        instTarg = env.Install( destDir.Dir( installRelPath ), file )
        if mode:
            env.AddPostAction( instTarg, SCons.Defaults.Chmod( str( instTarg[0] ), mode ) )
        instTargs.extend( instTarg )

    return instTargs

def getPyFilename( filename ):
    if ( filename.endswith( ".pyc" ) or filename.endswith( ".pyo" ) ):
        filename = filename[:-1]
    return filename

def multiple_replace(replist, text):
    """ Using a list of tuples (pattern, replacement) replace all occurrences
    of pattern (supports regex) with replacement. Returns the new string."""
    for pattern, replacement in replist:
        text = re.sub(pattern, replacement, text)
    return text

def replaceRegexInFile( fname, searchReplace, multiReplFunc=multiple_replace, replacedCallback=None ):
    try:
        fo = open( fname )
        if fo:
            fstr = fo.read()
            fo.close()
            if fstr:
                strout=multiReplFunc(searchReplace, fstr)
                if fstr != strout:
                    try:
                        of = open(fname, 'w+')
                        of.write(strout)
                        of.close()
                        if callable(replacedCallback): replacedCallback(fname=fname, text=strout)
                        return strout
                    except:
                        pass
    except IOError:
        pass
    return None

def RegexReplace(filematch, baseDir='.', searchReplace=[], excludelist=[], replacedCallback=None ):
    for dirpath, dirnames, filenames in os.walk(baseDir):
        dirnames[:] = [d for d in dirnames if not d in excludelist]
        for name in filenames:
            if filematch(dirpath, name):
                fname = os.path.join(dirpath, name)
                try:
                    replaceRegexInFile( fname, searchReplace, replacedCallback)
                except IOError:
                    pass

# monkey patch os.path to include relpath if python version is < 2.6
if not hasattr(os.path, "relpath"):
    def relpath_posix(path, start):
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

    def relpath_nt(path, start):
        """Return a relative version of a path"""

        if not path:
            raise ValueError("no path specified")

        if path == start:
            return '.'

        start_list = os.path.abspath(start).split(os.sep)
        path_list = os.path.abspath(path).split(os.sep)
        if start_list[0].lower() != path_list[0].lower():
            unc_path, rest = os.path.splitunc(path)
            unc_start, rest = os.path.splitunc(start)
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

        rel_list = [os.pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return curdir
        return join(*rel_list)

    if os.name == 'posix':
        os.path.relpath = relpath_posix
    elif os.name == 'nt':
        os.path.relpath = relpath_nt

def allFuncs(funcs, *args):
    """Returns True if all functions in 'funcs' return True"""
    for f in funcs:
        if not f(*args):
            return False
    return True

def getFlatENV(env):
    import SCons

    if 'ENV' not in env:
        env = Environment(ENV = env)

    # Ensure that the ENV values are all strings:
    newENV = {}
    for key, value in env['ENV'].items():
        if SCons.Util.is_List(value):
            # If the value is a list, then we assume it is a path list,
            # because that's a pretty common list-like value to stick
            # in an environment variable:
            value = SCons.Util.flatten_sequence(value)
            newENV[key] = string.join(map(str, value), os.pathsep)
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
