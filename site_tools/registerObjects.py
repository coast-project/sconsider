import os, pprint
import SCons.Node.FS

## * Install various specified objects (includes, libraries, etc.) and
##   xxLib.py
## * Add to the list of default targets and to definition of 'all'
## * Generate wrappers for programs
## Recognized keywords are
##        package - string
##        libraries - list of library nodes
##        testApps  - list of program nodes
##        binaries  - list of program nodes
##        includes - list of file paths
##        data     - list of file paths
##        xml      - list of file paths
##        pfiles
##        python
##        wrapper_env
##

def generate(env, **kw):
    if kw.get('package', '') != '':
        if kw.get('libraries', '') != '':
            libraries = env.Install(env['LIBDIR'], kw.get('libraries'))
            env.Alias(kw.get('package'), libraries)
            env.Default(libraries)
            env.Alias('libraries', libraries)
            env.Alias('all', libraries)
        if kw.get('binaries', '') != '':
            binaries = env.Install(env['BINDIR'], kw.get('binaries'))
            env.Tool('generateScript')
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
            env.Tool('generateScript')
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
            env.Append( WRAPPER_ENV = kw.get('wrapper_env') )

def exists(env):
    return 1;
