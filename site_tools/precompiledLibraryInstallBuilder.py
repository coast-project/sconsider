import os, pdb, re, platform, shutil, stat
import SCons.Action
import SCons.Builder

def findLibraryDirectory(env, basedir, libname):
    variantdir = ''
    # LIBPREFIXES = [ LIBPREFIX, SHLIBPREFIX ]
    # LIBSUFFIXES = [ LIBSUFFIX, SHLIBSUFFIX ]
    libRE = ''
    for pre in env['LIBPREFIXES']:
        if libRE:
            libRE += '|'
        libRE += re.escape(env.subst(pre))
    libRE = '(' + libRE + ')' + libname
    libRE += '[^.]*'
    libSFX = ''
    for suf in env['LIBSUFFIXES']:
        if libSFX:
            libSFX += '|'
        libSFX += re.escape(env.subst(suf))
    libRE += '(' + libSFX + ')(.*)'
    reLibname = re.compile(libRE)
    osStringSep = '[_-]'
    if env['PLATFORM'] == "cygwin":
        variantdir = 'Win_i386'
    elif env['PLATFORM'] == 'sunos':
        osver = tuple([int(x) for x in platform.release().split('.')])
        dirRE = platform.system() + osStringSep + '([0-9](\.[0-9])*)'
        # re for architecture (i686, sparc, amd,...) - bitwidth (32,64)
        dirRE += osStringSep + '?(.*)'
    else:
        osver = tuple([int(x) for x in platform.libc_ver(executable='/lib/libc.so.6')[1].split('.')])
        dirRE = platform.system() + osStringSep + 'glibc' + osStringSep + '([0-9](\.[0-9])*)'
        # re for architecture (i686, sparc, amd,...) - bitwidth (32,64)
        dirRE += osStringSep + '?(.*)'
    reDirname = re.compile(dirRE)
    reBits = re.compile('.*(32|64)')
    files = []
    for dirpath, dirnames, filenames in os.walk(basedir):
        dirnames[:] = [dir for dir in dirnames if not dir in ['build', '.git', '.svn', 'CVS']]
        dirMatch = reDirname.match(os.path.split(dirpath)[1])
        if dirMatch:
            for name in filenames:
                libMatch = reLibname.match(name)
                if libMatch:
                    bits = '32'
                    reM = reBits.match(dirMatch.group(3))
                    if reM:
                        bits = reM.group(1)
                    files.append({'osver':tuple([int(x) for x in dirMatch.group(1).split('.')]),
                                  'bits':bits,
                                  'file':libMatch.group(0),
                                  'path':dirpath,
                                  'linkfile':libMatch.group(0).replace(libMatch.group(3), ''),
                                  'suffix':libMatch.group(2),
                                  'libVersion':libMatch.group(3),
                                  })
    # find best matching library
    # dirmatch: (xxver[1]:'2.9', xxx[2]:'.9', arch-bits[3]:'i686-32')
    # libmatch: ([1]:'lib', sufx[2]:'.so',vers[3]:'.0.9.7')
    bitwidth = env.get('ARCHBITS', '32')
    # filter out wrong bit sizes
    files = [entry for entry in files if entry['bits'] == bitwidth]

    # check for best matching osver entry, downgrade if non exact match
    files.sort(cmp=lambda l, r: cmp(l['osver'], r['osver']), reverse=True)
    osvermatch = None
    for entry in files:
        if entry['osver'] <= osver:
            osvermatch = entry['osver']
            break
    files = [entry for entry in files if entry['osver'] == osvermatch]
    preferStaticLib = env.get('buildSettings', {}).get('preferStaticLib', False)

    staticLibs = [entry for entry in files if entry['suffix'] == env.subst(env['LIBSUFFIX']) ]
    sharedLibs = [entry for entry in files if entry['suffix'] == env.subst(env['SHLIBSUFFIX']) ]

    libVersion = env.get('buildSettings', {}).get('libVersion', '')
    # FIXME: libVersion on win
    if libVersion:
        sharedLibs = [entry for entry in sharedLibs if entry['libVersion'] == libVersion]

    if preferStaticLib:
        allLibs = staticLibs + sharedLibs
    else:
        allLibs = sharedLibs + staticLibs

    if allLibs:
        entry = allLibs[0]
        return (entry['path'], entry['file'], entry['linkfile'], (entry['suffix'] == env.subst(env['LIBSUFFIX'])))

    print 'library [%s] not available for this platform [%s] and bitwidth[%d]' % (libname, env['PLATFORM'], bitwidth)
    return (None, None)

def precompLibNamesEmitter(target, source, env):
    target = []
    newsource = []
    for src in source:
        path, libname = os.path.split(src.srcnode().abspath)
        srcpath, srcfile, linkfile, isStaticLib = findLibraryDirectory(env, path, libname)
        if srcfile:
            if not isStaticLib:
                if srcfile != linkfile:
                    newsource.append(SCons.Script.File(os.path.join(srcpath, srcfile)))
                    target.append(env['BASEOUTDIR'].Dir(env['LIBDIR']).File(linkfile))
                newsource.append(SCons.Script.File(os.path.join(srcpath, srcfile)))
                target.append(env['BASEOUTDIR'].Dir(env['LIBDIR']).File(srcfile))
            else:
                newsource.append(SCons.Script.File(os.path.join(srcpath, srcfile)))
                target.append(SCons.Script.Dir('.').File(srcfile))
    return (target, newsource)

def copyFunc(dest, source, env):
    """Install a source file or directory into a destination by copying,
    (including copying permission/mode bits)."""
    if os.path.isdir(source):
        if os.path.exists(dest):
            if not os.path.isdir(dest):
                raise SCons.Errors.UserError, "cannot overwrite non-directory `%s' with a directory `%s'" % (str(dest), str(source))
        else:
            parent = os.path.split(dest)[0]
            if not os.path.exists(parent):
                os.makedirs(parent)
        shutil.copytree(source, dest)
    else:
        shutil.copy2(source, dest)
        st = os.stat(source)
        os.chmod(dest, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)

    return 0

def installFunc(target, source, env):
    """Install a source file into a target using the function specified
    as the INSTALL construction variable."""
    if len(target) == len(source):
        for t, s in zip(target, source):
            if copyFunc(t.get_path(), s.get_path(), env):
                return 1
    return 0

def generate(env):
    PrecompLibAction = SCons.Action.Action(installFunc, "Installing precompiled library '$SOURCE' as '$TARGET'")
    PrecompLibBuilder = SCons.Builder.Builder(action=[PrecompLibAction],
                                                  emitter=precompLibNamesEmitter,
                                                  single_source=False)

    env.Append(BUILDERS={ 'PrecompiledLibraryInstallBuilder' : PrecompLibBuilder })

def exists(env):
    return 1;
