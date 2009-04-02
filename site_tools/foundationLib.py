import os,platform

def generate(env, **kw):
    if not kw.get('depsOnly', 0):
        env.Tool('addLibrary', library = ['foundation'])
    env.Tool('addLibrary', library = env['lokiLibs'])

def exists(env):
    return true
