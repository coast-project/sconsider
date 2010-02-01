import os, glob, string, re
import pdb

def FileNodeComparer( left, right ):
    """Default implementation for sorting File nodes according to their lexicographical order"""
    return cmp( left.srcnode().abspath, right.srcnode().abspath )

def listFiles( files, **kw ):
    import SCons
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
    import types
    if not isinstance( files, types.ListType ):
        files = [files]
    for fname in files:
        try:
            os.unlink( SCons.Script.File( fname ).abspath )
        except: pass

def findFiles( directories, extensions = [], matchfiles = [], direxcludes = [] ):
    import SCons
    files = []
    for directory in directories:
        directory = SCons.Script.Dir( directory ).srcnode().abspath
        for dirpath, dirnames, filenames in os.walk( directory ):
            curDir = SCons.Script.Dir( dirpath )
            dirnames[:] = [d for d in dirnames if not d in direxcludes]
            addfiles = []
            if extensions:
                efiles = [curDir.File( f ).srcnode() for f in filenames if os.path.splitext( f )[1] in extensions]
                addfiles.extend( efiles )
            if matchfiles:
                mfiles = [curDir.File( f ).srcnode() for f in filenames if os.path.split( f )[1] in matchfiles]
                addfiles.extend( mfiles )
            if addfiles:
                files.extend( addfiles )
    files.sort( cmp = FileNodeComparer )
    return files

def getPackageName( name ):
    return string.replace( name, 'Lib', '' )

def getModuleDirName( name ):
    return os.path.dirname( name )

class EnvVarDict( dict ):
    def __init__( self, _dict = None, uniqueValues = True, **kw ):
        self.uniqueValues = uniqueValues
        if not _dict:
            _dict = kw
        dict.__init__( self, _dict )

    def __getitem__( self, key ):
        return dict.__getitem__( self, key )

    def __setitem__( self, key, item ):
        import types
        if not isinstance( item, types.ListType ):
            item = [item]
        if dict.has_key( self, key ):
            ditem = dict.get( self, key )
            if not self.uniqueValues or not item[0] in ditem:
                ditem.extend( item )
                dict.setdefault( self, key, ditem )
        else:
            dict.setdefault( self, key, item )

    def __iadd__( self, other ):
        self.update( other )
        return self

    def __add__( self, other ):
        _dict = self.copy()
        _dict.update( other )
        return _dict

    def __radd__( self, other ):
        _dict = self.copy()
        _dict.update( other )
        return _dict

    def copy( self ):
        _dict = EnvVarDict()
        _dict.update( self )
        return _dict

    def update( self, _dict ):
        for ( key, val ) in _dict.items():
            self.__setitem__( key, val )

#def TestFunc():
#    pdb.set_trace()
#    _envFlags = EnvVarDict({ 'CPPDEFINES' : 'fooX' })
#    print _envFlags
#    _envFlags += EnvVarDict(CPPDEFINES=['blabla' + '_IMPL'])
#    print _envFlags
#    _envFlags += EnvVarDict(CPPDEFINES=['blabla' + '_IMPL'])
#    print _envFlags
#
#TestFunc()

def copyFileNodes( env, nodetuples, destDir, stripRelDirs = [], mode = None ):
    import SCons
    if not SCons.Util.is_List( stripRelDirs ):
        stripRelDirs = [stripRelDirs]

    instTargs = []
    for file, baseDir in nodetuples:
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

def DoReplaceInString(fstr, strRegex, replaceWith):
    lastiter = None
    strout = ''
    for it in re.finditer(strRegex, fstr, re.M):
        if lastiter:
            strout += it.string[lastiter.end(0):it.start(0)]
        else:
            strout += it.string[:it.start(0)]
        g = it.groups()
        if callable(replaceWith):
            strout += replaceWith(g, it)
        else:
            strout += replaceWith
        lastiter = it
    if lastiter:
        strout += lastiter.string[lastiter.end(0):]
        if fstr != strout:
            return strout
    return None

def replaceRegexInFile( fname, searchReplace ):
    try:
        fo = open( fname )
        if fo:
            fstr = fo.read()
            fo.close()
            if fstr:
                for reStr, replX in searchReplace:
                    strout = DoReplaceInString(fstr, reStr, replX)
                    if strout:
                        # prepare for potential next loop
                        fstr=strout
                if strout:
                    try:
                        of = open(fname, 'w+')
                        of.write(strout)
                        of.close()
                    except:
                        pass
    except IOError:
        pass

def RegexReplace(filematch, baseDir='.', searchReplace=[], excludelist=[] ):
    for dirpath, dirnames, filenames in os.walk(baseDir):
        dirnames[:] = [d for d in dirnames if not d in excludelist]
        for name in filenames:
            if filematch(dirpath, name):
                fname = os.path.join(dirpath, name)
                try:
                    replaceRegexInFile( fname, searchReplace )
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
