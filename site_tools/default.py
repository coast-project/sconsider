import pdb
import SCons.Tool

def generate(env):
    """Postpone adding default tools, see setupBuildTools for implementation"""
    pass
#    for t in SCons.Tool.tool_list(env['PLATFORM'], env):
#        SCons.Tool.Tool(t)(env)

def exists(env):
    return 1
