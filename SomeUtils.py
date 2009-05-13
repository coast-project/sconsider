import os,SCons,glob,pdb

from SCons.Script import Glob, Dir

def listFiles(files, **kw):
    allFiles = []
    for file in files:
        globFiles = Glob(file)
        newFiles = []
        for globFile in globFiles:
            if 'recursive' in kw and kw.get('recursive') and os.path.isdir(globFile.srcnode().abspath) and os.path.basename(globFile.srcnode().abspath) != 'CVS':
                allFiles+=listFiles([str(Dir('.').srcnode().rel_path(globFile.srcnode()))+"/*"], recursive = True)
            if os.path.isfile(globFile.srcnode().abspath):
                allFiles.append(globFile)
    return allFiles

def findFiles(directories, filespecs, direxcludes=[]):
    files = []
    for directory in directories:
        for dirpath, dirnames, filenames in os.walk(directory):
            curDir=Dir('.').Dir(dirpath)
            dirnames[:] = [d for d in dirnames if not d in direxcludes]
            addfiles = [curDir.File(f).srcnode() for f in filenames if os.path.splitext(f)[1] in filespecs]
            files.extend(addfiles)
    return files
