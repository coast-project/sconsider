import os, SCons, glob, pdb, string

from SCons.Script import Glob, Dir, Import

def FileNodeComparer(left, right):
    """Default implementation for sorting File nodes according to their lexicographical order"""
    return cmp(left.srcnode().abspath, right.srcnode().abspath)

def listFiles(files, **kw):
    allFiles = []
    for file in files:
        globFiles = Glob(file)
        newFiles = []
        for globFile in globFiles:
            if 'recursive' in kw and kw.get('recursive') and os.path.isdir(globFile.srcnode().abspath) and os.path.basename(globFile.srcnode().abspath) != 'CVS':
                allFiles += StanfordUtils.listFiles([str(Dir('.').srcnode().rel_path(globFile.srcnode())) + "/*"], recursive=True)
            if os.path.isfile(globFile.srcnode().abspath):
                allFiles.append(globFile)
    allFiles.sort(cmp=FileNodeComparer)
    return allFiles

def findFiles(directories, filespecs, direxcludes=[]):
    files = []
    for directory in directories:
        for dirpath, dirnames, filenames in os.walk(directory):
            curDir = Dir('.').Dir(dirpath)
            dirnames[:] = [d for d in dirnames if not d in direxcludes]
            addfiles = [curDir.File(f).srcnode() for f in filenames if os.path.splitext(f)[1] in filespecs]
            files.extend(addfiles)
    files.sort(cmp=FileNodeComparer)
    return files

def getPackageName(name):
    return string.replace(name, 'Lib', '')

def getModuleDirName(name):
    return os.path.dirname(name)

def setIncludePath(env, pkgname, includedir, basedir='', internal=True):
    if internal:
        installPath = Dir(includedir)
    else:
        if not basedir:
            basedir = env['BASEOUTDIR'].Dir(os.path.join(env['INCDIR'], pkgname))
        installPath = Dir(basedir).Dir(includedir)

    env.AppendUnique(CPPPATH=[installPath])

class EnvVarDict(dict):
    def __init__(self, _dict=None, uniqueValues=True, **kw):
        self.uniqueValues = uniqueValues
        if not _dict:
            _dict = kw
        dict.__init__(self, _dict)

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, item):
        import types
        if not isinstance(item, types.ListType):
            item = [item]
        if dict.has_key(self, key):
            ditem = dict.get(self, key)
            if not self.uniqueValues or not item[0] in ditem:
                ditem.extend(item)
                dict.setdefault(self, key, ditem)
        else:
            dict.setdefault(self, key, item)

    def __iadd__(self, other):
        self.update(other)
        return self

    def __add__(self, other):
        _dict = self.copy()
        _dict.update(other)
        return _dict

    def __radd__(self, other):
        _dict = self.copy()
        _dict.update(other)
        return _dict

    def copy(self):
        _dict = EnvVarDict()
        _dict.update(self)
        return _dict

    def update(self, _dict):
        for (key, val) in _dict.items():
            self.__setitem__(key, val)

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
