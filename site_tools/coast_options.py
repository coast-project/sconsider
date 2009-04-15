import os,platform,pdb,traceback
import SCons

def generate(env, **kw):
    env.AppendUnique(CPPDEFINES =['ONLY_STD_IOSTREAM'])
#    env.AppendUnique(CPPDEFINES =['_POSIX_THREADS'])
#    env.AppendUnique(CPPDEFINES =['_POSIX_PTHREAD_SEMANTICS'])
#    env.AppendUnique(CPPDEFINES =['_REENTRANT'])
    env.AppendUnique(CPPDEFINES =['_LARGEFILE64_SOURCE'])
    env.AppendUnique(CPPDEFINES =['WD_OPT'])

def exists(env):
    return true
