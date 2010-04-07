import re, sys, os

direxcludes = ['.build', 'CVS', '.git', '.gitmodules', 'doc']
rePackage = re.compile('^(.*)Lib.py$')
followlinks = False
if sys.version_info[:2] >= (2, 6):
    followlinks = True
for dirpath, dirnames, filenames in os.walk('.', followlinks=followlinks):
    dirnames[:] = [d for d in dirnames if not d in direxcludes]
    for name in filenames:
        rmatch = rePackage.match(name)
        if rmatch:
            path = os.path.abspath(dirpath)

            newname = rmatch.group(1)+'.sconsider'
            newpath = os.path.join(dirpath, newname)

            os.rename(os.path.join(dirpath, name), newpath)
            
            sconscript = os.path.join(path, 'SConscript')
            if os.path.isfile(sconscript):
                os.remove(sconscript)
            else:
                print "No SConscript"
            
            content = ''
            with open(newpath, 'r') as f:
                content += f.read()
            content = re.sub('packagename = SConsider\.getPackageName\(\s*__name__\s*\)', "Import('*')", content)
            with open(newpath, 'w') as f:
                f.write(content)
            
            print newpath
