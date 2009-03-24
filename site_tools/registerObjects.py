import os, pprint
import SCons.Node.FS

def generate(env, **kw):
    if kw.get('package', '') != '':
        if os.path.exists(os.path.join(str(env.Dir('.').srcnode()),kw.get('package')+"Lib.py")):
            tools = env.Install(env['TOOLDIR'], os.path.join(str(env.Dir('.').srcnode()),kw.get('package')+"Lib.py"))
            env.Default(tools)
            env.Alias('all', tools)
        if kw.get('libraries', '') != '':
            libraries = env.Install(env['LIBDIR'], kw.get('libraries'))
            env.Alias(kw.get('package'), libraries)
            env.Default(libraries)
            env.Alias('libraries', libraries)
            env.Alias('all', libraries)
        if kw.get('binaries', '') != '':
            binaries = env.Install(env['BINDIR'], kw.get('binaries'))
            wrappers = env.GenerateWrapperScript(binaries)
            env.Depends(wrappers, binaries)
            env.Alias(kw.get('package'), wrappers)
            env.Default(wrappers)
            env.Alias('binaries', wrappers)
            env.Alias('all', wrappers)
        if kw.get('includes', '') != '':
            for header in kw.get('includes'):
                header = env.File(str(header))
                splitFile = str(env.Dir('.').srcnode().rel_path(header.srcnode()))
                installPath = ''
                while os.path.split(splitFile)[0] != '':
                    parts = os.path.split(splitFile)
                    splitFile = parts[0]
                    installPath = os.path.normpath(os.path.join(parts[1], installPath))
                installPath = os.path.dirname(installPath)
                includes = env.Install(env['INCDIR'].Dir(kw.get('package')).Dir(installPath), header)
                env.Alias(kw.get('package'), includes)
                env.Default(includes)
                env.Alias('all', includes)
        if kw.get('testApps', '') != '':
            testApps = env.Install(env['TESTDIR'], kw.get('testApps'))
            wrappers = env.GenerateWrapperScript(testApps)
            env.Depends(wrappers, testApps)
            env.Alias(kw.get('package'), wrappers)
            env.Alias('test', wrappers)
            env.Alias('all', wrappers)
            env.Clean('test', wrappers)
        if kw.get('pfiles', '') != '':
            pfiles = env.Install(env['PFILESDIR'], kw.get('pfiles'))
            env.AppendUnique(PFILES = pfiles)
            env.Alias(kw.get('package'), pfiles)
            env.Default(pfiles)
            env.Alias('all', pfiles)
        if kw.get('data', '') != '':
            for file in kw.get('data'):
                file = env.File(str(file))
                splitFile = str(env.Dir('.').srcnode().rel_path(file.srcnode()))
                installPath = ''
                while os.path.split(splitFile)[0] != '':
                    parts = os.path.split(splitFile)
                    splitFile = parts[0]
                    installPath = os.path.normpath(os.path.join(parts[1], installPath))
                installPath = os.path.dirname(installPath)
                data = env.Install(env['DATADIR'].Dir(kw.get('package')).Dir(installPath), file)
                env.Alias(kw.get('package'), data)
                env.Default(data)
                env.Alias('all', data)
        if kw.get('xml', '') != '':
            for file in kw.get('xml'):
                file = env.File(str(file))
                splitFile = str(env.Dir('.').srcnode().rel_path(file.srcnode()))
                installPath = ''
                while os.path.split(splitFile)[0] != '':
                    parts = os.path.split(splitFile)
                    splitFile = parts[0]
                    installPath = os.path.normpath(os.path.join(parts[1], installPath))
                installPath = os.path.dirname(installPath)
                xml = env.Install(env['XMLDIR'].Dir(kw.get('package')).Dir(installPath), file)
                env.Alias(kw.get('package'), xml)
                env.Default(xml)
                env.Alias('all', xml)
        if kw.get('python', '') != '':
            python = env.Install(env['PYTHONDIR'], kw.get('python'))
            env.Alias(kw.get('package'), python)
            env.Default(python)
            env.Alias('all', python)
        if 'wrapper_env' in kw:
            # user has passed in a list of (exename, envdict) tuples
            # to be registered in the construction environment and eventually
            # emitted into the wrapper scripts
            print 'registerObjects: registering env dicts for %s' % list(x[0] for x in kw.get('wrapper_env'))
            env.Append( WRAPPER_ENV = kw.get('wrapper_env') )
                                        
def exists(env):
    return 1;
