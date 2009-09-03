import os, pdb, optparse
import SCons.Action
import SCons.Builder
from SCons.Script import AddOption, GetOption
import SomeUtils

def getTargetPath(prefix, suffix, env):
    return os.path.join(prefix, env.get('RELTARGETDIR', ''), suffix)

def generateWSHScript(scriptFile, env, wrapper):
    scriptFile.write("' Autogenerated by SCons; do not edit!\n")
    scriptFile.write('set shell = CreateObject("WScript.Shell")\n')
    scriptFile.write('set env = shell.Environment("Process")\n')
    if wrapper > 0:
        scriptFile.write('INST_DIR = WScript.ScriptFullName\n')
        scriptFile.write('INST_DIR = Left(INST_DIR,InStrRev(INST_DIR,"\\")-1)\n')
        scriptFile.write('INST_DIR = Left(INST_DIR,InStrRev(INST_DIR,"\\")-1)\n')
        scriptFile.write('INST_DIR = Left(INST_DIR,InStrRev(INST_DIR,"\\")-1)\n')
        scriptFile.write('env("INST_DIR")=INST_DIR\n')
    scriptFile.write('COAST_ROOT = env.item("COAST_ROOT")\n')
    scriptFile.write('If COAST_ROOT = "" Then\n')
    scriptFile.write('  WScript.Echo("What is the location of the External libraries?")\n')
    scriptFile.write('  WScript.Echo("If you set %COAST_ROOT% to this location this script will no longer ask")\n')
    scriptFile.write('  COAST_ROOT = WScript.StdIn.ReadLine()\n')
    scriptFile.write('  env("COAST_ROOT")=COAST_ROOT\n')
    scriptFile.write('End If\n')
    scriptFile.write('env("PATH") = env.Item("PATH") & ";" & INST_DIR & "\\' + str(os.path.join(env['LIBDIR'], env['VARIANTDIR'])) + '"\n')
    scriptFile.write('If COAST_ROOT = "" or INST_DIR = "" Then\n')
    scriptFile.write('  WScript.Echo("COAST_ROOT not set or unable to determine installation directory")\n')
    scriptFile.write('  WScript.Quit(1)\n')
    scriptFile.write('End If\n')
    scriptFile.write('env("PATH") = env.Item("PATH") ')
    scriptFile.write('\n')
    scriptFile.write('set filesystemObject = CreateObject("Scripting.FileSystemObject")\n')
    scriptFile.write('For i=0 to WScript.Arguments.Count-1\n')
    scriptFile.write('  arguments = arguments & WScript.Arguments.Item(i) & " "\n')
    scriptFile.write('Next\n')
    scriptFile.write('env("PYTHONPATH") = INST_DIR & "\\python" & env("PYTHONPATH")\n')
    return

def generateShellScript(scriptFile, env, wrapper):
    scriptText = """#!/bin/sh
################################################################################
# Copyright (c) IFS institute for software at HSR Rapperswil, Switzerland
# Dominik Wild, Marcel Huber
################################################################################
# Autogenerated by SCons; do not edit!

INST_DIR=`dirname $0`
# based on INST_DIR which is the scripts directory = (tests|apps)/<packagename>/scripts/<platform>/<scriptname>
# applications will get placed below targettype 'apps', tests in 'tests'
# <targettype>/<packagename>/...
INST_DIR=`cd $INST_DIR/""" + os.path.relpath(env['BASEOUTDIR'].abspath, os.path.dirname(scriptFile.name)) + """; pwd`

LD_LIBRARY_PATH=$INST_DIR/""" + os.path.join(env['LIBDIR'], env['VARIANTDIR']) + """:$LD_LIBRARY_PATH

export LD_LIBRARY_PATH PATH

# param $1 is the name of the generated file
# param $2 arguments passed to the debugged progam, do not forget to quote them!
# param $3 run executable within script or not, default 1, set to 0 to execute it manually
#
generateGdbCommandFile()
{
    outputfile=${1};
    locsrvopts=${2};
    locRunAsServer=${3:-1};
    # <<-EOF ignore tabs, nice for formatting heredocs
cat > ${outputfile} <<-EOF
    handle SIGSTOP nostop nopass
    handle SIGLWP  nostop pass
    handle SIGTERM nostop pass
#    handle SIGINT  nostop pass
    set environment PATH=${PATH}
#    set environment WD_ROOT=${WD_ROOT}
#    set environment WD_PATH=${WD_PATH}
    set environment LD_LIBRARY_PATH=${LD_LIBRARY_PATH}
#    set environment WD_LIBDIR=${WD_LIBDIR}
#    set environment LOGDIR=${LOGDIR}
#    set environment PID_FILE=${PID_FILE}
    set auto-solib-add 1
    file ${WDS_BIN}
    set args ${locsrvopts}
EOF
    if [ $locRunAsServer -eq 1 ]; then
cat >> ${outputfile} <<-EOF
    run
    where
    continue
    shell rm ${outputfile}
    quit
EOF
    fi;
}

cd """ + getTargetPath('$INST_DIR', '', env) + """

"""
    scriptFile.write(scriptText)

def generatePosixScript(target, source, env):
    for t, s in zip(target, source):
        scriptFile = open(str(t), 'w')
        generateShellScript(scriptFile, env, 1)
        if env["createGDBscript"]:
            scriptFile.write('WDS_BIN=' + os.path.join('$INST_DIR', str(s)) + '\n')
            scriptFile.write("""

cfg_gdbcommands="/tmp/`basename $0`_$$";
generateGdbCommandFile ${cfg_gdbcommands} "$@" 0
echo "Generated gdb command file:"
#cat ${cfg_gdbcommands}

""")
            scriptFile.write('gdb --command ${cfg_gdbcommands}\n')
        else:
            scriptFile.write(os.path.join('$INST_DIR', str(s)) + ' "$@"\n')
        scriptFile.close()
    return 0

def generateWindowsScript(target, source, env):
    for t, s in zip(target, source):
        scriptFile = open(str(t), 'w')
        generateWSHScript(scriptFile, env, 1)
        scriptFile.write('shell.Run "cmd.exe /k """ & INST_DIR & "\\' + str(s) + '"" " & arguments, 1, true')
        scriptFile.close()

def generateScriptEmitter(target, source, env):
    target = []
    gdbsuffix = ('', '_gdb')[env["createGDBscript"] != False]
    for src in source:
        if env['PLATFORM'] != 'win32':
            target.append(env['BASEOUTDIR'].Dir(env['RELTARGETDIR']).Dir(env['SCRIPTDIR']).Dir(env['VARIANTDIR']).File(os.path.basename(src.abspath + gdbsuffix)))
        else:
            target.append(env['BASEOUTDIR'].Dir(env['RELTARGETDIR']).Dir(env['SCRIPTDIR']).Dir(env['VARIANTDIR']).File(os.path.splitext(os.path.basename(src.abspath + gdbsuffix))[0] + ".vbs"))
    return (target, source)

def generateWrapperScript(env, target, gdb=False):
    return env.Depends(env.GenerateScriptBuilder(target, createGDBscript=gdb), SomeUtils.getPyFilename(__file__))

def generate(env):
    try:
        AddOption('--gdb', dest='gdb', action='store_true', default=False, help='Should we run the target within gdb control')
    except optparse.OptionConflictError:
        pass

    if env['PLATFORM'] != 'win32':
        GenerateScriptAction = SCons.Action.Action(generatePosixScript, "Creating wrapper script for '$TARGET'")
        GenerateScriptBuilder = SCons.Builder.Builder(action=[GenerateScriptAction, SCons.Defaults.Chmod('$TARGET', 0755)],
                                                      emitter=generateScriptEmitter,
                                                      single_source=1)
    else:
        GenerateScriptAction = SCons.Action.Action(generateWindowsScript, "Creating wrapper script fpr '$TARGET'")
        GenerateScriptBuilder = SCons.Builder.Builder(action=[GenerateScriptAction], emitter=generateScriptEmitter, single_source=1)

    env.Append(BUILDERS={ 'GenerateScriptBuilder' : GenerateScriptBuilder })
    env.AddMethod(generateWrapperScript, "GenerateWrapperScript")

def exists(env):
    return 1;
