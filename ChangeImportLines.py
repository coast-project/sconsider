import os, pdb, re

excludelist = ['build', 'CVS', 'data', 'xml', 'doc', 'bin', 'lib', '.git', '.gitmodules']
list2 = []
excludelist.extend(list2)

def ChangeToDependsOn():
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if not d in excludelist]
        for name in filenames:
            if re.compile('^.*Lib\.py$').match(name) or re.compile('^SConscript$').match(name):
                fname = os.path.join(dirpath, name)
                try:
                    fo = open(fname)
                    if fo:
                        fstr = fo.read()
                        fo.close()
                        strout = ''
                        lastiter = None
                        for it in re.finditer(r"(\w*[Ee]nv)(\.Tool\()([\w_]+|'\w+)(\s*\+?\s*'?Lib')([,\s\w=]+)?(\).*)$", fstr, re.M):
                            if lastiter:
                                strout += it.string[lastiter.end(0):it.start(0)]
                            else:
                                strout += it.string[:it.start(0)]
                            g = it.groups()
                            envName = g[0]
                            lname = g[2]
                            if lname.startswith("'"):
                                lname += "'"
                            params = ''
                            if g[4]:
                                params = g[4]
                            strout += "StanfordUtils.DependsOn(" + envName + ", " + lname + params + ")"
                            lastiter = it
                        if lastiter:
                            outstr = strout
                            outstr += lastiter.string[lastiter.end(0):]
                            if fstr != outstr:
                                print "matches in file:", fname
                                try:
                                    of = open(fname, 'w+')
                                    of.write(outstr)
                                    of.close()
                                except:
                                    pass
                except IOError:
                    pass

def RemoveEnvDump():
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if not d in excludelist]
        for name in filenames:
            if re.compile('^SConscript$').match(name):
                fname = os.path.join(dirpath, name)
                try:
                    fo = open(fname)
                    if fo:
                        fstr = fo.read()
                        fo.close()
                        strout = ''
                        lastiter = None
                        for it in re.finditer(r"^#print\s+(\w*[Ee]nv)\.Dump\(\)\s*$\n", fstr, re.M):
                            if lastiter:
                                strout += it.string[lastiter.end(0):it.start(0)]
                            else:
                                strout += it.string[:it.start(0)]
                            g = it.groups()
                            envName = g[0]
                            lastiter = it
                        if lastiter:
                            outstr = strout
                            outstr += lastiter.string[lastiter.end(0):]
                            if fstr != outstr:
                                print "matches in file:", fname
                                try:
                                    of = open(fname, 'w+')
                                    of.write(outstr)
                                    of.close()
                                except:
                                    pass
                except IOError:
                    pass

def ChangeBaseEnvClone():
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if not d in excludelist]
        for name in filenames:
            if re.compile('^SConscript$').match(name):
                fname = os.path.join(dirpath, name)
                try:
                    fo = open(fname)
                    if fo:
                        fstr = fo.read()
                        fo.close()
                        strout = ''
                        lastiter = None
                        for it in re.finditer(r"(baseEnv)\.Clone\(\)", fstr, re.M):
                            if lastiter:
                                strout += it.string[lastiter.end(0):it.start(0)]
                            else:
                                strout += it.string[:it.start(0)]
                            g = it.groups()
                            envName = g[0]
                            strout += "StanfordUtils.CloneBaseEnv()"
                            lastiter = it
                        if lastiter:
                            outstr = strout
                            outstr += lastiter.string[lastiter.end(0):]
                            if fstr != outstr:
                                print "matches in file:", fname
                                try:
                                    of = open(fname, 'w+')
                                    of.write(outstr)
                                    of.close()
                                except:
                                    pass
                except IOError:
                    pass

def ChangeListFiles():
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if not d in excludelist]
        for name in filenames:
            if re.compile('^.*Lib\.py$').match(name) or re.compile('^SConscript$').match(name):
                fname = os.path.join(dirpath, name)
                try:
                    fo = open(fname)
                    if fo:
                        fstr = fo.read()
                        fo.close()
                        strout = ''
                        lastiter = None
                        for it in re.finditer(r"([^.])(listFiles)", fstr, re.M):
                            if lastiter:
                                strout += it.string[lastiter.end(0):it.start(0)]
                            else:
                                strout += it.string[:it.start(0)]
                            g = it.groups()
                            envName = g[0]
                            strout += envName + "StanfordUtils.listFiles"
                            lastiter = it
                        if lastiter:
                            outstr = strout
                            outstr += lastiter.string[lastiter.end(0):]
                            if fstr != outstr:
                                print "matches in file:", fname
                                try:
                                    of = open(fname, 'w+')
                                    of.write(outstr)
                                    of.close()
                                except:
                                    pass
                except IOError:
                    pass

def ChangePackageName():
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if not d in excludelist]
        for name in filenames:
            if re.compile('^.*Lib\.py$').match(name):
                fname = os.path.join(dirpath, name)
                try:
                    fo = open(fname)
                    if fo:
                        fstr = fo.read()
                        fo.close()
                        strout = ''
                        lastiter = None
                        for it in re.finditer(r"string.replace\(([\w_]+),\s*'Lib',\s*''\)", fstr, re.M):
                            if lastiter:
                                strout += it.string[lastiter.end(0):it.start(0)]
                            else:
                                strout += it.string[:it.start(0)]
                            g = it.groups()
                            envName = g[0]
                            strout += "StanfordUtils.getPackageName(" + envName + ")"
                            lastiter = it
                        if lastiter:
                            outstr = strout
                            outstr += lastiter.string[lastiter.end(0):]
                            if fstr != outstr:
                                print "matches in file:", fname
                                try:
                                    of = open(fname, 'w+')
                                    of.write(outstr)
                                    of.close()
                                except:
                                    pass
                except IOError:
                    pass

def ChangePackageName():
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if not d in excludelist]
        for name in filenames:
            if re.compile('^.*Lib\.py$').match(name):
                fname = os.path.join(dirpath, name)
                try:
                    fo = open(fname)
                    if fo:
                        fstr = fo.read()
                        fo.close()
                        strout = ''
                        lastiter = None
                        for it in re.finditer(r"(libDepends)", fstr, re.M):
                            if lastiter:
                                strout += it.string[lastiter.end(0):it.start(0)]
                            else:
                                strout += it.string[:it.start(0)]
                            g = it.groups()
                            envName = g[0]
                            strout += "linkDependencies"
                            lastiter = it
                        if lastiter:
                            outstr = strout
                            outstr += lastiter.string[lastiter.end(0):]
                            if fstr != outstr:
                                print "matches in file:", fname
                                try:
                                    of = open(fname, 'w+')
                                    of.write(outstr)
                                    of.close()
                                except:
                                    pass
                except IOError:
                    pass

ChangePackageName()
#ChangeToDependsOn()
#ChangeBaseEnvClone()
#RemoveEnvDump()
#ChangeListFiles()
#ChangePackageName()
