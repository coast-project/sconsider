import contextlib, functools, os, pdb
import SCons

class Null(SCons.Util.Null):
    def __getitem__(self, key):
        return self
    def __contains__(self, key):
        return False

def CheckExecutable(context, executable):
    context.Message('Checking for executable {0}... '.format(executable))
    result = context.env.WhereIs(executable)
    context.Result(bool(result))
    return result

def CheckMultipleLibs(context, libraries = None, **kw):
    if not SCons.Util.is_List(libraries):
        libraries = [libraries]
    
    return functools.reduce(lambda x,y: SCons.SConf.CheckLib(context, y, **kw) and x, libraries, True)

def Configure(env, *args, **kw):
    if SCons.Script.GetOption('help'):
        return Null()
    
    kw.setdefault('custom_tests', {})['CheckExecutable'] = CheckExecutable
    kw.setdefault('custom_tests', {})['CheckMultipleLibs'] = CheckMultipleLibs
    env.Append(LINKFLAGS='-Wl,-rpath-link='+os.pathsep.join(map(str, env['LIBPATH'])))
    conf = env.Configure(*args, **kw)
    return conf
    
@contextlib.contextmanager
def ConfigureContext(env, *args, **kw):
    conf = Configure(env, *args, **kw)
    yield conf
    conf.Finish()