import os, pprint, pdb
import SCons.Util
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
        head,tail = os.path.split(splitFile)
        hasPath = False
        while head != '':
            installPath = os.path.normpath(os.path.join(tail, installPath))
            head,tail = os.path.split(head)
            hasPath = True
        if useFirstSegment and hasPath:
            installPath = os.path.join(tail, installPath)
        installPath = os.path.dirname(installPath)
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
        baseoutdir = baseoutdir.Dir(basereldir)

        if kw.get('libraries', [None])[0]:
            libs = kw.get('libraries')
            libraries = env.Install(baseoutdir.Dir(env['LIBDIR']), libs)
            env.Alias(pkgname, libraries)
            env.Default(libraries)
            env.Alias('libraries', libraries)
            env.Alias('all', libraries)

        if kw.get('testApps', '') != '':
            basereldir = 'tests'
        elif kw.get('binaries', '') != '':
            basereldir = 'apps'
        env['TargetType'] = basereldir
        baseoutdir = baseoutdir.Dir(basereldir)

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
            env.Alias(pkgname, wrappers)
            env.Default(wrappers)
            env.Alias('binaries', wrappers)
            env.Alias('all', wrappers)
        if kw.get('testApps', '') != '':
            pkgTarget = kw.get('testApps')
            testApps = env.InstallAs(baseoutdir.Dir(pkgname).Dir(env['TESTDIR']).File(pkgname), pkgTarget)
            env.Tool('generateScript')
            wrappers = env.GenerateWrapperScript(testApps)
            env.Alias(pkgname, wrappers)
            env.Alias('test', wrappers)
            env.Alias('all', wrappers)
            env.Clean('test', wrappers)
        if kw.get('python', '') != '':
            python = env.Install(env['PYTHONDIR'], kw.get('python'))
            env.Alias(pkgname, python)
            env.Default(python)
            env.Alias('all', python)
        if kw.get('requiresLibs', '') != '':
            pkgTarget = env.Alias(pkgname)[0]
            reqdTargets = kw.get('requiresLibs')
            if not SCons.Util.is_List(reqdTargets):
                reqdTargets = [reqdTargets]
            for targ in reqdTargets:
                env.Requires(pkgTarget, env.Alias(targ)[0])
        if 'wrapper_env' in kw:
            # user has passed in a list of (exename, envdict) tuples
            # to be registered in the construction environment and eventually
            # emitted into the wrapper scripts
            env.Append(WRAPPER_ENV=kw.get('wrapper_env'))

def exists(env):
    return 1;
