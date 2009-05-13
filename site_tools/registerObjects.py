import os, pprint, pdb
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

def copyFileNodes(env, nodename, baseoutdir, destdir, useFirstSegment=False, **kw):
    nodes = kw.get(nodename)
    instTargs = []
    baseOutPath = SCons.Script.Dir('')
    if nodename == 'includes':
        baseOutPath = baseoutdir.Dir(os.path.join(env[destdir], kw.get('package')))
    elif nodename == 'config':
        baseOutPath = baseoutdir.Dir(kw.get('package'))
    else:
        baseOutPath = baseoutdir.Dir(os.path.join(kw.get('package'), env[destdir]))
    for file in nodes:
        splitFile = str(env.Dir('.').srcnode().rel_path(file.srcnode()))
        installPath = ''
        while os.path.split(splitFile)[0] != '':
            parts = os.path.split(splitFile)
            splitFile = parts[0]
            installPath = os.path.normpath(os.path.join(parts[1], installPath))
        installPath = os.path.dirname(installPath)
        if useFirstSegment:
            installPath = os.path.join(splitFile, installPath)
        instTargs.extend(env.Install(baseOutPath.Dir(installPath), file))
    env.Alias(kw.get('package'), instTargs)
    env.Default(instTargs)
    env.Alias('all', instTargs)
    return 0

def generate(env, useFirstSegment=False, **kw):
    pkgname = kw.get('package', '')
    if pkgname != '':
        env['PackageName'] = pkgname
        baseoutdir = env['BASEOUTDIR']
        basereldir = ''
        if kw.get('testApps', '') != '':
            basereldir = 'tests'
        if kw.get('binaries', '') != '':
            basereldir = 'apps'
        env['TargetType'] = basereldir
        baseoutdir = baseoutdir.Dir(basereldir)
        if kw.get('libraries', '') != '':
            libraries = env.Install(baseoutdir.Dir(env['LIBDIR']), kw.get('libraries'))
            env.Alias(pkgname, libraries)
            env.Default(libraries)
            env.Alias('libraries', libraries)
            env.Alias('all', libraries)
        if kw.get('config', '') != '':
            copyFileNodes(env, 'config', baseoutdir, 'CONFIGDIR', useFirstSegment=True, **kw)
        if kw.get('data', '') != '':
            copyFileNodes(env, 'data', baseoutdir, 'DATADIR', useFirstSegment, **kw)
        if kw.get('xml', '') != '':
            copyFileNodes(env, 'xml', baseoutdir, 'XMLDIR', useFirstSegment, **kw)
        if kw.get('includes', '') != '':
            copyFileNodes(env, 'includes', baseoutdir, 'INCDIR', useFirstSegment, **kw)
        if kw.get('binaries', '') != '':
            binaries = env.Install(baseoutdir.Dir(pkgname).Dir(env['BINDIR']), kw.get('binaries'))
            env.Tool('generateScript')
            wrappers = env.GenerateWrapperScript(binaries)
            env.Depends(wrappers, binaries)
            env.Alias(pkgname, wrappers)
            env.Default(wrappers)
            env.Alias('binaries', wrappers)
            env.Alias('all', wrappers)
        if kw.get('testApps', '') != '':
            testApps = env.Install(baseoutdir.Dir(pkgname).Dir(env['TESTDIR']), kw.get('testApps'))
            env.Tool('generateScript')
            wrappers = env.GenerateWrapperScript(testApps)
            env.Depends(wrappers, testApps)
            env.Alias(pkgname, wrappers)
            env.Alias('test', wrappers)
            env.Alias('all', wrappers)
            env.Clean('test', wrappers)
        if kw.get('pfiles', '') != '':
            pfiles = env.Install(env['PFILESDIR'], kw.get('pfiles'))
            env.AppendUnique(PFILES=pfiles)
            env.Alias(pkgname, pfiles)
            env.Default(pfiles)
            env.Alias('all', pfiles)
        if kw.get('python', '') != '':
            python = env.Install(env['PYTHONDIR'], kw.get('python'))
            env.Alias(pkgname, python)
            env.Default(python)
            env.Alias('all', python)
        if 'wrapper_env' in kw:
            # user has passed in a list of (exename, envdict) tuples
            # to be registered in the construction environment and eventually
            # emitted into the wrapper scripts
            env.Append(WRAPPER_ENV=kw.get('wrapper_env'))

def exists(env):
    return 1;
