import os, re, subprocess, functools, itertools
import SomeUtils

def uniquelist(iterable):
    """
    Generates an order preserved list with unique items
    """
    return list(unique(iterable))

def unique(iterable):
    """
    Generates an iterator over an order preserved list with unique items 
    """
    seen = set()
    for element in itertools.ifilterfalse(seen.__contains__, iterable):
        seen.add(element)
        yield element

class FinderFactory(object):
    @staticmethod
    def getForPlatform(platform):
        if platform == 'win32':
            return Win32Finder()
        return UnixFinder()

class LibFinder(object):
    def getLibs(self, env, source, libdirs, libnames):
        raise NotImplementedError()

    def getSystemLibDirs(self, env, source):
        raise NotImplementedError()

class UnixFinder(LibFinder):
    def __filterLibs(self, env, filename, libnames):
        basename = os.path.basename(filename)
        libNamesStr = '('+'|'.join(map(re.escape, libnames))+')'
        match = re.match(r'^'+re.escape(env.subst('$SHLIBPREFIX'))+libNamesStr+re.escape(env.subst('$SHLIBSUFFIX')), basename)
        return bool(match)

    def getLibs(self, env, source, libdirs, libnames):
        env['ENV']['LD_LIBRARY_PATH'] = libdirs
        ldd = subprocess.Popen(['ldd', source[0].abspath], stdout=subprocess.PIPE, env=SomeUtils.getFlatENV(env))
        out, err = ldd.communicate()
        return filter(functools.partial(self.__filterLibs, env, libnames=libnames), re.findall('^.*=>\s*([^\s^\(]*)', out, re.MULTILINE))

    def getSystemLibDirs(self, env, source):
        libdirs = []
        linkercmd = env.subst('$LINK', target=source, source=source[0].sources)
        cmdargs = [linkercmd, '-print-search-dirs'] + env.subst('$LINKFLAGS').split(' ')
        linker = subprocess.Popen(cmdargs, stdout=subprocess.PIPE, env=SomeUtils.getFlatENV(env))
        out, err = linker.communicate()
        match = re.search('^libraries.*=(.*)$', out, re.MULTILINE)
        if match:
            libdirs.extend( unique(filter(os.path.exists, map(os.path.abspath, match.group(1).split(os.pathsep)))) )
        return libdirs

class Win32Finder(LibFinder):
    def __filterLibs(self, env, filename, libnames):
        basename = os.path.basename(filename)
        libNamesStr = '('+'|'.join(map(re.escape, libnames))+')'
        match = re.match(r'^('+re.escape(env.subst('$LIBPREFIX'))+')?'+libNamesStr+'.*'+re.escape(env.subst('$SHLIBSUFFIX'))+'$', basename)
        return bool(match)

    def __findFileInPath(self, filename, paths):
        for path in paths:
            if os.path.isfile(os.path.join(path, filename)):
                return os.path.abspath(os.path.join(path, filename))
        return None

    def getLibs(self, env, source, libdirs, libnames):
        ldd = subprocess.Popen(['objdump', '-p', source[0].abspath], stdout=subprocess.PIPE, env=SomeUtils.getFlatENV(env))
        out, err = ldd.communicate()
        deplibs = filter(functools.partial(self.__filterLibs, env, libnames=libnames), re.findall('DLL Name:\s*(\S*)', out, re.MULTILINE))
        return filter(lambda val: bool(val), itertools.imap(functools.partial(self.__findFileInPath, paths=libdirs), deplibs))

    def getSystemLibDirs(self, env, source):
        return os.environ['PATH'].split(os.pathsep)
