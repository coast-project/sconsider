import os,SCons,glob,pdb

from SCons.Script import Glob

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
