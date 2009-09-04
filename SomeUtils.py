import os, SCons, glob, pdb, string, re

from SCons.Script import Glob, Dir, Import, File

def FileNodeComparer( left, right ):
    """Default implementation for sorting File nodes according to their lexicographical order"""
    return cmp( left.srcnode().abspath, right.srcnode().abspath )

def listFiles( files, **kw ):
    allFiles = []
    for file in files:
        globFiles = Glob( file )
        newFiles = []
        for globFile in globFiles:
            if 'recursive' in kw and kw.get( 'recursive' ) and os.path.isdir( globFile.srcnode().abspath ) and os.path.basename( globFile.srcnode().abspath ) != 'CVS':
                allFiles += StanfordUtils.listFiles( [str( Dir( '.' ).srcnode().rel_path( globFile.srcnode() ) ) + "/*"], recursive = True )
            if os.path.isfile( globFile.srcnode().abspath ):
                allFiles.append( globFile )
    allFiles.sort( cmp = FileNodeComparer )
    return allFiles

def removeFiles( files, **kw ):
    import types
    if not isinstance( files, types.ListType ):
        files = [files]
    for fname in files:
        try:
            os.unlink( File( fname ).abspath )
        except: pass

def findFiles( directories, extensions = [], matchfiles = [], direxcludes = [] ):
    files = []
    for directory in directories:
        directory = Dir( directory ).srcnode().abspath
        for dirpath, dirnames, filenames in os.walk( directory ):
            curDir = Dir( dirpath )
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

def copyFileNodes( env, nodes, destDir, baseDir = None, stripRelDirs = [], mode = None, packagename = None, checkEnvCfg = False ):
    if not baseDir:
        baseDir = env.Dir( '.' )
    if hasattr( baseDir, 'srcnode' ):
        baseDir = baseDir.srcnode()

    if not SCons.Util.is_List( stripRelDirs ):
        stripRelDirs = [stripRelDirs]

    instTargs = []
    for node in nodes:
        file = node
        if hasattr( node, 'srcnode' ):
            file = node.srcnode()

        installRelPath = baseDir.rel_path( file.get_dir() )

        if stripRelDirs and baseDir.get_abspath() != file.get_dir().get_abspath():
            relPathParts = installRelPath.split( os.sep )
            delprefix = []
            for stripRelDir in stripRelDirs:
                delprefix = os.path.commonprefix( [stripRelDir.split( os.sep ), relPathParts] )
            installRelPath = os.sep.join( relPathParts[len( delprefix ):] )

        if checkEnvCfg:
            # based on installRelPath and file, try to find an override file to use instead
            fileWithRelpathToSearch = os.path.relpath( file.abspath, baseDir.abspath )
            #print "checking for cfgfile",fileWithRelpathToSearch
            envconfigdir = env.get( '__envconfigdir__', None )
            # catch possible errors and stop when wanting to do realtive movements
            if envconfigdir and not fileWithRelpathToSearch.startswith('..'):
                envcfgdir = envconfigdir.Dir( packagename ).abspath
                fileToCheckFor = os.path.join( envcfgdir, fileWithRelpathToSearch )
                if os.path.isfile( fileToCheckFor ):
                    #print "found override file",fileToCheckFor
                    file = File( fileToCheckFor )

        instTarg = env.Install( destDir.Dir( installRelPath ), file )
        if mode:
            env.AddPostAction( instTarg, SCons.Defaults.Chmod( str( instTarg[0] ), mode ) )
        instTargs.extend( instTarg )

    return instTargs

def getPyFilename( filename ):
    if ( filename.endswith( ".pyc" ) or filename.endswith( ".pyo" ) ):
        filename = filename[:-1]
    return filename

def replaceRegexInFile( fname, searchpattern, replacepatternorfunc ):
    try:
        fo = open( fname )
        if fo:
            fstr = fo.read()
            fo.close()
            strout = ''
            lastiter = None
            for it in re.finditer( searchpattern, fstr, re.M ):
                if lastiter:
                    strout += it.string[lastiter.end( 0 ):it.start( 0 )]
                else:
                    strout += it.string[:it.start( 0 )]
                g = it.groups()
                if callable( replacepatternorfunc ):
                    strout += replacepatternorfunc( g )
                else:
                    strout += replacepatternorfunc
                lastiter = it
            if lastiter:
                outstr = strout
                outstr += lastiter.string[lastiter.end( 0 ):]
                if fstr != outstr:
                    print "replaced in", fname
                    try:
                        of = open( fname, 'w+' )
                        of.write( outstr )
                        of.close()
                    except:
                        pass
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
